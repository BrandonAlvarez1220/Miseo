# syntax=docker/dockerfile:1
# Build context: repository root (pnpm workspace). See docker-compose.yml.
FROM node:22-alpine AS base
RUN corepack enable
WORKDIR /repo

FROM base AS deps
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/
RUN pnpm install --frozen-lockfile --filter web

FROM deps AS build
COPY apps/web apps/web
ENV NEXT_TELEMETRY_DISABLED=1 NEXT_OUTPUT=standalone
RUN pnpm --filter web build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN addgroup -S miseo && adduser -S miseo -G miseo
COPY --from=build --chown=miseo:miseo /repo/apps/web/.next/standalone ./
COPY --from=build --chown=miseo:miseo /repo/apps/web/.next/static ./apps/web/.next/static
# Add "COPY .../apps/web/public" here once the app ships public assets (PWA icons, Phase 5).
USER miseo
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
