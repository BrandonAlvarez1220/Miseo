"use client";

import { Check, Copy, KeyRound, Loader2, Plug } from "lucide-react";
import { useActionState, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import type { Agent } from "@/types/api";

import { createAgentAction, revokeAgentAction, type CreateAgentState } from "./actions";

const PROVIDERS = [
  { value: "opencode", label: "opencode" },
  { value: "claude", label: "Claude" },
  { value: "gemini", label: "Gemini" },
  { value: "other", label: "Otro" },
];

const field =
  "h-11 w-full rounded-md border border-line bg-surface px-3 text-sm focus:border-primary focus:outline-none";

export function AgentManager({ agents }: { agents: Agent[] }) {
  const [state, formAction, pending] = useActionState<CreateAgentState, FormData>(
    createAgentAction,
    { status: "idle" },
  );
  const [copied, setCopied] = useState(false);
  const [revoking, startRevoke] = useTransition();
  const [revokeError, setRevokeError] = useState<string | null>(null);

  async function copy(token: string) {
    try {
      await navigator.clipboard.writeText(token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Copy failed", error);
    }
  }

  return (
    <div className="space-y-8">
      <section aria-labelledby="connect" className="rounded-lg border border-line bg-surface p-5">
        <h2 id="connect" className="flex items-center gap-2 text-lg font-bold">
          <Plug aria-hidden="true" className="size-5 text-primary" /> Conectar un agente
        </h2>
        <p className="mt-1 text-sm text-ink-muted">
          Crea una identidad por herramienta (opencode, Claude, Gemini…). Así sabes de cuál viene
          cada receta y puedes revocar una sin tocar las demás.
        </p>
        <form
          action={formAction}
          className="mt-4 grid gap-3 sm:grid-cols-[1fr_12rem_auto] sm:items-end"
        >
          <label className="text-sm font-semibold">
            Nombre
            <input
              name="name"
              required
              minLength={2}
              maxLength={60}
              placeholder="Claude recetas MX"
              className={`${field} mt-1 font-normal`}
            />
          </label>
          <label className="text-sm font-semibold">
            Herramienta
            <select name="provider" className={`${field} mt-1 font-normal`} defaultValue="claude">
              {PROVIDERS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <Button type="submit" size="lg" disabled={pending}>
            {pending ? (
              <Loader2 aria-hidden="true" className="animate-spin" />
            ) : (
              <KeyRound aria-hidden="true" />
            )}
            Crear y obtener token
          </Button>
        </form>

        {state.status === "error" ? (
          <p role="alert" className="mt-3 rounded-md bg-danger-soft px-4 py-3 text-sm text-danger">
            {state.error}
          </p>
        ) : null}

        {state.status === "created" ? (
          <div
            role="status"
            className="mt-4 space-y-3 rounded-md border-2 border-notice bg-notice-soft p-4"
          >
            <p className="text-sm font-semibold">
              Token de «{state.name}». Cópialo ahora: <u>no se vuelve a mostrar</u>.
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <code className="min-w-0 flex-1 rounded bg-surface px-3 py-2 text-xs break-all select-all">
                {state.token}
              </code>
              <Button variant="secondary" size="sm" onClick={() => copy(state.token)}>
                {copied ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}
                {copied ? "Copiado" : "Copiar"}
              </Button>
            </div>
            <p className="text-xs text-ink-muted">
              Guárdalo como variable de entorno del agente (<code>MISEO_AGENT_TOKEN</code>), nunca
              en el repositorio. Las instrucciones para pegarle están en{" "}
              <code>docs/AGENT_GUIDE.md</code>.
            </p>
          </div>
        ) : null}
      </section>

      <section aria-labelledby="agents-list">
        <h2 id="agents-list" className="mb-3 text-lg font-bold">
          Agentes conectados
        </h2>
        {revokeError ? (
          <p role="alert" className="mb-3 rounded-md bg-danger-soft px-4 py-3 text-sm text-danger">
            {revokeError}
          </p>
        ) : null}
        {agents.length === 0 ? (
          <p className="rounded-md bg-surface-muted px-4 py-6 text-sm text-ink-muted">
            Todavía no hay agentes. Conecta el primero arriba.
          </p>
        ) : (
          <ul className="space-y-3">
            {agents.map((agent) => (
              <li
                key={agent.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-surface p-4"
              >
                <span className="min-w-0">
                  <span className="block font-bold">
                    {agent.name}{" "}
                    <span className="text-xs font-medium text-ink-muted">({agent.provider})</span>
                  </span>
                  <span className="mt-1 block text-xs text-ink-muted">
                    <code>{agent.token_prefix}…</code> · creado{" "}
                    {new Date(agent.created_at).toLocaleDateString("es", { dateStyle: "medium" })} ·{" "}
                    {agent.last_used_at
                      ? `último uso ${new Date(agent.last_used_at).toLocaleString("es", { dateStyle: "medium", timeStyle: "short" })}`
                      : "sin usar todavía"}
                  </span>
                </span>
                {agent.is_active ? (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={revoking}
                    onClick={() => {
                      if (
                        !window.confirm(
                          `¿Revocar «${agent.name}»? Dejará de funcionar de inmediato.`,
                        )
                      )
                        return;
                      setRevokeError(null);
                      startRevoke(async () => {
                        const result = await revokeAgentAction(agent.id);
                        if (!result.ok) setRevokeError(result.error ?? "No se pudo revocar.");
                        else window.location.reload();
                      });
                    }}
                  >
                    Revocar
                  </Button>
                ) : (
                  <span className="rounded-full bg-surface-muted px-3 py-1 text-xs font-semibold text-ink-muted">
                    Revocado
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
