'use client';

import { useQueries, useQuery } from '@tanstack/react-query';
import { ArrowRight, Clock3, Database, MessagesSquare, Sparkles } from 'lucide-react';
import Link from 'next/link';

import { ConnectionForm } from '@/components/connection-form';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { api } from '@/lib/api';
import { formatTimestamp, truncate } from '@/lib/utils';

const examplePrompts = [
  'Show monthly revenue for the last 12 months',
  'Who are the top 5 customers by total spend?',
  'Which products had the biggest drop in sales month over month?',
];

export function DashboardClient() {
  const connectionsQuery = useQuery({
    queryKey: ['connections'],
    queryFn: api.listConnections,
  });

  const sessionQueries = useQueries({
    queries: (connectionsQuery.data ?? []).slice(0, 6).map((connection) => ({
      queryKey: ['sessions', connection.id],
      queryFn: () => api.listSessions(connection.id),
    })),
  });

  const recentChats = sessionQueries
    .flatMap((query) => query.data ?? [])
    .sort((a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt))
    .slice(0, 5);

  return (
    <main className="min-h-screen px-4 py-10 md:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <section className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
          <Card className="overflow-hidden bg-hero-grid">
            <CardContent className="flex min-h-[320px] flex-col justify-between gap-8 p-8">
              <div className="space-y-4">
                <Badge className="bg-white/80 text-cyan-900">
                  Natural language to database
                </Badge>
                <div className="space-y-3">
                  <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-slate-950 md:text-5xl">
                    AI SQL Copilot for fast answers, safer queries, and explainable plans.
                  </h1>
                  <p className="max-w-2xl text-base text-slate-600">
                    Connect PostgreSQL, SQLite, or DuckDB. Generate schema-aware SQL,
                    validate it server-side, visualize results, and get plan plus index guidance in one workspace.
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-3">
                <ConnectionForm />
                {connectionsQuery.data?.[0] ? (
                  <Link
                    className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                    href={`/workspace/${connectionsQuery.data[0].id}`}
                  >
                    Open latest workspace
                  </Link>
                ) : (
                  <Button variant="outline" disabled>
                    Open latest workspace
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Example prompts</CardTitle>
              <CardDescription>Designed for the included demo sales data.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {examplePrompts.map((prompt) => (
                <div
                  key={prompt}
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700"
                >
                  {prompt}
                </div>
              ))}
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr_0.8fr]">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-4 w-4 text-cyan-700" />
                Saved connections
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {connectionsQuery.data?.length ? (
                connectionsQuery.data.map((connection) => (
                  <Link
                    key={connection.id}
                    href={`/workspace/${connection.id}`}
                    className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-4 transition hover:-translate-y-0.5 hover:border-cyan-200"
                  >
                    <div>
                      <p className="font-medium text-slate-900">{connection.name}</p>
                      <p className="text-sm text-slate-500">
                        {connection.type} • {connection.status}
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-slate-400" />
                  </Link>
                ))
              ) : (
                <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
                  No connections yet. Create one to unlock schema discovery and chat.
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessagesSquare className="h-4 w-4 text-orange-500" />
                Recent chats
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {recentChats.length ? (
                recentChats.map((session) => (
                  <Link
                    key={session.id}
                    href={`/workspace/${session.connectionId}?session=${session.id}`}
                    className="block rounded-2xl border border-slate-200 bg-white px-4 py-4 hover:border-orange-200"
                  >
                    <p className="font-medium text-slate-900">{session.title}</p>
                    <p className="mt-1 text-sm text-slate-500">
                      {truncate(session.lastMessage?.content ?? 'No messages yet')}
                    </p>
                  </Link>
                ))
              ) : (
                <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
                  Recent chat sessions will appear after the first generated SQL exchange.
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock3 className="h-4 w-4 text-slate-500" />
                Health snapshot
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm text-slate-500">Backend reachability</p>
                <p className="mt-2 text-2xl font-semibold text-slate-950">
                  {connectionsQuery.isError ? 'Unavailable' : 'Ready'}
                </p>
              </div>
              <div className="rounded-2xl bg-cyan-50 p-4 text-sm text-cyan-900">
                <Sparkles className="mb-2 h-4 w-4" />
                Generated SQL is validated server-side before execution, with row limits and read-only guardrails enabled.
              </div>
              {connectionsQuery.data?.[0] ? (
                <p className="text-xs text-slate-500">
                  Latest connection updated{' '}
                  {formatTimestamp(connectionsQuery.data[0].updatedAt)}.
                </p>
              ) : null}
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}
