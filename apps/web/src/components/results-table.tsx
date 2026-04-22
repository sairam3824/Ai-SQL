'use client';

import type { QueryResult } from '@ai-sql-copilot/shared';

import { ChartRenderer } from '@/components/chart-renderer';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export function ResultsTable({
  result,
  chartType,
}: {
  result?: QueryResult | null;
  chartType: string;
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Results</CardTitle>
      </CardHeader>
      <CardContent>
        {!result ? (
          <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
            Run a safe query to view rows, execution time, and chart options.
          </div>
        ) : (
          <Tabs defaultValue="table" className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap gap-2 text-xs text-slate-500">
                <span>{result.rowCount} rows returned</span>
                <span>•</span>
                <span>{result.executionTimeMs.toFixed(1)} ms</span>
                <span>•</span>
                <span>{result.truncated ? 'Truncated by safety cap' : 'Complete page'}</span>
              </div>
              <TabsList>
                <TabsTrigger value="table">Table</TabsTrigger>
                <TabsTrigger value="chart">Chart</TabsTrigger>
                <TabsTrigger value="json">Raw JSON</TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="table">
              <ScrollArea className="w-full rounded-2xl border border-slate-200">
                <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      {result.columns.map((column) => (
                        <th key={column} className="px-4 py-3 font-medium text-slate-700">
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {result.rows.map((row, index) => (
                      <tr key={index}>
                        {result.columns.map((column) => (
                          <td key={`${index}-${column}`} className="px-4 py-3 text-slate-600">
                            {String(row[column] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="chart">
              {chartType === 'table' ? (
                <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
                  No chart is recommended for this result shape yet. You can still switch the chart type in the insights panel.
                </div>
              ) : (
                <ChartRenderer result={result} chartType={chartType} />
              )}
            </TabsContent>

            <TabsContent value="json">
              <pre className="max-h-[360px] overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-cyan-100">
                <code>{JSON.stringify(result.rows, null, 2)}</code>
              </pre>
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}
