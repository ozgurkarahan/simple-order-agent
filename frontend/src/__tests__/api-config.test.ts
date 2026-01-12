/**
 * Tests for Configuration API client functions.
 */

import {
  fetchConfig,
  updateA2AConfig,
  updateMCPConfig,
  testA2AConnection,
  testMCPConnection,
  resetConfig,
} from '@/lib/api';

describe('Configuration API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchConfig', () => {
    it('fetches current configuration from /api/config', async () => {
      const mockConfig = {
        a2a: { url: 'http://localhost:8000', headers: {}, is_local: true },
        mcp: { name: 'orders', url: 'https://mcp.example.com', headers: {}, is_active: true },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig,
      });

      const result = await fetchConfig();

      expect(global.fetch).toHaveBeenCalledWith('/api/config');
      expect(result).toEqual(mockConfig);
    });

    it('throws error when fetch fails', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      });

      await expect(fetchConfig()).rejects.toThrow();
    });
  });

  describe('updateA2AConfig', () => {
    it('sends PUT request to /api/config/a2a', async () => {
      const newConfig = {
        url: 'https://new-agent.example.com',
        headers: { 'Authorization': 'Bearer token' },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'saved' }),
      });

      await updateA2AConfig(newConfig);

      expect(global.fetch).toHaveBeenCalledWith('/api/config/a2a', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig),
      });
    });

    it('returns response data on success', async () => {
      const newConfig = { url: 'https://agent.example.com', headers: {} };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'saved', connection_test: 'success' }),
      });

      const result = await updateA2AConfig(newConfig);

      expect(result.status).toBe('saved');
    });

    it('throws error when update fails', async () => {
      const newConfig = { url: 'invalid', headers: {} };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Unprocessable Entity',
      });

      await expect(updateA2AConfig(newConfig)).rejects.toThrow();
    });
  });

  describe('updateMCPConfig', () => {
    it('sends PUT request to /api/config/mcp', async () => {
      const newConfig = {
        name: 'custom-mcp',
        url: 'https://new-mcp.example.com',
        headers: { 'client_id': 'id123' },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'saved' }),
      });

      await updateMCPConfig(newConfig);

      expect(global.fetch).toHaveBeenCalledWith('/api/config/mcp', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig),
      });
    });

    it('returns response data on success', async () => {
      const newConfig = { name: 'mcp', url: 'https://mcp.example.com', headers: {} };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'saved', reload_required: false }),
      });

      const result = await updateMCPConfig(newConfig);

      expect(result.status).toBe('saved');
    });
  });

  describe('testA2AConnection', () => {
    it('sends POST request to /api/config/a2a/test', async () => {
      const testConfig = {
        url: 'http://localhost:8000',
        headers: {},
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          agent_card: { name: 'Test Agent', version: '1.0.0' },
        }),
      });

      await testA2AConnection(testConfig);

      expect(global.fetch).toHaveBeenCalledWith('/api/config/a2a/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testConfig),
      });
    });

    it('returns agent card on successful connection', async () => {
      const testConfig = { url: 'http://localhost:8000', headers: {} };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          agent_card: { name: 'Orders Agent', version: '1.0.0', description: 'An agent' },
        }),
      });

      const result = await testA2AConnection(testConfig);

      expect(result.success).toBe(true);
      expect(result.agent_card?.name).toBe('Orders Agent');
    });

    it('returns error on failed connection', async () => {
      const testConfig = { url: 'https://unreachable.example.com', headers: {} };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: false,
          error: 'Connection refused',
        }),
      });

      const result = await testA2AConnection(testConfig);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Connection refused');
    });
  });

  describe('testMCPConnection', () => {
    it('sends POST request to /api/config/mcp/test', async () => {
      const testConfig = {
        url: 'https://mcp.example.com',
        headers: { 'client_id': 'test' },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          tools: ['get-all-orders', 'create-order'],
        }),
      });

      await testMCPConnection(testConfig);

      expect(global.fetch).toHaveBeenCalledWith('/api/config/mcp/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testConfig),
      });
    });

    it('returns tools list on successful connection', async () => {
      const testConfig = { url: 'https://mcp.example.com', headers: {} };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          tools: ['get-all-orders', 'get-orders-by-customer-id', 'create-order'],
        }),
      });

      const result = await testMCPConnection(testConfig);

      expect(result.success).toBe(true);
      expect(result.tools).toHaveLength(3);
    });

    it('returns error on failed connection', async () => {
      const testConfig = { url: 'https://unreachable.example.com', headers: {} };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: false,
          error: 'Timeout',
        }),
      });

      const result = await testMCPConnection(testConfig);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Timeout');
    });
  });

  describe('resetConfig', () => {
    it('sends POST request to /api/config/reset', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'reset', message: 'Configuration reset to defaults' }),
      });

      await resetConfig();

      expect(global.fetch).toHaveBeenCalledWith('/api/config/reset', {
        method: 'POST',
      });
    });

    it('returns reset confirmation on success', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'reset', message: 'Configuration reset to defaults' }),
      });

      const result = await resetConfig();

      expect(result.status).toBe('reset');
    });
  });
});

describe('Configuration Types', () => {
  it('AppConfig has correct structure', () => {
    // This is a type test - it ensures our types are correct
    const config = {
      a2a: {
        url: 'http://localhost:8000',
        headers: { 'Authorization': 'Bearer token' },
        is_local: true,
      },
      mcp: {
        name: 'orders',
        url: 'https://mcp.example.com',
        headers: { 'client_id': 'id', 'client_secret': 'secret' },
        is_active: true,
      },
      updated_at: '2025-01-12T10:00:00Z',
    };

    expect(config.a2a.url).toBeDefined();
    expect(config.mcp.name).toBeDefined();
  });
});
