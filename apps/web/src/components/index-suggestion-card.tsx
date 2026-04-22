'use client';

import type { IndexSuggestion } from '@ai-sql-copilot/shared';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';

export function IndexSuggestionCard({
  suggestion,
}: {
  suggestion: IndexSuggestion;
}) {
  return (
    <Card className="border-slate-200 shadow-none">
      <CardContent className="space-y-3 p-4">
        <div className="flex items-center justify-between gap-3">
          <h4 className="text-sm font-semibold text-slate-900">
            {suggestion.summary}
          </h4>
          <Badge>{suggestion.confidence}</Badge>
        </div>
        <p className="text-sm text-slate-600">{suggestion.rationale}</p>
        <pre className="overflow-x-auto rounded-xl bg-slate-950 p-3 text-xs text-cyan-100">
          <code>{suggestion.statement}</code>
        </pre>
        <div className="space-y-1 text-xs text-slate-500">
          {suggestion.tradeoffs.map((tradeoff) => (
            <p key={tradeoff}>• {tradeoff}</p>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
