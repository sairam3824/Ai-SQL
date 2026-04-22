export type ConnectionType = 'postgresql' | 'sqlite' | 'duckdb';

export interface ConnectionSummary {
  id: string;
  name: string;
  type: ConnectionType;
  status: 'connected' | 'error' | 'unknown';
  statusMessage?: string | null;
  createdAt: string;
  updatedAt: string;
  configSummary: Record<string, string | number | boolean | null>;
}

export interface SchemaColumn {
  name: string;
  dataType: string;
  nullable: boolean;
  defaultValue?: string | null;
}

export interface SchemaIndex {
  name: string;
  columns: string[];
  unique: boolean;
}

export interface SchemaForeignKey {
  constrainedColumns: string[];
  referredTable: string;
  referredColumns: string[];
}

export interface SchemaTable {
  name: string;
  schema?: string | null;
  columns: SchemaColumn[];
  primaryKey: string[];
  foreignKeys: SchemaForeignKey[];
  indexes: SchemaIndex[];
  estimatedRowCount?: number | null;
}

export interface SchemaMetadata {
  connectionId: string;
  refreshedAt: string;
  summary: string;
  tables: SchemaTable[];
}

export interface SqlGenerationResult {
  sql: string;
  explanation: string;
  assumptions: string[];
  warnings: string[];
  visualizationSuggestion?: string | null;
  confidence: 'high' | 'medium' | 'low';
}

export interface QueryResult {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  rowCount: number;
  executionTimeMs: number;
  truncated: boolean;
  page: number;
  pageSize: number;
  chartRecommendation?: string | null;
}

export interface PlanInsight {
  title: string;
  detail: string;
  severity: 'info' | 'warning' | 'high';
}

export interface ExplainResult {
  dialect: ConnectionType;
  rawPlan: unknown;
  summary: string;
  insights: PlanInsight[];
}

export interface IndexSuggestion {
  summary: string;
  rationale: string;
  statement: string;
  confidence: 'high' | 'medium' | 'low';
  tradeoffs: string[];
}

export interface IndexAdviceResult {
  overview: string;
  suggestions: IndexSuggestion[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  generatedSql?: string | null;
  createdAt: string;
  metadata?: Record<string, unknown> | null;
}

export interface ChatSessionSummary {
  id: string;
  connectionId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  lastMessage?: ChatMessage | null;
}
