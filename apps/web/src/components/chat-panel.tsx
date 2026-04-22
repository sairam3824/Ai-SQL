'use client';

import type { ChatMessage } from '@ai-sql-copilot/shared';
import { Loader2, SendHorizontal } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { formatTimestamp } from '@/lib/utils';

export function ChatPanel({
  messages,
  prompt,
  setPrompt,
  onSubmit,
  isLoading,
}: {
  messages: ChatMessage[];
  prompt: string;
  setPrompt: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Schema-Aware Chat</CardTitle>
      </CardHeader>
      <CardContent className="grid h-[420px] grid-rows-[1fr_auto] gap-4">
        <ScrollArea className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div className="space-y-4">
            {messages.length ? (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm ${
                    message.role === 'user'
                      ? 'ml-auto bg-slate-950 text-white'
                      : 'bg-white text-slate-700'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.generatedSql ? (
                    <pre className="mt-3 overflow-x-auto rounded-xl bg-slate-100 p-3 text-xs text-slate-700">
                      <code>{message.generatedSql}</code>
                    </pre>
                  ) : null}
                  <p className="mt-2 text-[11px] opacity-70">
                    {formatTimestamp(message.createdAt)}
                  </p>
                </div>
              ))
            ) : (
              <div className="flex h-full items-center justify-center text-center text-sm text-slate-500">
                Ask a business question and the copilot will generate SQL with
                assumptions, warnings, and a chart suggestion.
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="space-y-3">
          <Textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Top 10 customers by revenue last quarter"
          />
          <div className="flex justify-end">
            <Button onClick={onSubmit} disabled={isLoading || !prompt.trim()}>
              {isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <SendHorizontal className="mr-2 h-4 w-4" />
              )}
              Generate SQL
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
