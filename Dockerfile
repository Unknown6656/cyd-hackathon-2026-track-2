FROM python:3.12

RUN pip install --no-cache-dir uv

WORKDIR /app/app

ENV UV_LINK_MODE=copy

COPY app/pyproject.toml app/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

COPY app /app/app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

ENV PYTHONPATH=/app/app/src

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
