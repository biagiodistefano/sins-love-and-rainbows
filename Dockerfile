FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry globally
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Create app user
RUN adduser --disabled-password appuser

WORKDIR /app

COPY poetry.lock pyproject.toml README.md version ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --only main

# Switch user *after* installing dependencies
USER appuser

COPY --chown=appuser:appuser src/ ./src/
WORKDIR /app/src

ENV DOCKER_BUILD=1

RUN python manage.py collectstatic --noinput

COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]