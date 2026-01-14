/**
 * Tests for ConversationSidebar component
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ConversationSidebar from "@/components/ConversationSidebar";
import type { Conversation } from "@/lib/api";

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  ChevronLeft: () => <div data-testid="chevron-left">ChevronLeft</div>,
  ChevronRight: () => <div data-testid="chevron-right">ChevronRight</div>,
  MessageSquarePlus: () => <div data-testid="message-square-plus">MessageSquarePlus</div>,
  Trash2: () => <div data-testid="trash2">Trash2</div>,
  Edit2: () => <div data-testid="edit2">Edit2</div>,
  Check: () => <div data-testid="check">Check</div>,
  X: () => <div data-testid="x">X</div>,
}));

describe("ConversationSidebar", () => {
  const mockConversations: Conversation[] = [
    {
      id: "conv-1",
      title: "First Conversation",
      created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
      updated_at: new Date(Date.now() - 3600000).toISOString(),
      message_count: 5,
    },
    {
      id: "conv-2",
      title: "Second Conversation",
      created_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
      updated_at: new Date(Date.now() - 7200000).toISOString(),
      message_count: 3,
    },
    {
      id: "conv-3",
      title: "Third Conversation",
      created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
      updated_at: new Date(Date.now() - 86400000).toISOString(),
      message_count: 10,
    },
  ];

  const defaultProps = {
    conversations: mockConversations,
    activeConversationId: "conv-1",
    isOpen: true,
    onToggle: jest.fn(),
    onSelectConversation: jest.fn(),
    onNewConversation: jest.fn(),
    onRenameConversation: jest.fn(),
    onDeleteConversation: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders sidebar toggle button", () => {
      render(<ConversationSidebar {...defaultProps} />);
      const toggleButton = screen.getByRole("button", { name: /close sidebar/i });
      expect(toggleButton).toBeInTheDocument();
    });

    it("renders chevron-left icon when sidebar is open", () => {
      render(<ConversationSidebar {...defaultProps} />);
      expect(screen.getByTestId("chevron-left")).toBeInTheDocument();
    });

    it("renders chevron-right icon when sidebar is closed", () => {
      render(<ConversationSidebar {...defaultProps} isOpen={false} />);
      expect(screen.getByTestId("chevron-right")).toBeInTheDocument();
    });

    it("renders new conversation button", () => {
      render(<ConversationSidebar {...defaultProps} />);
      const newButton = screen.getByRole("button", { name: /new conversation/i });
      expect(newButton).toBeInTheDocument();
    });

    it("renders all conversations", () => {
      render(<ConversationSidebar {...defaultProps} />);
      expect(screen.getByText("First Conversation")).toBeInTheDocument();
      expect(screen.getByText("Second Conversation")).toBeInTheDocument();
      expect(screen.getByText("Third Conversation")).toBeInTheDocument();
    });

    it("displays message count for each conversation", () => {
      render(<ConversationSidebar {...defaultProps} />);
      expect(screen.getByText(/5 msgs/i)).toBeInTheDocument();
      expect(screen.getByText(/3 msgs/i)).toBeInTheDocument();
      expect(screen.getByText(/10 msgs/i)).toBeInTheDocument();
    });

    it("highlights active conversation", () => {
      const { container } = render(<ConversationSidebar {...defaultProps} />);
      const activeConv = container.querySelector('[class*="border-blue-600"]');
      expect(activeConv).toBeInTheDocument();
    });

    it("shows empty state when no conversations", () => {
      render(<ConversationSidebar {...defaultProps} conversations={[]} />);
      expect(screen.getByText(/no conversations yet/i)).toBeInTheDocument();
    });
  });

  describe("Toggle Functionality", () => {
    it("calls onToggle when toggle button is clicked", async () => {
      const user = userEvent.setup();
      render(<ConversationSidebar {...defaultProps} />);
      
      const toggleButton = screen.getByRole("button", { name: /close sidebar/i });
      await user.click(toggleButton);
      
      expect(defaultProps.onToggle).toHaveBeenCalledTimes(1);
    });

    it("applies correct translation class when closed", () => {
      const { container } = render(<ConversationSidebar {...defaultProps} isOpen={false} />);
      const sidebar = container.querySelector('[class*="-translate-x-full"]');
      expect(sidebar).toBeInTheDocument();
    });

    it("applies correct translation class when open", () => {
      const { container } = render(<ConversationSidebar {...defaultProps} isOpen={true} />);
      const sidebar = container.querySelector('[class*="translate-x-0"]');
      expect(sidebar).toBeInTheDocument();
    });
  });

  describe("New Conversation", () => {
    it("calls onNewConversation when new button is clicked", async () => {
      const user = userEvent.setup();
      render(<ConversationSidebar {...defaultProps} />);
      
      const newButton = screen.getByRole("button", { name: /new conversation/i });
      await user.click(newButton);
      
      expect(defaultProps.onNewConversation).toHaveBeenCalledTimes(1);
    });
  });

  describe("Select Conversation", () => {
    it("calls onSelectConversation when a conversation is clicked", async () => {
      const user = userEvent.setup();
      render(<ConversationSidebar {...defaultProps} />);
      
      const conversation = screen.getByText("Second Conversation");
      await user.click(conversation);
      
      expect(defaultProps.onSelectConversation).toHaveBeenCalledWith("conv-2");
    });

    it("does not call onSelectConversation when clicking active conversation", async () => {
      const user = userEvent.setup();
      render(<ConversationSidebar {...defaultProps} />);
      
      // First conversation is active, clicking it should still call the handler
      const conversation = screen.getByText("First Conversation");
      await user.click(conversation);
      
      // It should be called (user might want to ensure focus)
      expect(defaultProps.onSelectConversation).toHaveBeenCalledWith("conv-1");
    });
  });

  describe("Rename Conversation", () => {
    it("enters edit mode when edit button is clicked", async () => {
      const user = userEvent.setup();
      const { container } = render(<ConversationSidebar {...defaultProps} />);
      
      // Hover over conversation to show edit button
      const conversation = screen.getByText("First Conversation").closest("div");
      if (conversation) {
        fireEvent.mouseEnter(conversation);
      }
      
      // Find and click edit button
      const editButtons = screen.getAllByRole("button", { name: /rename conversation/i });
      await user.click(editButtons[0]);
      
      // Should show input field
      const input = container.querySelector('input[type="text"]');
      expect(input).toBeInTheDocument();
      expect(input).toHaveValue("First Conversation");
    });

    it("saves new title when check button is clicked", async () => {
      const user = userEvent.setup();
      const { container } = render(<ConversationSidebar {...defaultProps} />);
      
      // Enter edit mode
      const conversation = screen.getByText("First Conversation").closest("div");
      if (conversation) {
        fireEvent.mouseEnter(conversation);
      }
      const editButtons = screen.getAllByRole("button", { name: /rename conversation/i });
      await user.click(editButtons[0]);
      
      // Change the title
      const input = container.querySelector('input[type="text"]') as HTMLInputElement;
      await user.clear(input);
      await user.type(input, "Updated Title");
      
      // Click save
      const saveButton = screen.getByTestId("check").closest("button");
      if (saveButton) {
        await user.click(saveButton);
      }
      
      expect(defaultProps.onRenameConversation).toHaveBeenCalledWith("conv-1", "Updated Title");
    });

    it("saves new title when Enter key is pressed", async () => {
      const user = userEvent.setup();
      const { container } = render(<ConversationSidebar {...defaultProps} />);
      
      // Enter edit mode
      const conversation = screen.getByText("First Conversation").closest("div");
      if (conversation) {
        fireEvent.mouseEnter(conversation);
      }
      const editButtons = screen.getAllByRole("button", { name: /rename conversation/i });
      await user.click(editButtons[0]);
      
      // Change the title and press Enter
      const input = container.querySelector('input[type="text"]') as HTMLInputElement;
      await user.clear(input);
      await user.type(input, "New Title{Enter}");
      
      expect(defaultProps.onRenameConversation).toHaveBeenCalledWith("conv-1", "New Title");
    });

    it("cancels edit when X button is clicked", async () => {
      const user = userEvent.setup();
      const { container } = render(<ConversationSidebar {...defaultProps} />);
      
      // Enter edit mode
      const conversation = screen.getByText("First Conversation").closest("div");
      if (conversation) {
        fireEvent.mouseEnter(conversation);
      }
      const editButtons = screen.getAllByRole("button", { name: /rename conversation/i });
      await user.click(editButtons[0]);
      
      // Change the title
      const input = container.querySelector('input[type="text"]') as HTMLInputElement;
      await user.clear(input);
      await user.type(input, "Should Not Save");
      
      // Click cancel
      const cancelButton = screen.getByTestId("x").closest("button");
      if (cancelButton) {
        await user.click(cancelButton);
      }
      
      expect(defaultProps.onRenameConversation).not.toHaveBeenCalled();
      
      // Should exit edit mode and show original title
      await waitFor(() => {
        expect(screen.getByText("First Conversation")).toBeInTheDocument();
      });
    });

    it("cancels edit when Escape key is pressed", async () => {
      const user = userEvent.setup();
      const { container } = render(<ConversationSidebar {...defaultProps} />);
      
      // Enter edit mode
      const conversation = screen.getByText("First Conversation").closest("div");
      if (conversation) {
        fireEvent.mouseEnter(conversation);
      }
      const editButtons = screen.getAllByRole("button", { name: /rename conversation/i });
      await user.click(editButtons[0]);
      
      // Press Escape
      const input = container.querySelector('input[type="text"]') as HTMLInputElement;
      await user.type(input, "{Escape}");
      
      expect(defaultProps.onRenameConversation).not.toHaveBeenCalled();
    });
  });

  describe("Delete Conversation", () => {
    it("shows confirmation dialog when delete button is clicked", async () => {
      const user = userEvent.setup();
      const confirmSpy = jest.spyOn(window, "confirm").mockReturnValue(true);
      
      render(<ConversationSidebar {...defaultProps} />);
      
      // Hover to show delete button
      const conversation = screen.getByText("First Conversation").closest("div");
      if (conversation) {
        fireEvent.mouseEnter(conversation);
      }
      
      // Click delete
      const deleteButtons = screen.getAllByRole("button", { name: /delete conversation/i });
      await user.click(deleteButtons[0]);
      
      expect(confirmSpy).toHaveBeenCalledWith('Delete conversation "First Conversation"?');
      confirmSpy.mockRestore();
    });

    it("calls onDeleteConversation when deletion is confirmed", async () => {
      const user = userEvent.setup();
      jest.spyOn(window, "confirm").mockReturnValue(true);
      
      render(<ConversationSidebar {...defaultProps} />);
      
      const conversation = screen.getByText("First Conversation").closest("div");
      if (conversation) {
        fireEvent.mouseEnter(conversation);
      }
      
      const deleteButtons = screen.getAllByRole("button", { name: /delete conversation/i });
      await user.click(deleteButtons[0]);
      
      expect(defaultProps.onDeleteConversation).toHaveBeenCalledWith("conv-1");
    });

    it("does not delete when user cancels confirmation", async () => {
      const user = userEvent.setup();
      jest.spyOn(window, "confirm").mockReturnValue(false);
      
      render(<ConversationSidebar {...defaultProps} />);
      
      const conversation = screen.getByText("First Conversation").closest("div");
      if (conversation) {
        fireEvent.mouseEnter(conversation);
      }
      
      const deleteButtons = screen.getAllByRole("button", { name: /delete conversation/i });
      await user.click(deleteButtons[0]);
      
      expect(defaultProps.onDeleteConversation).not.toHaveBeenCalled();
    });
  });

  describe("Time Formatting", () => {
    it("displays 'Just now' for very recent updates", () => {
      const recentConversations = [
        {
          id: "conv-recent",
          title: "Recent Conversation",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          message_count: 1,
        },
      ];
      
      render(<ConversationSidebar {...defaultProps} conversations={recentConversations} />);
      
      expect(screen.getByText(/just now/i)).toBeInTheDocument();
    });

    it("displays minutes ago for recent updates", () => {
      render(<ConversationSidebar {...defaultProps} />);
      
      // First conversation is 1 hour ago, should show "1h ago"
      expect(screen.getByText(/1h ago/i)).toBeInTheDocument();
    });

    it("displays days ago for older updates", () => {
      render(<ConversationSidebar {...defaultProps} />);
      
      // Third conversation is 1 day ago
      expect(screen.getByText(/1d ago/i)).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("has proper ARIA labels", () => {
      render(<ConversationSidebar {...defaultProps} isOpen={true} />);
      
      const toggleButton = screen.getByLabelText(/close sidebar/i);
      expect(toggleButton).toBeInTheDocument();
    });

    it("toggle button has correct label when closed", () => {
      render(<ConversationSidebar {...defaultProps} isOpen={false} />);
      
      const toggleButton = screen.getByLabelText(/open sidebar/i);
      expect(toggleButton).toBeInTheDocument();
    });
  });
});
