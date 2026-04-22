import { WorkspaceClient } from '@/components/workspace-client';

export default async function WorkspacePage({
  params,
}: {
  params: Promise<{ connectionId: string }>;
}) {
  const { connectionId } = await params;
  return <WorkspaceClient connectionId={connectionId} />;
}
