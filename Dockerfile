FROM python:3.12

RUN pip install --no-cache-dir uv

WORKDIR /app/app
COPY app /app/app
RUN uv sync --frozen

ENV PYTHONPATH=/app/app/src

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
