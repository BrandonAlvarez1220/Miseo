import type { Metadata } from "next";
import { connection } from "next/server";
import { Suspense } from "react";

import { apiErrorState } from "@/components/ui/api-error-state";
import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { listAgents } from "@/features/agents/api";
import { AgentManager } from "@/features/agents/agent-manager";
import { Forbidden } from "@/features/auth/forbidden";
import { requireRole } from "@/features/auth/guard";
import { attempt } from "@/lib/attempt";

export const metadata: Metadata = { title: "Agentes" };

export default function AgentsPage() {
  return (
    <>
      <PageHeader
        lead="Conectar"
        title="agentes de ingesta"
        description="Los agentes buscan y reescriben recetas y las envían a revisión. Cada uno tiene su propio token y nunca publica por sí solo."
      />
      <Container>
        <Suspense fallback={<Skeleton className="h-64 w-full rounded-lg" />}>
          <Content />
        </Suspense>
      </Container>
    </>
  );
}

async function Content() {
  await connection();
  const session = await requireRole("admin", "/admin/agentes");
  if (!session) return <Forbidden needs="administradores" />;
  const result = await attempt(listAgents(session.token));
  if (!result.ok) return apiErrorState(result.error, "/admin/agentes", "los agentes");
  return <AgentManager agents={result.data} />;
}
