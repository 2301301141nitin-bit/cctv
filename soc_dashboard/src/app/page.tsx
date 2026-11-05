"use client";

import { useState } from "react";
import CameraList from "../components/CameraList";
import EventFeed from "../components/EventFeed";
import EventDetail from "../components/EventDetail";
import SemanticSearchControl from "../components/SemanticSearchControl";
import FilterBar from "../components/FilterBar";
import { ComplexEvent } from "../lib/types";

export default function DashboardPage() {
  const [selectedEvent, setSelectedEvent] = useState<ComplexEvent | null>(null);

  return (
    <main className="flex h-screen w-full bg-black text-white">
      {/* Sidebar: Cameras */}
      <CameraList />
      
      {/* Middle Column: Event Feed */}
      <EventFeed 
        onSelectEvent={(event) => setSelectedEvent(event)} 
        selectedEventId={selectedEvent?.id} 
      />
      
      {/* Right Column: Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <SemanticSearchControl />
        <FilterBar />
        <EventDetail event={selectedEvent} />
      </div>
    </main>
  );
}
