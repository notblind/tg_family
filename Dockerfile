FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./
COPY tg_family ./tg_family
COPY alembic.ini ./

# Install dependencies
RUN uv sync --frozen

# Create data directory for database
RUN mkdir -p data

# Run migrations
RUN uv run alembic upgrade head

# Run the bot
CMD ["uv", "run", "python", "-m", "tg_family.bot.bot"]
