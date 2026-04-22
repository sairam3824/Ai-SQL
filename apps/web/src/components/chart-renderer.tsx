'use client';

import type { QueryResult } from '@ai-sql-copilot/shared';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function ChartRenderer({
  result,
  chartType,
}: {
  result?: QueryResult | null;
  chartType: string;
}) {
  if (!result || result.columns.length < 2) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Chart</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-slate-500">
          A chart appears when the result set has a category or time axis with a
          numeric measure.
        </CardContent>
      </Card>
    );
  }

  const xKey = result.columns[0];
  const yKey = result.columns[1];
  const data = result.rows.map((row) => ({
    [xKey]: row[xKey],
    [yKey]: Number(row[yKey] ?? 0),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Visualization</CardTitle>
      </CardHeader>
      <CardContent className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'line' ? (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey={xKey} stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip />
              <Line
                type="monotone"
                dataKey={yKey}
                stroke="#0891b2"
                strokeWidth={3}
                dot={{ r: 3 }}
              />
            </LineChart>
          ) : chartType === 'pie' ? (
            <PieChart>
              <Tooltip />
              <Pie
                data={data}
                nameKey={xKey}
                dataKey={yKey}
                innerRadius={58}
                outerRadius={92}
                fill="#0891b2"
              />
            </PieChart>
          ) : (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey={xKey} stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip />
              <Bar dataKey={yKey} fill="#f97316" radius={[8, 8, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
