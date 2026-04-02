# ─────────────────────────────────────────────────────────────────────────────
# Subsystem V: Perpetual Deployment — The Eternal
# Containerised ARC-AGI-3 Pentarchy Solver
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN useradd -m arcuser
WORKDIR /app

# Install Python dependencies before copying source (layer cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY pyproject.toml ./
COPY src/ ./src/
COPY data/ ./data/

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

USER arcuser

# Default: run the solver CLI
ENTRYPOINT ["python", "-m", "arc_solver"]
CMD ["--help"]
