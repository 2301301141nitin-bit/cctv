"use client";

import { useState } from "react";
import { Search, SlidersHorizontal, Check } from "lucide-react";

export default function SemanticSearchControl() {
  const [targets, setTargets] = useState("person, car");
  const [confidence, setConfidence] = useState(25);
  const [status, setStatus] = useState<"idle" | "updating" | "success" | "error">("idle");

  const handleUpdate = async () => {
    setStatus("updating");
    try {
      const classList = targets
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t.length > 0);

      // Default fallback
      if (classList.length === 0) {
        classList.push("person", "car");
      }

      const response = await fetch("http://localhost:8000/ai/config", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          targets: classList,
          confidence: confidence / 100.0,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to update AI config");
      }

      setStatus("success");
      setTimeout(() => setStatus("idle"), 2000);
    } catch (error) {
      console.error("Error updating AI settings:", error);
      setStatus("error");
      setTimeout(() => setStatus("idle"), 3000);
    }
  };

  return (
    <div className="bg-gray-900 border-b border-gray-800 p-4 flex flex-col gap-3">
      <div className="flex items-center gap-2 text-gray-300">
        <Search size={16} className="text-blue-500" />
        <span className="text-sm font-semibold uppercase">Global Semantic AI Control</span>
      </div>

      <div className="flex items-center gap-6 bg-gray-800/50 p-3 rounded-md border border-gray-700/50">
        {/* Targets Input */}
        <div className="flex-1 flex items-center gap-3">
          <label className="text-sm text-gray-400 font-medium whitespace-nowrap">Targets:</label>
          <input
            type="text"
            value={targets}
            onChange={(e) => setTargets(e.target.value)}
            placeholder="e.g. red shirt, backpack, black car"
            className="w-full bg-gray-900 text-white text-sm rounded border border-gray-700 px-3 py-1.5 outline-none focus:border-blue-500"
          />
        </div>

        {/* Confidence Slider */}
        <div className="flex items-center gap-4 w-64">
          <div className="flex items-center gap-2 text-sm text-gray-400 font-medium whitespace-nowrap">
            <SlidersHorizontal size={14} />
            Strictness: {confidence}%
          </div>
          <input
            type="range"
            min="5"
            max="95"
            step="1"
            value={confidence}
            onChange={(e) => setConfidence(parseInt(e.target.value))}
            className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>

        {/* Update Button */}
        <button
          onClick={handleUpdate}
          disabled={status === "updating"}
          className={`flex items-center justify-center gap-2 px-4 py-1.5 rounded text-sm font-medium transition-colors min-w-[140px]
            ${
              status === "success"
                ? "bg-green-600 hover:bg-green-700 text-white"
                : status === "error"
                ? "bg-red-600 hover:bg-red-700 text-white"
                : "bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
            }
          `}
        >
          {status === "updating" ? (
            "Updating..."
          ) : status === "success" ? (
            <>
              <Check size={16} /> Updated
            </>
          ) : status === "error" ? (
            "Failed"
          ) : (
            "Update Inference Nodes"
          )}
        </button>
      </div>
    </div>
  );
}
