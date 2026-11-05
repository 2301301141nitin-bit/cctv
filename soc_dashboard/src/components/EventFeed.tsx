"use client";

import { useEffect, useState } from "react";
import { collection, onSnapshot, query, orderBy, limit } from "firebase/firestore";
import { db } from "../lib/firebase";
import { ComplexEvent } from "../lib/types";
import { AlertTriangle, Clock, ShieldAlert } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

const severityColors = {
  INFO: "bg-blue-500",
  LOW: "bg-green-500",
  MEDIUM: "bg-yellow-500",
  HIGH: "bg-orange-500",
  CRITICAL: "bg-red-500",
};

interface EventFeedProps {
  onSelectEvent: (event: ComplexEvent) => void;
  selectedEventId?: string;
}

export default function EventFeed({ onSelectEvent, selectedEventId }: EventFeedProps) {
  const [events, setEvents] = useState<ComplexEvent[]>([]);

  useEffect(() => {
    // In a real app, we would apply filters here (where clauses)
    const q = query(collection(db, "events"), orderBy("timestamp", "desc"), limit(50));
    
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const eventsData = snapshot.docs.map((doc) => ({
        id: doc.id,
        ...doc.data(),
      })) as ComplexEvent[];
      setEvents(eventsData);
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="w-80 bg-gray-900 border-r border-gray-800 h-screen flex flex-col">
      <div className="p-4 border-b border-gray-800">
        <h2 className="text-sm uppercase text-gray-400 font-semibold flex items-center gap-2">
          <ShieldAlert size={16} /> Real-time Events
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto">
        {events.length === 0 ? (
          <div className="p-4 text-sm text-gray-500 text-center mt-10">
            No events detected.
          </div>
        ) : (
          events.map((event) => (
            <div
              key={event.id}
              onClick={() => onSelectEvent(event)}
              className={`p-4 border-b border-gray-800 cursor-pointer transition-colors hover:bg-gray-800 ${
                selectedEventId === event.id ? "bg-gray-800 border-l-4 border-blue-500" : "border-l-4 border-transparent"
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className={`text-xs px-2 py-0.5 rounded font-bold text-white ${severityColors[event.severity]}`}>
                  {event.severity}
                </span>
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock size={12} />
                  {event.timestamp ? formatDistanceToNow(new Date(event.timestamp * 1000), { addSuffix: true }) : "Just now"}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-white mb-1">{event.event_type}</h3>
              <p className="text-xs text-gray-400">Cam: {event.camera_id}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
