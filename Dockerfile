# ---- build stage: resolve dependencies into a self-contained virtualenv ----
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install dependencies in their own layer so it is cached independently of app code.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project


# ---- runtime stage ----
FROM python:3.13-slim-bookworm

RUN useradd --create-home --uid 10001 app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app app.py gunicorn_config.py ./
COPY --chown=app:app Subscriptions ./Subscriptions
COPY --chown=app:app bankofmaldives ./bankofmaldives

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER app

# Railway overrides this with $PORT at runtime; 8080 is the local default.
EXPOSE 8080

CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
