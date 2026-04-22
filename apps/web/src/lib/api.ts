import type {
  ChatMessage,
  ChatSessionSummary,
  ConnectionSummary,
  ExplainResult,
  IndexSuggestion,
  IndexAdviceResult,
  QueryResult,
  SchemaColumn,
  SchemaForeignKey,
  SchemaIndex,
  SchemaMetadata,
  SchemaTable,
  SqlGenerationResult,
} from '@ai-sql-copilot/shared';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';

const DEFAULT_TIMEOUT_MS = 60_000;

async function apiFetch<T>(
  path: string,
  init?: RequestInit & { timeoutMs?: number },
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    init?.timeoutMs ?? DEFAULT_TIMEOUT_MS,
  );

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        ...(init?.body instanceof FormData
          ? {}
          : { 'Content-Type': 'application/json' }),
        ...(init?.headers ?? {}),
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      const payload = await response
        .json()
        .catch(() => ({ detail: 'Unexpected API error.' }));
      throw new Error(payload.detail ?? 'Unexpected API error.');
    }

    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.');
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export interface ConnectionFormPayload {
  name: string;
  type: 'postgresql' | 'sqlite' | 'duckdb';
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  ssl?: boolean;
  file?: File | null;
  createDuckdb?: boolean;
}

function buildConnectionFormData(payload: ConnectionFormPayload) {
  const formData = new FormData();
  formData.append('name', payload.name);
  formData.append('type', payload.type);
  if (payload.host) formData.append('host', payload.host);
  if (payload.port) formData.append('port', String(payload.port));
  if (payload.database) formData.append('database', payload.database);
  if (payload.username) formData.append('username', payload.username);
  if (payload.password) formData.append('password', payload.password);
  if (payload.ssl) formData.append('ssl', 'true');
  if (payload.createDuckdb) formData.append('create_duckdb', 'true');
  if (payload.file) formData.append('file', payload.file);
  return formData;
}

type ConnectionApi = {
  id: string;
  name: string;
  type: 'postgresql' | 'sqlite' | 'duckdb';
  status: 'connected' | 'error' | 'unknown';
  status_message?: string | null;
  created_at: string;
  updated_at: string;
  config_summary: Record<string, string | number | boolean | null>;
  schema_cached_at?: string | null;
};

type SchemaApi = {
  connection_id: string;
  refreshed_at: string;
  summary: string;
  tables: Array<{
    name: string;
    schema?: string | null;
    columns: Array<{
      name: string;
      data_type: string;
      nullable: boolean;
      default_value?: string | null;
    }>;
    primary_key: string[];
    foreign_keys: Array<{
      constrained_columns: string[];
      referred_table: string;
      referred_columns: string[];
    }>;
    indexes: Array<{
      name: string;
      columns: string[];
      unique: boolean;
    }>;
    estimated_row_count?: number | null;
  }>;
};

type SessionApi = {
  id: string;
  connection_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  last_message?: MessageApi | null;
  messages?: MessageApi[];
};

type MessageApi = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  generated_sql?: string | null;
  created_at: string;
  metadata?: Record<string, unknown> | null;
};

type SqlGenerationApi = {
  session_id: string;
  sql: string;
  explanation: string;
  assumptions: string[];
  warnings: string[];
  visualization_suggestion?: string | null;
  confidence: 'high' | 'medium' | 'low';
};

type QueryResultApi = {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
  execution_time_ms: number;
  truncated: boolean;
  page: number;
  page_size: number;
  chart_recommendation?: string | null;
};

type ExplainApi = {
  dialect: 'postgresql' | 'sqlite' | 'duckdb';
  raw_plan: unknown;
  summary: string;
  insights: Array<{
    title: string;
    detail: string;
    severity: 'info' | 'warning' | 'high';
  }>;
};

type IndexAdviceApi = {
  overview: string;
  suggestions: Array<{
    summary: string;
    rationale: string;
    statement: string;
    confidence: 'high' | 'medium' | 'low';
    tradeoffs: string[];
  }>;
};

function mapConnection(connection: ConnectionApi): ConnectionSummary & {
  schemaCachedAt?: string | null;
} {
  return {
    id: connection.id,
    name: connection.name,
    type: connection.type,
    status: connection.status,
    statusMessage: connection.status_message,
    createdAt: connection.created_at,
    updatedAt: connection.updated_at,
    configSummary: connection.config_summary,
    schemaCachedAt: connection.schema_cached_at,
  };
}

function mapColumn(column: SchemaApi['tables'][number]['columns'][number]): SchemaColumn {
  return {
    name: column.name,
    dataType: column.data_type,
    nullable: column.nullable,
    defaultValue: column.default_value,
  };
}

function mapIndex(index: SchemaApi['tables'][number]['indexes'][number]): SchemaIndex {
  return {
    name: index.name,
    columns: index.columns,
    unique: index.unique,
  };
}

function mapForeignKey(
  foreignKey: SchemaApi['tables'][number]['foreign_keys'][number],
): SchemaForeignKey {
  return {
    constrainedColumns: foreignKey.constrained_columns,
    referredTable: foreignKey.referred_table,
    referredColumns: foreignKey.referred_columns,
  };
}

