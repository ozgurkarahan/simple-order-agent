/**
 * Tests for the Settings Page.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SettingsPage from '@/app/settings/page';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

const mockConfig = {
  a2a: { url: 'http://localhost:8000', headers: {}, is_local: true },
  mcp: { name: 'orders', url: 'https://mcp.example.com/', headers: {}, is_active: true },
};

describe('Settings Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  describe('Page Layout', () => {
    it('renders back to chat link', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/back to chat/i)).toBeInTheDocument();
      });
    });

    it('renders Configuration title', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Configuration')).toBeInTheDocument();
      });
    });

    it('renders A2A Agent Connection section', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('A2A Agent Connection')).toBeInTheDocument();
      });
    });

    it('renders MCP Server Configuration section', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('MCP Server Configuration')).toBeInTheDocument();
      });
    });
  });

  describe('Loading Configuration', () => {
    it('fetches and displays current config on load', async () => {
      const customConfig = {
        a2a: { url: 'https://custom-agent.example.com', headers: {}, is_local: false },
        mcp: { name: 'custom-mcp', url: 'https://custom-mcp.example.com/', headers: {}, is_active: true },
      };
      
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => customConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByDisplayValue('https://custom-agent.example.com')).toBeInTheDocument();
      });
    });

    it('shows loading state while fetching config', () => {
      (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));

      render(<SettingsPage />, { wrapper: createWrapper() });

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('shows error message if config fetch fails', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });
  });

  describe('A2A Configuration', () => {
    it('allows updating A2A URL', async () => {
      const user = userEvent.setup();
      
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByDisplayValue('http://localhost:8000')).toBeInTheDocument();
      });

      const urlInput = screen.getByLabelText(/agent url/i);
      await user.clear(urlInput);
      await user.type(urlInput, 'https://new-agent.example.com');

      expect(screen.getByDisplayValue('https://new-agent.example.com')).toBeInTheDocument();
    });

    it('has Test Connection button for A2A', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        const testButtons = screen.getAllByRole('button', { name: /test connection/i });
        expect(testButtons.length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  describe('MCP Configuration', () => {
    it('allows updating MCP server name', async () => {
      const user = userEvent.setup();
      
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByDisplayValue('orders')).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/server name/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'custom-server');

      expect(screen.getByDisplayValue('custom-server')).toBeInTheDocument();
    });

    it('allows updating MCP URL', async () => {
      const user = userEvent.setup();
      
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByDisplayValue('https://mcp.example.com/')).toBeInTheDocument();
      });

      const urlInput = screen.getByLabelText(/server url/i);
      await user.clear(urlInput);
      await user.type(urlInput, 'https://new-mcp.example.com/');

      expect(screen.getByDisplayValue('https://new-mcp.example.com/')).toBeInTheDocument();
    });
  });

  describe('Headers Editor', () => {
    it('has Add Header buttons', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByDisplayValue('http://localhost:8000')).toBeInTheDocument();
      });

      // Should have Add Header buttons for both A2A and MCP sections
      const addHeaderButtons = screen.getAllByRole('button', { name: /add header/i });
      expect(addHeaderButtons.length).toBe(2);
    });
  });

  describe('Save Configuration', () => {
    it('has Save Configuration button', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /save configuration/i })).toBeInTheDocument();
      });
    });

    it('calls API to save config on Save button click', async () => {
      const user = userEvent.setup();
      
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, json: async () => mockConfig })
        .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'saved' }) })
        .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'saved' }) });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByDisplayValue('http://localhost:8000')).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /save configuration/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/config/a2a',
          expect.objectContaining({ method: 'PUT' })
        );
      });
    });
  });

  describe('Reset Configuration', () => {
    it('has Reset to Defaults button', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      render(<SettingsPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /reset to defaults/i })).toBeInTheDocument();
      });
    });
  });
});
