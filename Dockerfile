FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./
COPY . .

# Install dependencies
RUN uv sync --frozen

# Run the bot
CMD ["uv", "run", "python", "bot/bot.py"]
