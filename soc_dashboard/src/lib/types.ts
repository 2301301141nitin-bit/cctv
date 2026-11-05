export interface Camera {
  id: string;
  source: string;
  status: "running" | "stopped";
  sampling_rate: number;
}

export interface Node {
  id: string; // Document ID
  status: string;
  last_heartbeat: any; // Firestore Timestamp
  cameras?: Camera[];
}

export interface ComplexEvent {
  id: string; // Document ID (same as event_id)
  event_id: string;
  camera_id: string;
  node_id: string;
  timestamp: any; // Firestore Timestamp or float
  event_type: string; // e.g. "Restricted Zone Entry"
  severity: "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  risk_score: number;
  entity_ids: number[];
  snapshot_url?: string;
  operator_feedback: "pending" | "confirmed" | "false_positive";
  metadata?: Record<string, any>;
}
