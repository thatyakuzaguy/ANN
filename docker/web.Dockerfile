FROM node:22-alpine AS deps
WORKDIR /workspace
COPY package.json package-lock.json* ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /workspace
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /workspace/node_modules ./node_modules
COPY package.json package-lock.json* ./
COPY apps/web ./apps/web
WORKDIR /workspace/apps/web
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /workspace
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
COPY --from=builder /workspace/apps/web/.next/standalone ./
COPY --from=builder /workspace/apps/web/.next/static ./apps/web/.next/static
RUN addgroup -S ann && adduser -S ann -G ann \
    && chown -R ann:ann /workspace
USER ann
WORKDIR /workspace/apps/web
EXPOSE 3000
CMD ["node", "server.js"]
