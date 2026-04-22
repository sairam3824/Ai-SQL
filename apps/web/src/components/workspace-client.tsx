'use client';

import type {
  ChatMessage,
  ExplainResult,
  IndexAdviceResult,
  QueryResult,
  SqlGenerationResult,
} from '@ai-sql-copilot/shared';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2, Play, RefreshCw, ScanSearch } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';

import { ChatPanel } from '@/components/chat-panel';
import { PlanInsightPanel } from '@/components/plan-insight-panel';
import { ResultsTable } from '@/components/results-table';
import { SchemaTree } from '@/components/schema-tree';
import { SqlEditor } from '@/components/sql-editor';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { api } from '@/lib/api';
import { formatTimestamp, getErrorMessage, truncate } from '@/lib/utils';

export function WorkspaceClient({ connectionId }: { connectionId: string }) {
  const searchParams = useSearchParams();
  const initialSessionId = searchParams.get('session');
  const queryClient = useQueryClient();

  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    initialSessionId,
  );
  const [prompt, setPrompt] = useState('');
  const [sql, setSql] = useState('');
  const [generation, setGeneration] = useState<SqlGenerationResult | null>(null);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [explain, setExplain] = useState<ExplainResult | null>(null);
  const [indexAdvice, setIndexAdvice] = useState<IndexAdviceResult | null>(null);
  const [chartType, setChartType] = useState('table');

  const connectionQuery = useQuery({
    queryKey: ['connection', connectionId],
    queryFn: () => api.getConnection(connectionId),
  });

  const schemaQuery = useQuery({
    queryKey: ['schema', connectionId],
    queryFn: () => api.getSchema(connectionId),
  });

  const sessionsQuery = useQuery({
    queryKey: ['sessions', connectionId],
    queryFn: () => api.listSessions(connectionId),
  });

  const sessionQuery = useQuery({
    queryKey: ['session', selectedSessionId],
    queryFn: () => api.getSession(selectedSessionId as string),
    enabled: Boolean(selectedSessionId),
  });

  useEffect(() => {
    if (!selectedSessionId && sessionsQuery.data?.[0]) {
      setSelectedSessionId(sessionsQuery.data[0].id);
    }
  }, [selectedSessionId, sessionsQuery.data]);

  // Reset display state when switching sessions to avoid showing stale results
  useEffect(() => {
    setGeneration(null);
    setSql('');
    setResult(null);
    setExplain(null);
    setIndexAdvice(null);
    setChartType('table');
  }, [selectedSessionId]);

  const messages = useMemo<ChatMessage[]>(
    () => sessionQuery.data?.messages ?? [],
    [sessionQuery.data],
  );

  const generateMutation = useMutation<
    Awaited<ReturnType<typeof api.generateSql>>,
    Error,
    string
  >({
    mutationFn: (question: string) =>
      api.generateSql(connectionId, {
        question,
        session_id: selectedSessionId,
      }),
    onSuccess: async (data) => {
      setSelectedSessionId(data.session_id);
      setGeneration(data);
      setSql(data.sql);
      if (data.visualizationSuggestion) {
        setChartType(data.visualizationSuggestion);
      }
      setPrompt('');
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['sessions', connectionId] }),
        queryClient.invalidateQueries({ queryKey: ['session', data.session_id] }),
      ]);
    },
  });

  const executeMutation = useMutation<
    Awaited<ReturnType<typeof api.executeSql>>,
    Error
  >({
    mutationFn: () =>
      api.executeSql(connectionId, {
        sql,
        page: 1,
        page_size: 100,
      }),
    onSuccess: (data) => {
      setResult(data);
      if (data.chartRecommendation) {
        setChartType(data.chartRecommendation);
      }
    },
  });

  const explainMutation = useMutation<
    Awaited<ReturnType<typeof api.explainSql>>,
    Error
  >({
    mutationFn: () => api.explainSql(connectionId, { sql, analyze: false }),
    onSuccess: setExplain,
  });

  const indexMutation = useMutation<
    Awaited<ReturnType<typeof api.adviseIndexes>>,
    Error
  >({
    mutationFn: () => api.adviseIndexes(connectionId, { sql }),
    onSuccess: setIndexAdvice,
  });

  const refreshSchemaMutation = useMutation<
    Awaited<ReturnType<typeof api.refreshSchema>>,
    Error
  >({
    mutationFn: () => api.refreshSchema(connectionId),
    onSuccess: async (schema) => {
      await queryClient.setQueryData(['schema', connectionId], schema);
    },
  });

  const busy =
    generateMutation.isPending ||
    executeMutation.isPending ||
    explainMutation.isPending ||
    indexMutation.isPending;
  const combinedError =
    generateMutation.error ??
    executeMutation.error ??
    explainMutation.error ??
    indexMutation.error;

  return (
    <main className="min-h-screen p-4 md:p-6">
      <div className="mx-auto max-w-[1600px] space-y-4">
        <Card className="border-white/80 bg-white/80">
          <CardContent className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-cyan-700">
                Workspace
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-3">
                <h1 className="text-2xl font-semibold text-slate-950">
                  {connectionQuery.data?.name ?? 'Loading connection…'}
                </h1>
                {connectionQuery.data ? (
                  <Badge>{connectionQuery.data.type}</Badge>
                ) : null}
                {connectionQuery.data ? (
                  <Badge className="bg-emerald-50 text-emerald-700">
                    {connectionQuery.data.status}
                  </Badge>
                ) : null}
              </div>
              <p className="mt-2 text-sm text-slate-500">
                Cached schema refreshed{' '}
                {connectionQuery.data?.schemaCachedAt
                  ? formatTimestamp(connectionQuery.data.schemaCachedAt)
                  : 'not yet'}.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                onClick={() => refreshSchemaMutation.mutate()}
                disabled={refreshSchemaMutation.isPending}
              >
                {refreshSchemaMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Refresh Schema
              </Button>
              <Button onClick={() => executeMutation.mutate()} disabled={busy || !sql}>
                {executeMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                Run Query
              </Button>
              <Button
                variant="secondary"
                onClick={() => explainMutation.mutate()}
                disabled={busy || !sql}
              >
                <ScanSearch className="mr-2 h-4 w-4" />
                Explain Plan
              </Button>
              <Button
                variant="outline"
                onClick={() => indexMutation.mutate()}
                disabled={busy || !sql}
              >
                Suggest Indexes
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 xl:grid-cols-[300px_minmax(0,1fr)_360px]">
          <div className="space-y-4">
            <SchemaTree schema={schemaQuery.data} />
            <Card>
              <CardContent className="p-0">
                <div className="p-5 pb-3">
                  <h3 className="text-base font-semibold text-slate-950">
                    Chat History
                  </h3>
                </div>
                <Separator />
                <ScrollArea className="h-[280px] p-3">
                  <div className="space-y-2 px-2 pb-2">
                    {sessionsQuery.data?.length ? (
                      sessionsQuery.data.map((session) => (
                        <button
                          key={session.id}
                          className={`w-full rounded-2xl px-3 py-3 text-left transition ${
                            selectedSessionId === session.id
                              ? 'bg-slate-950 text-white'
                              : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                          }`}
                          onClick={() => setSelectedSessionId(session.id)}
                        >
                          <p className="text-sm font-medium">{session.title}</p>
                          <p className="mt-1 text-xs opacity-80">
                            {truncate(session.lastMessage?.content ?? 'No messages')}
                          </p>
                        </button>
                      ))
                    ) : (
                      <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
                        Generated chats will be grouped here by connection.
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <ChatPanel
              messages={messages}
              prompt={prompt}
              setPrompt={setPrompt}
              onSubmit={() => generateMutation.mutate(prompt)}
              isLoading={generateMutation.isPending}
            />
            <SqlEditor value={sql} onChange={setSql} />
            <ResultsTable result={result} chartType={chartType} />
            {(executeMutation.isError ||
              explainMutation.isError ||
              indexMutation.isError ||
              generateMutation.isError) && (
              <Card>
                <CardContent className="p-4 text-sm text-red-700">
                  {getErrorMessage(combinedError)}
                </CardContent>
              </Card>
            )}
          </div>

          <PlanInsightPanel
            generation={generation}
            explain={explain}
            indexAdvice={indexAdvice}
            result={result}
            chartType={chartType}
            onChartTypeChange={setChartType}
          />
        </div>
      </div>
    </main>
  );
}
