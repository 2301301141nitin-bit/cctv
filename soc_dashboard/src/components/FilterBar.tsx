"use client";

import { Filter } from "lucide-react";

export default function FilterBar() {
  return (
    <div className="bg-gray-900 border-b border-gray-800 p-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-gray-400">
          <Filter size={16} />
          <span className="text-sm font-semibold uppercase">Filters</span>
        </div>
        
        <select className="bg-gray-800 text-white text-sm rounded border border-gray-700 px-3 py-1 outline-none focus:border-blue-500">
          <option value="all">All Cameras</option>
          <option value="0">Camera 0</option>
          <option value="1">Camera 1</option>
        </select>

        <select className="bg-gray-800 text-white text-sm rounded border border-gray-700 px-3 py-1 outline-none focus:border-blue-500">
          <option value="all">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
          <option value="INFO">Info</option>
        </select>
        
        <select className="bg-gray-800 text-white text-sm rounded border border-gray-700 px-3 py-1 outline-none focus:border-blue-500">
          <option value="all">Any Time</option>
          <option value="1h">Last Hour</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
        </select>
      </div>
      
      <div className="text-sm text-gray-500">
        Showing real-time stream
      </div>
    </div>
  );
}
