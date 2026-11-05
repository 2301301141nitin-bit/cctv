"use client";

import { useEffect, useState } from "react";
import { collection, onSnapshot, query } from "firebase/firestore";
import { db } from "../lib/firebase";
import { Node, Camera } from "../lib/types";
import { Server, Video, Activity, Wifi, WifiOff } from "lucide-react";

export default function CameraList() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);

  useEffect(() => {
    // In a real app we would query nodes and their subcollections
    // For this prototype, we'll just mock or use a flat listener if we structured it flatly.
    // For now, let's assume a simplified structure or just UI mocking if no data.
    const q = query(collection(db, "nodes"));
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const nodesData = snapshot.docs.map((doc) => ({
        id: doc.id,
        ...doc.data(),
      })) as Node[];
      setNodes(nodesData);
      
      // Let's assume cameras are stored at /cameras for easy querying in the dashboard
      // Or we can just show static UI if empty
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="w-64 bg-gray-900 border-r border-gray-800 h-screen flex flex-col p-4 text-white">
      <div className="flex items-center gap-2 mb-8">
        <Activity className="text-blue-500" />
        <h1 className="text-lg font-bold">SOC Dashboard</h1>
      </div>

      <div className="flex-1 overflow-y-auto">
        <h2 className="text-xs uppercase text-gray-500 font-semibold mb-3">Nodes & Cameras</h2>
        
        {nodes.length === 0 ? (
          <div className="text-sm text-gray-500">No nodes connected. Waiting for inference nodes...</div>
        ) : (
          nodes.map((node) => (
            <div key={node.id} className="mb-4">
              <div className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
                <div className="flex items-center gap-2">
                  <Server size={16} />
                  <span>{node.id}</span>
                </div>
                {node.status === "online" ? (
                  <Wifi size={14} className="text-green-500" />
                ) : (
                  <WifiOff size={14} className="text-red-500" />
                )}
              </div>
              
              {/* This would map over node.cameras if we fetched the subcollection */}
              <div className="pl-6 space-y-2">
                 <div className="flex items-center gap-2 text-xs text-gray-400 bg-gray-800 p-2 rounded">
                    <Video size={14} />
                    <span>Camera 0 (Running)</span>
                 </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
