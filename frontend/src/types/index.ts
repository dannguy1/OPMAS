export enum AgentStatus {
  RUNNING = 'running',
  STOPPED = 'stopped',
  ERROR = 'error',
}

export enum FindingSeverity {
  LOW = 'Low',
  MEDIUM = 'Medium',
  HIGH = 'High',
  CRITICAL = 'Critical',
}

export interface Agent {
  id: number;
  name: string;
  package_name: string;
  subscribed_topics: string[];
  enabled: boolean;
  status: AgentStatus;
  created_at: string;
  updated_at: string;
}

export interface AgentRule {
  id: number;
  agent_id: number;
  name: string;
  description: string;
  pattern: string;
  severity: FindingSeverity;
  enabled: boolean;
  cooldown_seconds: number;
  threshold: number;
  created_at: string;
  updated_at: string;
}

export interface Finding {
  id: number;
  finding_type: string;
  agent_name: string;
  resource_id: string;
  severity: FindingSeverity;
  message: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface FindingFilter {
  agent_name?: string;
  finding_type?: string;
  severity?: FindingSeverity;
  resource_id?: string;
  start_time?: string;
  end_time?: string;
  sort_by?: string;
  sort_desc?: boolean;
  limit?: number;
  offset?: number;
} 