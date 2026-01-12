"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";
import {
  TrendingUp,
  Package,
  DollarSign,
  ShoppingCart,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";

// Sample data - in real app, this would come from the agent/API
const revenueData = [
  { name: "Mon", value: 4000 },
  { name: "Tue", value: 3000 },
  { name: "Wed", value: 5000 },
  { name: "Thu", value: 2780 },
  { name: "Fri", value: 6890 },
  { name: "Sat", value: 4390 },
  { name: "Sun", value: 3490 },
];

const ordersByStatus = [
  { name: "Pending", value: 15, color: "#f59e0b" },
  { name: "Processing", value: 25, color: "#3b82f6" },
  { name: "Shipped", value: 35, color: "#8b5cf6" },
  { name: "Delivered", value: 45, color: "#22c55e" },
];

const trendData = [
  { name: "Week 1", orders: 120, revenue: 15000 },
  { name: "Week 2", orders: 150, revenue: 18500 },
  { name: "Week 3", orders: 180, revenue: 22000 },
  { name: "Week 4", orders: 220, revenue: 28000 },
];

interface StatCardProps {
  title: string;
  value: string;
  change: number;
  icon: React.ElementType;
  trend: "up" | "down";
}

function StatCard({ title, value, change, icon: Icon, trend }: StatCardProps) {
  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        <div
          className={cn(
            "flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full",
            trend === "up"
              ? "bg-green-500/10 text-green-500"
              : "bg-red-500/10 text-red-500"
          )}
        >
          {trend === "up" ? (
            <ArrowUpRight className="w-3 h-3" />
          ) : (
            <ArrowDownRight className="w-3 h-3" />
          )}
          {Math.abs(change)}%
        </div>
      </div>
      <h3 className="text-2xl font-bold">{value}</h3>
      <p className="text-sm text-muted-foreground">{title}</p>
    </div>
  );
}

export function Analytics() {
  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Analytics Dashboard</h2>
        <p className="text-muted-foreground">
          Overview of your order analytics and trends
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Revenue"
          value={formatCurrency(83550)}
          change={12.5}
          icon={DollarSign}
          trend="up"
        />
        <StatCard
          title="Total Orders"
          value="670"
          change={8.2}
          icon={ShoppingCart}
          trend="up"
        />
        <StatCard
          title="Avg. Order Value"
          value={formatCurrency(124.70)}
          change={-2.4}
          icon={TrendingUp}
          trend="down"
        />
        <StatCard
          title="Products Sold"
          value="1,847"
          change={15.3}
          icon={Package}
          trend="up"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <div className="bg-card border border-border rounded-xl p-4">
          <h3 className="font-semibold mb-4">Weekly Revenue</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="name"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                />
                <YAxis
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickFormatter={(value) => `$${value}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                  formatter={(value: number) => [formatCurrency(value), "Revenue"]}
                />
                <Bar
                  dataKey="value"
                  fill="hsl(var(--primary))"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Orders by Status */}
        <div className="bg-card border border-border rounded-xl p-4">
          <h3 className="font-semibold mb-4">Orders by Status</h3>
          <div className="h-64 flex items-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={ordersByStatus}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {ordersByStatus.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2">
              {ordersByStatus.map((status) => (
                <div key={status.name} className="flex items-center gap-2 text-sm">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: status.color }}
                  />
                  <span className="text-muted-foreground">{status.name}</span>
                  <span className="font-medium ml-auto">{status.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="bg-card border border-border rounded-xl p-4">
        <h3 className="font-semibold mb-4">Monthly Trend</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="name"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
              />
              <YAxis
                yAxisId="left"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickFormatter={(value) => `$${value / 1000}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="orders"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: "#3b82f6" }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="revenue"
                stroke="#22c55e"
                strokeWidth={2}
                dot={{ fill: "#22c55e" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="flex justify-center gap-6 mt-4">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-muted-foreground">Orders</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-muted-foreground">Revenue</span>
          </div>
        </div>
      </div>
    </div>
  );
}
