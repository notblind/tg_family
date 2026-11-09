import asyncio
import logging
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings
from middlewares.whitelist import WhitelistMiddleware
from scheduler.scheduler import scheduler
from handlers import base, birthdays, tasks, pills, settings as settings_handler


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Setup whitelist middleware
    dp.message.middleware(WhitelistMiddleware())
    dp.callback_query.middleware(WhitelistMiddleware())

    # Start scheduler
    from scheduler.scheduler import init_scheduler
    await init_scheduler()

    # Register handlers
    dp.include_router(base.router)
    dp.include_router(birthdays.router)
    dp.include_router(tasks.router)
    dp.include_router(pills.router)
    dp.include_router(settings_handler.router)

    logger.info("Bot started")
    try:
        await dp.start_polling(bot)
    finally:
        from scheduler.scheduler import shutdown_scheduler
        shutdown_scheduler()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
