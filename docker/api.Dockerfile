FROM docker:29.6.2-cli AS docker-cli

FROM golang:1.26.5-alpine AS compose-builder

RUN apk add --no-cache git
COPY docker/compose-compat /compat/docker
RUN git init /src \
    && cd /src \
    && git remote add origin https://github.com/docker/compose.git \
    && git fetch --depth 1 origin a163be59cf8a81e1d0b9bf72d4ea980f12f577b7 \
    && git checkout --detach FETCH_HEAD \
    && go mod edit -require=golang.org/x/text@v0.39.0 \
    && go mod edit -require=google.golang.org/grpc@v1.82.1 \
    && go mod edit -replace=github.com/docker/docker=/compat/docker \
    && go mod tidy \
    && CGO_ENABLED=0 go build -trimpath \
        -ldflags="-s -w -X github.com/docker/compose/v5/internal.Version=v5.3.1-ann.1" \
        -o /out/docker-compose ./cmd

FROM python:3.12-slim

WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/packages/agents:/workspace/packages/orchestration:/workspace/packages/sandbox:/workspace/packages/git:/workspace/packages/logs:/workspace/packages/shared:/workspace/packages/database:/workspace/packages/security:/workspace/apps/api

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=compose-builder /out/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose

COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY apps/api /workspace/apps/api
COPY agentic_network /workspace/agentic_network
COPY packages /workspace/packages
COPY config /workspace/config
COPY scripts /workspace/scripts
COPY pyproject.toml README.md LICENSE /workspace/

RUN groupadd --gid 10001 ann \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin ann \
    && mkdir -p /workspace/data /workspace/generated-projects /workspace/logs /workspace/outputs \
    && chown -R ann:ann /workspace/data /workspace/generated-projects /workspace/logs /workspace/outputs

EXPOSE 8000
USER ann
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
