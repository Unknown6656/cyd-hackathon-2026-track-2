FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY . .
RUN uv pip install --system ./app

CMD ["python", "-m", "app.main"]
