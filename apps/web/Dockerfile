FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json tsconfig.base.json /app/
COPY apps/web/package.json /app/apps/web/package.json
COPY packages/shared/package.json /app/packages/shared/package.json

RUN npm ci

FROM node:20-alpine AS builder

WORKDIR /app

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

COPY --from=deps /app/node_modules /app/node_modules
COPY package.json package-lock.json tsconfig.base.json /app/
COPY packages/shared /app/packages/shared
COPY apps/web /app/apps/web

WORKDIR /app/apps/web

RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

COPY --from=builder /app/apps/web/.next/standalone /app/
COPY --from=builder /app/apps/web/.next/static /app/apps/web/.next/static

EXPOSE 3000

CMD ["node", "apps/web/server.js"]