function mapTable(table: SchemaApi['tables'][number]): SchemaTable {
  return {
    name: table.name,
    schema: table.schema,
    columns: table.columns.map(mapColumn),
    primaryKey: table.primary_key,
    foreignKeys: table.foreign_keys.map(mapForeignKey),
    indexes: table.indexes.map(mapIndex),
    estimatedRowCount: table.estimated_row_count,
  };
}

function mapSchema(schema: SchemaApi): SchemaMetadata {
  return {
    connectionId: schema.connection_id,
    refreshedAt: schema.refreshed_at,
    summary: schema.summary,
    tables: schema.tables.map(mapTable),
  };
}

function mapMessage(message: MessageApi): ChatMessage {
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    generatedSql: message.generated_sql,
    createdAt: message.created_at,
    metadata: message.metadata,
  };
}

function mapSession(session: SessionApi): ChatSessionSummary {
  return {
    id: session.id,
    connectionId: session.connection_id,
    title: session.title,
    createdAt: session.created_at,
    updatedAt: session.updated_at,
    lastMessage: session.last_message ? mapMessage(session.last_message) : null,
  };
}

function mapSqlGeneration(
  response: SqlGenerationApi,
): SqlGenerationResult & { session_id: string } {
  return {
    session_id: response.session_id,
    sql: response.sql,
    explanation: response.explanation,
    assumptions: response.assumptions,
    warnings: response.warnings,
    visualizationSuggestion: response.visualization_suggestion,
    confidence: response.confidence,
  };
}

function mapQueryResult(response: QueryResultApi): QueryResult {
  return {
    columns: response.columns,
    rows: response.rows,
    rowCount: response.row_count,
    executionTimeMs: response.execution_time_ms,
    truncated: response.truncated,
    page: response.page,
    pageSize: response.page_size,
    chartRecommendation: response.chart_recommendation,
  };
}

function mapExplain(response: ExplainApi): ExplainResult {
  return {
    dialect: response.dialect,
    rawPlan: response.raw_plan,
    summary: response.summary,
    insights: response.insights,
  };
}

function mapSuggestion(
  suggestion: IndexAdviceApi['suggestions'][number],
): IndexSuggestion {
  return suggestion;
}

function mapIndexAdvice(response: IndexAdviceApi): IndexAdviceResult {
  return {
    overview: response.overview,
    suggestions: response.suggestions.map(mapSuggestion),
  };
}

export const api = {
  health: () => apiFetch<{ status: string; timestamp: string }>('/health'),
  listConnections: async () =>
    (await apiFetch<ConnectionApi[]>('/connections')).map(mapConnection),
  getConnection: async (id: string) =>
    mapConnection(await apiFetch<ConnectionApi>(`/connections/${id}`)),
  testConnection: (payload: ConnectionFormPayload) =>
    apiFetch<{
      ok: boolean;
      message: string;
      inferred_name?: string | null;
      config_summary: Record<string, unknown>;
    }>('/connections/test', {
      method: 'POST',
      body: buildConnectionFormData(payload),
    }),
  createConnection: async (payload: ConnectionFormPayload) =>
    mapConnection(
      await apiFetch<ConnectionApi>('/connections', {
        method: 'POST',
        body: buildConnectionFormData(payload),
      }),
    ),
  deleteConnection: (id: string) =>
    apiFetch<{ ok: boolean }>(`/connections/${id}`, {
      method: 'DELETE',
    }),
  getSchema: async (connectionId: string) =>
    mapSchema(await apiFetch<SchemaApi>(`/connections/${connectionId}/schema`)),
  refreshSchema: async (connectionId: string) =>
    mapSchema(
      await apiFetch<SchemaApi>(`/connections/${connectionId}/schema/refresh`, {
        method: 'POST',
      }),
    ),
  listSessions: async (connectionId: string) =>
    (await apiFetch<SessionApi[]>(`/connections/${connectionId}/sessions`)).map(
      mapSession,
    ),
  createSession: (connectionId: string, title?: string) =>
    apiFetch<SessionApi>(`/connections/${connectionId}/sessions`, {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),
  getSession: async (id: string) => {
    const session = await apiFetch<SessionApi>(`/sessions/${id}`);
    return {
      id: session.id,
      connectionId: session.connection_id,
      title: session.title,
      createdAt: session.created_at,
      updatedAt: session.updated_at,
      messages: (session.messages ?? []).map(mapMessage),
    };
  },
  generateSql: async (
    connectionId: string,
    payload: { question: string; session_id?: string | null },
  ) =>
    mapSqlGeneration(
      await apiFetch<SqlGenerationApi>(
        `/connections/${connectionId}/generate-sql`,
        {
          method: 'POST',
          body: JSON.stringify(payload),
        },
      ),
    ),
  executeSql: (
    connectionId: string,
    payload: { sql: string; page: number; page_size: number },
  ) =>
    apiFetch<QueryResultApi>(`/connections/${connectionId}/execute`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }).then(mapQueryResult),
  explainSql: (
    connectionId: string,
    payload: { sql: string; analyze: boolean },
  ) =>
    apiFetch<ExplainApi>(`/connections/${connectionId}/explain`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }).then(mapExplain),
  adviseIndexes: (connectionId: string, payload: { sql: string }) =>
    apiFetch<IndexAdviceApi>(
      `/connections/${connectionId}/advise-indexes`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
    ).then(mapIndexAdvice),
};
