'use client';

import { Button } from '@/components/ui/button';

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-cyan-700">
          Application Error
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-950">
          Something went off script.
        </h1>
        <p className="mt-3 max-w-lg text-sm text-slate-600">{error.message}</p>
      </div>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
