FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN python -m pip install --no-cache-dir .

COPY alembic.ini ./
COPY migrations/ ./migrations/

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8080

CMD ["sh", "-c", "python -m alembic upgrade head && exec python -m uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8080}\""]
