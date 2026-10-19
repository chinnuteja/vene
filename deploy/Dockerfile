FROM node:24.19.0-bookworm-slim AS node
FROM python:3.12.14-slim-bookworm
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && apt-get update && apt-get install -y --no-install-recommends postgresql-15 ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g pnpm@11.25.0
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile
COPY services/backend services/backend
RUN pip install --no-cache-dir -e ./services/backend
COPY apps/web apps/web
COPY packages packages
COPY fixtures fixtures
COPY deploy deploy
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build
EXPOSE 10000
CMD ["python", "deploy/hosted.py"]
