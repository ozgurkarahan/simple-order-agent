"use client";

import { useState } from "react";
import {
  Search,
  Filter,
  ChevronDown,
  Eye,
  MoreHorizontal,
  Package,
  Truck,
  CheckCircle,
  Clock,
  XCircle,
} from "lucide-react";
import { cn, formatCurrency, formatDate } from "@/lib/utils";

// Sample data - in real app, this would come from the agent/API
const sampleOrders = [
  {
    id: "ORD-001",
    customer: "John Doe",
    email: "john@example.com",
    status: "delivered",
    total: 150.0,
    items: 3,
    createdAt: "2024-01-15T10:00:00Z",
  },
  {
    id: "ORD-002",
    customer: "Jane Smith",
    email: "jane@example.com",
    status: "shipped",
    total: 275.5,
    items: 2,
    createdAt: "2024-01-14T15:30:00Z",
  },
  {
    id: "ORD-003",
    customer: "Bob Johnson",
    email: "bob@example.com",
    status: "processing",
    total: 89.99,
    items: 1,
    createdAt: "2024-01-16T09:15:00Z",
  },
  {
    id: "ORD-004",
    customer: "Alice Brown",
    email: "alice@example.com",
    status: "pending",
    total: 324.0,
    items: 5,
    createdAt: "2024-01-16T11:45:00Z",
  },
  {
    id: "ORD-005",
    customer: "Charlie Wilson",
    email: "charlie@example.com",
    status: "cancelled",
    total: 67.5,
    items: 2,
    createdAt: "2024-01-13T14:20:00Z",
  },
  {
    id: "ORD-006",
    customer: "Diana Lee",
    email: "diana@example.com",
    status: "delivered",
    total: 199.99,
    items: 4,
    createdAt: "2024-01-12T16:30:00Z",
  },
  {
    id: "ORD-007",
    customer: "Edward Chen",
    email: "edward@example.com",
    status: "shipped",
    total: 445.0,
    items: 6,
    createdAt: "2024-01-15T08:00:00Z",
  },
  {
    id: "ORD-008",
    customer: "Fiona Garcia",
    email: "fiona@example.com",
    status: "processing",
    total: 120.0,
    items: 2,
    createdAt: "2024-01-16T13:10:00Z",
  },
];

type OrderStatus = "pending" | "processing" | "shipped" | "delivered" | "cancelled";

const statusConfig: Record<
  OrderStatus,
  { label: string; color: string; icon: React.ElementType }
> = {
  pending: { label: "Pending", color: "text-yellow-500 bg-yellow-500/10", icon: Clock },
  processing: { label: "Processing", color: "text-blue-500 bg-blue-500/10", icon: Package },
  shipped: { label: "Shipped", color: "text-purple-500 bg-purple-500/10", icon: Truck },
  delivered: { label: "Delivered", color: "text-green-500 bg-green-500/10", icon: CheckCircle },
  cancelled: { label: "Cancelled", color: "text-red-500 bg-red-500/10", icon: XCircle },
};

interface OrderDetailsModalProps {
  order: (typeof sampleOrders)[0];
  onClose: () => void;
}

function OrderDetailsModal({ order, onClose }: OrderDetailsModalProps) {
  const status = statusConfig[order.status as OrderStatus];
  const StatusIcon = status.icon;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card border border-border rounded-xl w-full max-w-md p-6 m-4 animate-slide-up">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Order Details</h3>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            ×
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Order ID</span>
            <span className="font-mono font-medium">{order.id}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Status</span>
            <span
              className={cn(
                "flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium",
                status.color
              )}
            >
              <StatusIcon className="w-3 h-3" />
              {status.label}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Customer</span>
            <span className="font-medium">{order.customer}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Email</span>
            <span className="text-sm">{order.email}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Items</span>
            <span className="font-medium">{order.items}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Total</span>
            <span className="font-bold text-lg">{formatCurrency(order.total)}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Date</span>
            <span className="text-sm">{formatDate(order.createdAt)}</span>
          </div>
        </div>

        <div className="flex gap-2 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors"
          >
            Close
          </button>
          <button className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
            Edit Order
          </button>
        </div>
      </div>
    </div>
  );
}

export function OrdersTable() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedOrder, setSelectedOrder] = useState<(typeof sampleOrders)[0] | null>(
    null
  );

  const filteredOrders = sampleOrders.filter((order) => {
    const matchesSearch =
      order.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.customer.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || order.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-6 space-y-6 h-full overflow-hidden flex flex-col">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Orders</h2>
        <p className="text-muted-foreground">
          View and manage all orders in the system
        </p>
      </div>

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search orders..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="pl-9 pr-8 py-2 rounded-lg border border-input bg-background text-sm appearance-none focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="shipped">Shipped</option>
            <option value="delivered">Delivered</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto border border-border rounded-xl">
        <table className="w-full">
          <thead className="bg-muted/50 sticky top-0">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground">
                Order ID
              </th>
              <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground">
                Customer
              </th>
              <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground">
                Status
              </th>
              <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground">
                Items
              </th>
              <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground">
                Total
              </th>
              <th className="text-left px-4 py-3 text-sm font-medium text-muted-foreground">
                Date
              </th>
              <th className="text-right px-4 py-3 text-sm font-medium text-muted-foreground">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredOrders.map((order) => {
              const status = statusConfig[order.status as OrderStatus];
              const StatusIcon = status.icon;

              return (
                <tr
                  key={order.id}
                  className="border-t border-border hover:bg-muted/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="font-mono text-sm font-medium">{order.id}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium text-sm">{order.customer}</p>
                      <p className="text-xs text-muted-foreground">{order.email}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium",
                        status.color
                      )}
                    >
                      <StatusIcon className="w-3 h-3" />
                      {status.label}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">{order.items}</td>
                  <td className="px-4 py-3">
                    <span className="font-medium">{formatCurrency(order.total)}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {formatDate(order.createdAt)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setSelectedOrder(order)}
                        className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                        title="View details"
                      >
                        <Eye className="w-4 h-4 text-muted-foreground" />
                      </button>
                      <button
                        className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                        title="More options"
                      >
                        <MoreHorizontal className="w-4 h-4 text-muted-foreground" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filteredOrders.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            No orders found matching your criteria.
          </div>
        )}
      </div>

      {/* Order Details Modal */}
      {selectedOrder && (
        <OrderDetailsModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
        />
      )}
    </div>
  );
}
