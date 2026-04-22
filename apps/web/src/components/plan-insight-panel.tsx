'use client';

import type {
  ExplainResult,
  IndexAdviceResult,
  QueryResult,
  SqlGenerationResult,
} from '@ai-sql-copilot/shared';

import { ChartRenderer } from '@/components/chart-renderer';
import { IndexSuggestionCard } from '@/components/index-suggestion-card';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export function PlanInsightPanel({
  generation,
  explain,
  indexAdvice,
  result,
  chartType,
  onChartTypeChange,
}: {
  generation?: SqlGenerationResult | null;
  explain?: ExplainResult | null;
  indexAdvice?: IndexAdviceResult | null;
  result?: QueryResult | null;
  chartType: string;
  onChartTypeChange: (value: string) => void;
}) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Query Explanation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm text-slate-700">
              {generation?.explanation ??
                'Generate SQL to see a natural-language explanation here.'}
            </p>
          </div>
          {generation?.warnings?.length ? (
            <div className="space-y-2">
              {generation.warnings.map((warning) => (
                <div
                  key={warning}
                  className="rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800"
                >
                  {warning}
                </div>
              ))}
            </div>
          ) : null}
          {generation?.assumptions?.length ? (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                Assumptions
              </p>
              {generation.assumptions.map((assumption) => (
                <Badge key={assumption} className="mr-2">
                  {assumption}
                </Badge>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Plan Insights</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-slate-700">
            {explain?.summary ??
              'Explain a query to review scans, sorts, joins, and likely bottlenecks.'}
          </p>
          {explain?.insights?.map((insight) => (
            <div
              key={`${insight.title}-${insight.detail}`}
              className={`rounded-xl px-3 py-2 text-sm ${
                insight.severity === 'high'
                  ? 'bg-red-50 text-red-700'
                  : insight.severity === 'warning'
                    ? 'bg-amber-50 text-amber-800'
                    : 'bg-cyan-50 text-cyan-800'
              }`}
            >
              <p className="font-semibold">{insight.title}</p>
              <p>{insight.detail}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Chart Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Select value={chartType} onValueChange={onChartTypeChange}>
            <SelectTrigger>
              <SelectValue placeholder="Select a chart" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="table">Table only</SelectItem>
              <SelectItem value="line">Line</SelectItem>
              <SelectItem value="bar">Bar</SelectItem>
              <SelectItem value="pie">Pie</SelectItem>
            </SelectContent>
          </Select>
          {chartType !== 'table' ? (
            <ChartRenderer result={result} chartType={chartType} />
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Index Suggestions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-slate-700">
            {indexAdvice?.overview ??
              'Ask for index advice after generating or editing a query.'}
          </p>
          {indexAdvice?.suggestions?.map((suggestion) => (
            <IndexSuggestionCard
              key={suggestion.statement}
              suggestion={suggestion}
            />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
