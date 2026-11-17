FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# BEGIN QUORQ SYSTEM PACKAGES
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpango-1.0-0 \
    && rm -rf /var/lib/apt/lists/*
# END QUORQ SYSTEM PACKAGES

COPY requirements.txt ./
# --only-binary :all: installs from wheels only, so no dependency's setup.py
# runs at build time. Every pinned requirement publishes a wheel for this base.
RUN pip install --no-cache-dir --only-binary :all: -r requirements.txt

COPY app ./app
# The schema is only ever changed through a migration (the architecture's rule),
# so the migrations and their config have to be in the image: without them
# `alembic upgrade head` cannot be run against the deployed database, and the
# worker container -- which runs this same image -- could not be brought up
# against a fresh one either.
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

# Run as an unprivileged user. The service never needs root, and a container that
# drops it limits what a compromise of the app can do to the host.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Reports the container unhealthy when the app stops answering. Uses the Python
# standard library rather than curl, which the slim base image does not ship.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
