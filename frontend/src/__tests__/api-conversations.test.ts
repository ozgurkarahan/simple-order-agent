/**
 * Tests for conversation API functions
 */

import {
  listConversations,
  createConversation,
  getConversation,
  updateConversation,
  deleteConversation,
} from "@/lib/api";

// Mock fetch globally
global.fetch = jest.fn();

describe("Conversation API Functions", () => {
  const mockConversation = {
    id: "conv-123",
    title: "Test Conversation",
    created_at: "2026-01-14T12:00:00Z",
    updated_at: "2026-01-14T12:00:00Z",
    message_count: 5,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  describe("listConversations", () => {
    it("fetches all conversations successfully", async () => {
      const mockConversations = [mockConversation];
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConversations,
      });

      const result = await listConversations();

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/conversations"
      );
      expect(result).toEqual(mockConversations);
    });

    it("throws error when request fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await expect(listConversations()).rejects.toThrow(
        "Failed to list conversations: 500"
      );
    });
  });

  describe("createConversation", () => {
    it("creates conversation without title", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConversation,
      });

      const result = await createConversation();

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/conversations",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        })
      );
      expect(result).toEqual(mockConversation);
    });

    it("creates conversation with custom title", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockConversation, title: "Custom Title" }),
      });

      const result = await createConversation({ title: "Custom Title" });

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/conversations",
        expect.objectContaining({
          body: JSON.stringify({ title: "Custom Title" }),
        })
      );
      expect(result.title).toBe("Custom Title");
    });

    it("throws error when creation fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
      });

      await expect(createConversation()).rejects.toThrow(
        "Failed to create conversation: 400"
      );
    });
  });

  describe("getConversation", () => {
    it("fetches specific conversation successfully", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockConversation,
      });

      const result = await getConversation("conv-123");

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/conversations/conv-123"
      );
      expect(result).toEqual(mockConversation);
    });

    it("throws error when conversation not found", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await expect(getConversation("nonexistent")).rejects.toThrow(
        "Failed to get conversation: 404"
      );
    });
  });

  describe("updateConversation", () => {
    it("updates conversation title successfully", async () => {
      const updatedConversation = {
        ...mockConversation,
        title: "Updated Title",
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => updatedConversation,
      });

      const result = await updateConversation("conv-123", {
        title: "Updated Title",
      });

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/conversations/conv-123",
        expect.objectContaining({
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: "Updated Title" }),
        })
      );
      expect(result.title).toBe("Updated Title");
    });

    it("throws error when update fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await expect(
        updateConversation("nonexistent", { title: "New Title" })
      ).rejects.toThrow("Failed to update conversation: 404");
    });
  });

  describe("deleteConversation", () => {
    it("deletes conversation successfully", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
      });

      await deleteConversation("conv-123");

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/conversations/conv-123",
        expect.objectContaining({
          method: "DELETE",
        })
      );
    });

    it("throws error when deletion fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await expect(deleteConversation("nonexistent")).rejects.toThrow(
        "Failed to delete conversation: 404"
      );
    });

    it("returns void on successful deletion", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
      });

      const result = await deleteConversation("conv-123");

      expect(result).toBeUndefined();
    });
  });

  describe("API Error Handling", () => {
    it("handles network errors", async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error("Network error")
      );

      await expect(listConversations()).rejects.toThrow("Network error");
    });

    it("handles malformed JSON responses", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error("Invalid JSON");
        },
      });

      await expect(listConversations()).rejects.toThrow("Invalid JSON");
    });
  });

  describe("API Base URL", () => {
    it("uses correct base URL for all endpoints", async () => {
      const baseUrl = "http://localhost:8000";

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => [],
      });

      await listConversations();
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining(baseUrl)
      );

      await createConversation();
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining(baseUrl),
        expect.any(Object)
      );

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockConversation,
      });

      await getConversation("conv-123");
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining(baseUrl)
      );
    });
  });
});
