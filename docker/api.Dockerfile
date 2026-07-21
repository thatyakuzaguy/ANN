FROM docker:29.5.2-cli AS docker-cli

FROM python:3.12-slim

WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/packages/agents:/workspace/packages/orchestration:/workspace/packages/sandbox:/workspace/packages/git:/workspace/packages/logs:/workspace/packages/shared:/workspace/packages/database:/workspace/packages/security:/workspace/apps/api

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker-cli /usr/local/libexec/docker/cli-plugins/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose

COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY apps/api /workspace/apps/api
COPY agentic_network /workspace/agentic_network
COPY packages /workspace/packages
COPY config /workspace/config
COPY scripts /workspace/scripts
COPY pyproject.toml README.md LICENSE /workspace/

RUN mkdir -p /workspace/generated-projects /workspace/logs /workspace/outputs

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
