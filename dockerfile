FROM ghcr.io/astral-sh/uv:debian-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_NO_SYNC=1

# Install dependencies
COPY uv.lock pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy source code (no src folder, files are in root)
COPY *.py ./

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT []
CMD ["uv", "run", "python", "ingest.py", "--listen"]