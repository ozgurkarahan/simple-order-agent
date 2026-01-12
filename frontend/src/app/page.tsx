"use client";

import { useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Chat } from "@/components/Chat";
import { Analytics } from "@/components/Analytics";
import { OrdersTable } from "@/components/OrdersTable";

export default function Home() {
  const [activeView, setActiveView] = useState<"chat" | "dashboard" | "orders">("chat");

  return (
    <div className="flex h-screen bg-background">
      <Sidebar activeView={activeView} onViewChange={setActiveView} />

      <main className="flex-1 overflow-hidden">
        {activeView === "chat" && <Chat />}
        {activeView === "dashboard" && <Analytics />}
        {activeView === "orders" && <OrdersTable />}
      </main>
    </div>
  );
}
