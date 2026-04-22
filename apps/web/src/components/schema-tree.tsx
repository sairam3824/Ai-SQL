'use client';

import type { SchemaMetadata } from '@ai-sql-copilot/shared';
import { Database, KeyRound, Table2 } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

export function SchemaTree({ schema }: { schema?: SchemaMetadata }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Schema Explorer</CardTitle>
      </CardHeader>
      <CardContent className="h-[calc(100%-64px)] p-0">
        <ScrollArea className="h-[520px] px-5 pb-5">
          {!schema ? (
            <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
              Connect a database to inspect tables, keys, and indexes.
            </div>
          ) : (
            <div className="space-y-3">
              {schema.tables.map((table) => (
                <details
                  key={`${table.schema ?? 'public'}-${table.name}`}
                  className="rounded-2xl border border-slate-200 bg-white p-4"
                >
                  <summary className="flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-900">
                    <Table2 className="h-4 w-4 text-cyan-700" />
                    {table.schema ? `${table.schema}.` : ''}
                    {table.name}
                    <span className="ml-auto text-xs font-normal text-slate-400">
                      {table.estimatedRowCount ?? '—'} rows
                    </span>
                  </summary>
                  <div className="mt-4 space-y-4 text-sm text-slate-600">
                    <div className="space-y-2">
                      {table.columns.map((column) => (
                        <div
                          key={column.name}
                          className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2"
                        >
                          <div className="flex items-center gap-2">
                            <Database className="h-3.5 w-3.5 text-slate-400" />
                            <span>{column.name}</span>
                          </div>
                          <span className="text-xs uppercase tracking-wide text-slate-400">
                            {column.dataType}
                          </span>
                        </div>
                      ))}
                    </div>
                    {table.primaryKey.length ? (
                      <div className="rounded-xl bg-amber-50 px-3 py-2 text-xs text-amber-800">
                        <KeyRound className="mr-2 inline h-3.5 w-3.5" />
                        Primary key: {table.primaryKey.join(', ')}
                      </div>
                    ) : null}
                  </div>
                </details>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
