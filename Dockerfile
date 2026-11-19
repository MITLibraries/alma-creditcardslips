FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY ccslips ./ccslips
COPY config ./config

RUN uv export --locked --no-dev --no-emit-project \
        --format requirements.txt --output-file /tmp/requirements.txt && \
    uv pip install --system --no-deps -r /tmp/requirements.txt && \
    uv pip install --system --no-deps .

ENTRYPOINT ["ccslips"]
CMD []
