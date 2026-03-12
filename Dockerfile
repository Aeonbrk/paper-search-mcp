FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG UV_VERSION=0.10.9
RUN python -m pip install --no-cache-dir "uv==${UV_VERSION}" \
    && uv --version

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

COPY . .

ENV PATH="/app/.venv/bin:${PATH}"

CMD ["python", "-m", "paper_search_mcp.server"]
