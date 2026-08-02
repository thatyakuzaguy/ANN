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

FROM nvidia/cuda:12.6.3-devel-ubuntu24.04 AS model-runtime-builder

WORKDIR /workspace
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CUDA_STUBS_PATH=/usr/local/cuda/lib64/stubs
ENV LIBRARY_PATH=/usr/local/cuda/lib64/stubs
ENV CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=86 -DCMAKE_LIBRARY_PATH=/usr/local/cuda/lib64/stubs -DCMAKE_EXE_LINKER_FLAGS=-Wl,-rpath-link,/usr/local/cuda/lib64/stubs"
ENV FORCE_CMAKE=1
ENV CMAKE_BUILD_PARALLEL_LEVEL=4

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        ninja-build \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=compose-builder /out/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose

RUN ln -sf ${CUDA_STUBS_PATH}/libcuda.so ${CUDA_STUBS_PATH}/libcuda.so.1

COPY apps/api/requirements.txt /tmp/requirements.txt
COPY apps/api/requirements-models.txt /tmp/requirements-models.txt
COPY apps/api/requirements-llama-cpp.txt /tmp/requirements-llama-cpp.txt
RUN python3 -m pip install --break-system-packages --no-cache-dir -r /tmp/requirements-models.txt \
    && python3 -m pip install --break-system-packages --no-cache-dir --no-deps \
        -r /tmp/requirements-llama-cpp.txt \
    && python3 -c "import importlib.metadata as m; assert all((d.metadata.get('Name') or '').lower() != 'diskcache' for d in m.distributions())"

FROM nvidia/cuda:12.6.3-runtime-ubuntu24.04 AS api-runtime

WORKDIR /workspace
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/packages/agents:/workspace/packages/orchestration:/workspace/packages/sandbox:/workspace/packages/git:/workspace/packages/logs:/workspace/packages/shared:/workspace/packages/database:/workspace/packages/security:/workspace/apps/api

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        libgomp1 \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=compose-builder /out/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose
COPY --from=model-runtime-builder /usr/local/bin/ /usr/local/bin/
COPY --from=model-runtime-builder /usr/local/lib/python3.12/dist-packages/ /usr/local/lib/python3.12/dist-packages/

RUN python3 -c "import importlib.metadata as m; assert m.version('llama-cpp-python') == '0.3.32'; assert all((d.metadata.get('Name') or '').lower() != 'diskcache' for d in m.distributions())"

COPY . /workspace

RUN groupadd --gid 10001 ann \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin ann \
    && mkdir -p /workspace/data /workspace/generated-projects /workspace/logs /workspace/outputs \
    && chown -R ann:ann /workspace/data /workspace/generated-projects /workspace/logs /workspace/outputs

EXPOSE 8000
USER ann
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
