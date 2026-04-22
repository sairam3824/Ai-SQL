'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Database, FileUp, Loader2, PlugZap } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { api, ConnectionFormPayload } from '@/lib/api';
import { cn, getErrorMessage } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';

const connectionSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  type: z.enum(['postgresql', 'sqlite', 'duckdb']),
  host: z.string().optional(),
  port: z.number().int().min(1).max(65535).optional(),
  database: z.string().optional(),
  username: z.string().optional(),
  password: z.string().optional(),
  ssl: z.boolean().optional(),
  file: z.any().optional(),
  createDuckdb: z.boolean().optional(),
});

type FormValues = ConnectionFormPayload;

export function ConnectionForm() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const { register, handleSubmit, watch, setValue, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(connectionSchema),
    defaultValues: {
      name: '',
      type: 'postgresql',
      port: 5432,
      ssl: true,
      createDuckdb: false,
    },
  });

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
    if (!nextOpen) {
      setTestMessage(null);
      reset();
    }
  };

  const connectionType = watch('type');

  const testMutation = useMutation<
    {
      ok: boolean;
      message: string;
      inferred_name?: string | null;
      config_summary: Record<string, unknown>;
    },
    Error,
    ConnectionFormPayload
  >({
    mutationFn: api.testConnection,
    onSuccess: (result) => setTestMessage(result.message),
    onError: (error) => setTestMessage(error.message),
  });

  const createMutation = useMutation<
    Awaited<ReturnType<typeof api.createConnection>>,
    Error,
    ConnectionFormPayload
  >({
    mutationFn: api.createConnection,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['connections'] });
      setOpen(false);
      setTestMessage(null);
      reset();
    },
  });

  const submit = handleSubmit(async (values) => {
    await createMutation.mutateAsync(values);
  });

  const testConnection = handleSubmit(async (values) => {
    await testMutation.mutateAsync(values);
  });

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <PlugZap className="h-4 w-4" />
          New Connection
        </Button>
      </DialogTrigger>
      <DialogContent>
        <div className="space-y-6">
          <div>
            <DialogTitle className="text-xl font-semibold text-slate-950">
              Add a database connection
            </DialogTitle>
            <DialogDescription className="mt-2 text-sm text-slate-500">
              PostgreSQL credentials stay server-side. SQLite and DuckDB files are
              stored in backend-managed storage.
            </DialogDescription>
          </div>

          <form className="space-y-4" onSubmit={submit}>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2 text-sm text-slate-700">
                <span>Name</span>
                <Input placeholder="Revenue warehouse" {...register('name')} />
                {errors.name && <p className="text-xs text-red-600">{errors.name.message}</p>}
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span>Type</span>
                <select
                  className="flex h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
                  {...register('type')}
                >
                  <option value="postgresql">PostgreSQL</option>
                  <option value="sqlite">SQLite</option>
                  <option value="duckdb">DuckDB</option>
                </select>
              </label>
            </div>

            {connectionType === 'postgresql' ? (
              <div className="grid gap-4 md:grid-cols-2">
                <label className="space-y-2 text-sm text-slate-700">
                  <span>Host</span>
                  <Input placeholder="localhost" {...register('host')} />
                </label>
                <label className="space-y-2 text-sm text-slate-700">
                  <span>Port</span>
                  <Input
                    type="number"
                    placeholder="5432"
                    {...register('port', { valueAsNumber: true })}
                  />
                </label>
                <label className="space-y-2 text-sm text-slate-700">
                  <span>Database</span>
                  <Input placeholder="analytics" {...register('database')} />
                </label>
                <label className="space-y-2 text-sm text-slate-700">
                  <span>User</span>
                  <Input placeholder="postgres" {...register('username')} />
                </label>
                <label className="space-y-2 text-sm text-slate-700 md:col-span-2">
                  <span>Password</span>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    {...register('password')}
                  />
                </label>
                <label className="inline-flex items-center gap-3 text-sm text-slate-700">
                  <input type="checkbox" {...register('ssl')} />
                  Require SSL
                </label>
              </div>
            ) : (
              <div className="space-y-4 rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4">
                <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
                  <FileUp className="h-4 w-4 text-cyan-700" />
                  <span>Upload {connectionType === 'sqlite' ? '.db/.sqlite' : '.duckdb'} file</span>
                  <input
                    className="hidden"
                    type="file"
                    accept={connectionType === 'sqlite' ? '.db,.sqlite' : '.duckdb'}
                    onChange={(event) =>
                      setValue('file', event.target.files?.[0] ?? null)
                    }
                  />
                </label>
                {connectionType === 'duckdb' ? (
                  <label className="inline-flex items-center gap-3 text-sm text-slate-700">
                    <input type="checkbox" {...register('createDuckdb')} />
                    Create an empty local DuckDB file if no upload is provided
                  </label>
                ) : null}
              </div>
            )}

            {testMessage ? (
              <div
                className={cn(
                  'rounded-xl px-4 py-3 text-sm',
                  testMutation.isError
                    ? 'bg-red-50 text-red-700'
                    : 'bg-emerald-50 text-emerald-700',
                )}
              >
                {testMessage}
              </div>
            ) : null}

            {createMutation.isError ? (
              <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
                {getErrorMessage(createMutation.error)}
              </div>
            ) : null}

            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Database className="h-4 w-4" />
                Test the connection before saving to pre-cache schema metadata.
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void testConnection()}
                  disabled={testMutation.isPending || createMutation.isPending}
                >
                  {testMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : null}
                  Test Connection
                </Button>
                <Button
                  type="submit"
                  disabled={testMutation.isPending || createMutation.isPending}
                >
                  {createMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : null}
                  Save Connection
                </Button>
              </div>
            </div>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
