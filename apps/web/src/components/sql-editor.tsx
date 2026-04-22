'use client';

import Editor from '@monaco-editor/react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function SqlEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>SQL Editor</CardTitle>
      </CardHeader>
      <CardContent className="h-[320px]">
        <Editor
          theme="vs-light"
          height="100%"
          language="sql"
          value={value}
          onChange={(nextValue) => onChange(nextValue ?? '')}
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            wordWrap: 'on',
            scrollBeyondLastLine: false,
          }}
        />
      </CardContent>
    </Card>
  );
}
