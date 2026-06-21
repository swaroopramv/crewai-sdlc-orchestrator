# syntax=docker/dockerfile:1

# ---- Builder stage ----
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

# Install dependencies first (better layer caching)
COPY pyproject.toml README.md ./
COPY poetry.lock* ./
RUN poetry install --no-root --only main

# ---- Runtime stage ----
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/app"

# Create a non-root user
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# Copy the prepared virtualenv and application code
COPY --from=builder /app/.venv /app/.venv
COPY app ./app

USER appuser

ENTRYPOINT ["python", "/app/app/main.py"]
CMD ["--help"]
