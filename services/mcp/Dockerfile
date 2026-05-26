# syntax=docker/dockerfile:1

FROM node:20-alpine AS build

ARG MCP_SERVICE
WORKDIR /workspace

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY services/mcp ./services/mcp

RUN test -n "$MCP_SERVICE"
RUN corepack pnpm install --filter "./services/mcp/${MCP_SERVICE}" --frozen-lockfile=false
RUN corepack pnpm --filter "./services/mcp/${MCP_SERVICE}" build

FROM node:20-alpine AS runtime

ARG MCP_SERVICE
ENV MCP_SERVICE=${MCP_SERVICE}
ENV NODE_ENV=production
WORKDIR /workspace

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY --from=build /workspace/services/mcp ./services/mcp
COPY --from=build /workspace/node_modules ./node_modules

CMD ["sh", "-c", "node services/mcp/${MCP_SERVICE}/build/${MCP_ENTRYPOINT:-index.js}"]
