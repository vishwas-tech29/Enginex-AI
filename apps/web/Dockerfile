# Build context is the monorepo root (see docker-compose.yml / cd-deploy.yml)
# so pnpm can resolve the workspace lockfile and any packages/* dependencies.
FROM node:20-alpine AS deps
WORKDIR /repo
RUN corepack enable && corepack prepare pnpm@9.0.0 --activate
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* ./
COPY apps/web/package.json apps/web/package.json
COPY packages packages
RUN pnpm install --frozen-lockfile --filter web...

FROM node:20-alpine AS builder
WORKDIR /repo
RUN corepack enable && corepack prepare pnpm@9.0.0 --activate
COPY --from=deps /repo/node_modules ./node_modules
COPY --from=deps /repo/apps/web/node_modules ./apps/web/node_modules
COPY package.json pnpm-workspace.yaml turbo.json ./
COPY packages packages
COPY apps/web apps/web
RUN pnpm --filter web run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /repo/apps/web/next.config.js ./
COPY --from=builder /repo/apps/web/public ./public
COPY --from=builder /repo/apps/web/.next ./.next
COPY --from=builder /repo/apps/web/node_modules ./node_modules
COPY --from=builder /repo/apps/web/package.json ./package.json

EXPOSE 3000

CMD ["node_modules/.bin/next", "start"]
