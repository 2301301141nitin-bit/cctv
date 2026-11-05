"use client";

import { ComplexEvent } from "../lib/types";
import { doc, updateDoc } from "firebase/firestore";
import { db } from "../lib/firebase";
import { ShieldCheck, XCircle, AlertOctagon, Info } from "lucide-react";

interface EventDetailProps {
  event: ComplexEvent | null;
}

export default function EventDetail({ event }: EventDetailProps) {
  if (!event) {
    return (
      <div className="flex-1 bg-black flex items-center justify-center text-gray-500 flex-col gap-4">
        <AlertOctagon size={48} className="text-gray-800" />
        <p>Select an event from the feed to view details and evidence.</p>
      </div>
    );
  }

  const handleFeedback = async (feedback: "confirmed" | "false_positive") => {
    try {
      const eventRef = doc(db, "events", event.id);
      await updateDoc(eventRef, { operator_feedback: feedback });
    } catch (error) {
      console.error("Error updating feedback:", error);
    }
  };

  return (
    <div className="flex-1 bg-black text-white flex flex-col h-screen overflow-y-auto p-6">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">{event.event_type}</h2>
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <span>Camera: {event.camera_id}</span>
            <span>|</span>
            <span>Node: {event.node_id}</span>
            <span>|</span>
            <span>Risk Score: {(event.risk_score * 100).toFixed(0)}%</span>
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={() => handleFeedback("confirmed")}
            className={`flex items-center gap-2 px-4 py-2 rounded text-sm font-semibold transition-colors ${
              event.operator_feedback === "confirmed" 
                ? "bg-green-600 text-white" 
                : "bg-gray-800 text-gray-300 hover:bg-green-600 hover:text-white"
            }`}
          >
            <ShieldCheck size={16} /> Confirm
          </button>
          <button
            onClick={() => handleFeedback("false_positive")}
            className={`flex items-center gap-2 px-4 py-2 rounded text-sm font-semibold transition-colors ${
              event.operator_feedback === "false_positive" 
                ? "bg-red-600 text-white" 
                : "bg-gray-800 text-gray-300 hover:bg-red-600 hover:text-white"
            }`}
          >
            <XCircle size={16} /> False Positive
          </button>
        </div>
      </div>

      {/* Evidence Snapshot */}
      <div className="bg-gray-900 rounded-lg overflow-hidden border border-gray-800 mb-6 aspect-video flex items-center justify-center relative">
        {event.snapshot_url ? (
          <img src={event.snapshot_url} alt="Event Evidence" className="object-contain w-full h-full" />
        ) : (
          <div className="text-gray-600 flex flex-col items-center">
            <Info size={32} className="mb-2" />
            <p>No snapshot evidence available</p>
          </div>
        )}
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-900 p-4 rounded-lg border border-gray-800">
          <h3 className="text-sm font-bold text-gray-400 uppercase mb-3">Event Timeline</h3>
          <ul className="text-sm space-y-3">
            <li className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-blue-500 mt-1.5"></div>
              <div>
                <p className="text-white">Detection Triggered</p>
                <p className="text-gray-500 text-xs">System identified {event.event_type}</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-gray-600 mt-1.5"></div>
              <div>
                <p className="text-gray-400">Operator Review</p>
                <p className="text-gray-500 text-xs">
                  {event.operator_feedback === "pending" ? "Awaiting your response" : `Marked as ${event.operator_feedback}`}
                </p>
              </div>
            </li>
          </ul>
        </div>
        
        <div className="bg-gray-900 p-4 rounded-lg border border-gray-800">
          <h3 className="text-sm font-bold text-gray-400 uppercase mb-3">Detection Entities</h3>
          <p className="text-sm text-gray-300 mb-2">Track IDs involved:</p>
          <div className="flex flex-wrap gap-2">
            {event.entity_ids?.map(id => (
              <span key={id} className="bg-gray-800 text-blue-400 px-2 py-1 rounded text-xs font-mono">
                ID: {id}
              </span>
            ))}
            {(!event.entity_ids || event.entity_ids.length === 0) && (
              <span className="text-gray-500 text-sm">None</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
