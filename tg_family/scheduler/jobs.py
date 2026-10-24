from datetime import datetime, date, timedelta
from sqlalchemy import select
from database.session import async_session
from database.models import Birthday, Task, Pill
from config import settings
import json
import logging

logger = logging.getLogger(__name__)


async def check_birthdays_monthly():
    """Send birthday reminders on the last day of the month for next month"""
    from aiogram import Bot
    bot = Bot(token=settings.bot_token)
    
    today = date.today()
    # Check if today is the last day of the month
    next_month = today.replace(day=28) + timedelta(days=4)
    last_day_of_month = next_month - timedelta(days=next_month.day)
    
    if today != last_day_of_month:
        await bot.session.close()
        return
    
    # Get birthdays for next month
    next_month = today + timedelta(days=32)
    next_month = next_month.replace(day=1)
    
    async with async_session() as session:
        result = await session.execute(select(Birthday))
        birthdays = result.scalars().all()
    
    next_month_birthdays = []
    for b in birthdays:
        if b.date.month == next_month.month:
            next_month_birthdays.append(b)
    
    if next_month_birthdays:
        admin_ids = settings.get_admin_ids()
        text = f"🎂 Дни рождения в {next_month.strftime('%B')}:\n\n"
        
        for b in next_month_birthdays:
            category_emoji = "👨‍👩‍👧‍👦" if b.category.value == "family" else "👥"
            text += f"{category_emoji} {b.name} - {b.date.strftime('%d.%m')}"
            if b.note:
                text += f" ({b.note})"
            text += "\n"
        
        for admin_id in admin_ids:
            await bot.send_message(admin_id, text)
    
    await bot.session.close()
    logger.info(f"Sent birthday reminders for {next_month.strftime('%B')}")


async def check_task_deadlines():
    """Check for tasks with deadlines and send reminders"""
    from aiogram import Bot
    bot = Bot(token=settings.bot_token)
    
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    async with async_session() as session:
        result = await session.execute(
            select(Task).where(
                Task.is_completed == False,
                Task.deadline.isnot(None)
            )
        )
        tasks = result.scalars().all()
    
    admin_ids = settings.get_admin_ids()
    
    for task in tasks:
        if task.deadline:
            if task.deadline.date() == today.date():
                # Deadline is today
                for admin_id in admin_ids:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ Дедлайн сегодня: {task.text} ({task.deadline.strftime('%H:%M')})"
                    )
            elif task.deadline.date() == tomorrow.date():
                # Deadline is tomorrow
                for admin_id in admin_ids:
                    await bot.send_message(
                        admin_id,
                        f"📌 Дедлайн завтра: {task.text} ({task.deadline.strftime('%d.%m %H:%M')})"
                    )
    
    await bot.session.close()
    logger.info("Checked task deadlines")


async def check_pill_reminders():
    """Check and send pill reminders"""
    from aiogram import Bot
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    bot = Bot(token=settings.bot_token)
    
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_day = now.weekday()  # 0 = Monday, 6 = Sunday
    
    async with async_session() as session:
        result = await session.execute(
            select(Pill).where(
                Pill.reminder_time == current_time
            )
        )
        pills = result.scalars().all()
    
    admin_ids = settings.get_admin_ids()
    
    for pill in pills:
        # Check if today is a scheduled day
        scheduled_days = json.loads(pill.days_of_week)
        if current_day not in scheduled_days:
            continue
        
        # Check if course is still active
        if not pill.is_indefinite and pill.end_date < now.date():
            continue
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="✅ Выпил", callback_data=f"pill_taken_{pill.id}")
        keyboard.button(text="⏰ Отложить на 15 мин", callback_data=f"pill_postpone_{pill.id}")
        keyboard.adjust(2)
        
        for admin_id in admin_ids:
            await bot.send_message(
                admin_id,
                f"💊 Пора принять: {pill.name}",
                reply_markup=keyboard.as_markup()
            )
    
    await bot.session.close()
    logger.info("Checked pill reminders")
