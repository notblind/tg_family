from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from database.session import get_session
from database.models import NotificationSettings
from config import settings
from handlers.birthdays import BirthdayStates
from handlers.tasks import TaskStates
from handlers.pills import PillStates

router = Router()


@router.message(F.text == "/menu")
async def cmd_menu(message: types.Message):
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text="📅 Дни рождения")
    keyboard.button(text="📋 Дела")
    keyboard.button(text="💊 Таблетки")
    keyboard.button(text="⚙️ Настройки")
    keyboard.button(text="❓ FAQ")
    keyboard.adjust(2)
    
    await message.answer(
        "🏠 Главное меню",
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )


@router.message(F.text == "⚙️ Настройки")
async def cmd_settings(message: types.Message):
    user_id = message.from_user.id
    
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(NotificationSettings).where(NotificationSettings.user_id == user_id)
        )
        user_settings = result.scalar_one_or_none()
        
        if not user_settings:
            user_settings = NotificationSettings(user_id=user_id)
            session.add(user_settings)
            await session.commit()
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔔 Уведомления", callback_data="settings_notifications")
    keyboard.button(text="◀️ Назад", callback_data="menu_back")
    keyboard.adjust(1)
    
    text = "⚙️ Настройки\n\n"
    text += f"🎂 Дни рождения: {'✅' if user_settings.birthdays_notification else '❌'}\n"
    text += f"📋 Дела: {'✅' if user_settings.tasks_notification else '❌'}\n"
    text += f"💊 Таблетки: {'✅' if user_settings.pills_notification else '❌'}\n"
    
    await message.answer(text, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "settings_notifications")
async def callback_settings_notifications(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(NotificationSettings).where(NotificationSettings.user_id == user_id)
        )
        user_settings = result.scalar_one_or_none()
        
        if not user_settings:
            user_settings = NotificationSettings(user_id=user_id)
            session.add(user_settings)
            await session.commit()
            await session.refresh(user_settings)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=f"🎂 Дни рождения: {'🔔' if user_settings.birthdays_notification else '🔕'}",
        callback_data="toggle_birthdays"
    )
    keyboard.button(
        text=f"📋 Дела: {'🔔' if user_settings.tasks_notification else '🔕'}",
        callback_data="toggle_tasks"
    )
    keyboard.button(
        text=f"💊 Таблетки: {'🔔' if user_settings.pills_notification else '🔕'}",
        callback_data="toggle_pills"
    )
    keyboard.button(text="◀️ Назад", callback_data="settings_back")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "🔔 Настройки уведомлений\n\nНажмите для переключения:",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "toggle_birthdays")
async def callback_toggle_birthdays(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(NotificationSettings).where(NotificationSettings.user_id == user_id)
        )
        user_settings = result.scalar_one_or_none()
        
        if user_settings:
            user_settings.birthdays_notification = not user_settings.birthdays_notification
            await session.commit()
    
    await callback.answer("Настройка обновлена")
    await callback_settings_notifications(callback)


@router.callback_query(F.data == "toggle_tasks")
async def callback_toggle_tasks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(NotificationSettings).where(NotificationSettings.user_id == user_id)
        )
        user_settings = result.scalar_one_or_none()
        
        if user_settings:
            user_settings.tasks_notification = not user_settings.tasks_notification
            await session.commit()
    
    await callback.answer("Настройка обновлена")
    await callback_settings_notifications(callback)


@router.callback_query(F.data == "toggle_pills")
async def callback_toggle_pills(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(NotificationSettings).where(NotificationSettings.user_id == user_id)
        )
        user_settings = result.scalar_one_or_none()
        
        if user_settings:
            user_settings.pills_notification = not user_settings.pills_notification
            await session.commit()
    
    await callback.answer("Настройка обновлена")
    await callback_settings_notifications(callback)


@router.callback_query(F.data == "settings_back")
async def callback_settings_back(callback: types.CallbackQuery):
    await cmd_settings(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menu_back")
async def callback_menu_back(callback: types.CallbackQuery):
    await cmd_menu(callback.message)
    await callback.answer()


@router.message(F.text == "📅 Дни рождения")
async def cmd_birthdays_menu(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Добавить день рождения", callback_data="menu_add_birthday")
    keyboard.button(text="📋 Все дни рождения", callback_data="menu_birthdays")
    keyboard.button(text="📅 Ближайшие дни рождения", callback_data="menu_upcoming_birthdays")
    keyboard.adjust(1)
    
    await message.answer(
        "📅 Дни рождения",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data == "menu_add_birthday")
async def callback_menu_add_birthday(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data="cancel_add_birthday")
    keyboard.adjust(1)

    await callback.message.answer(
        "Введите день рождения в формате:\n"
        "Имя - ДД.ММ\n\n"
        "Пример: Иван - 15.05",
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(BirthdayStates.add_birthday)
    await callback.answer()


@router.message(BirthdayStates.add_birthday)
async def process_add_birthday_from_menu(message: types.Message, state: FSMContext):
    from handlers.birthdays import process_add_birthday
    await process_add_birthday(message, state)


@router.callback_query(F.data == "menu_birthdays")
async def callback_menu_birthdays(callback: types.CallbackQuery):
    from handlers.birthdays import cmd_birthdays
    await cmd_birthdays(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menu_upcoming_birthdays")
async def callback_menu_upcoming_birthdays(callback: types.CallbackQuery):
    from handlers.birthdays import cmd_upcoming_birthdays
    await cmd_upcoming_birthdays(callback.message)
    await callback.answer()


@router.message(F.text == "📋 Дела")
async def cmd_tasks_menu(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Добавить дело", callback_data="menu_add_task")
    keyboard.button(text="📋 Список дел", callback_data="menu_tasks")
    keyboard.button(text="📋 Все дела", callback_data="menu_tasks_all")
    keyboard.adjust(1)
    
    await message.answer(
        "📋 Дела",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data == "menu_add_task")
async def callback_menu_add_task(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data="cancel_add_task")
    keyboard.adjust(1)

    await callback.message.answer(
        "Введите задачу в формате:\n"
        "Текст задачи - ДД.ММ ЧЧ:ММ\n\n"
        "Пример: Купить продукты - 25.10 18:00\n\n"
        "Если дедлайна нет, просто введите текст задачи.",
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(TaskStates.add_task)
    await callback.answer()


@router.message(TaskStates.add_task)
async def process_add_task_from_menu(message: types.Message, state: FSMContext):
    from handlers.tasks import process_add_task
    await process_add_task(message, state)


@router.callback_query(F.data == "menu_tasks")
async def callback_menu_tasks(callback: types.CallbackQuery):
    from handlers.tasks import cmd_tasks
    await cmd_tasks(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menu_tasks_all")
async def callback_menu_tasks_all(callback: types.CallbackQuery):
    from handlers.tasks import cmd_tasks_all
    await cmd_tasks_all(callback.message)
    await callback.answer()


@router.message(F.text == "💊 Таблетки")
async def cmd_pills_menu(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Добавить напоминание", callback_data="menu_add_pill")
    keyboard.button(text="💊 Список напоминаний", callback_data="menu_pills")
    keyboard.button(text="📋 Журнал приёмов", callback_data="menu_pill_log")
    keyboard.adjust(1)
    
    await message.answer(
        "💊 Таблетки",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data == "menu_add_pill")
async def callback_menu_add_pill(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data="cancel_add_pill")
    keyboard.adjust(1)

    await callback.message.answer(
        "Введите напоминание в формате:\n"
        "Название - ЧЧ:ММ\n"
        "или\n"
        "Название - ЧЧ:ММ - Дни недели\n\n"
        "Примеры:\n"
        "Витамин C - 09:00 (ежедневно)\n"
        "Витамин C - 09:00 - Пн Вт Ср Чт Пт (рабочие дни)\n\n"
        "Дни недели: Пн Вт Ср Чт Пт Сб Вс (через пробел)",
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(PillStates.add_pill)
    await callback.answer()


@router.message(PillStates.add_pill)
async def process_add_pill_from_menu(message: types.Message, state: FSMContext):
    from handlers.pills import process_add_pill
    await process_add_pill(message, state)


@router.callback_query(F.data == "menu_pills")
async def callback_menu_pills(callback: types.CallbackQuery):
    from handlers.pills import cmd_pills
    await cmd_pills(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menu_pill_log")
async def callback_menu_pill_log(callback: types.CallbackQuery):
    from handlers.pills import cmd_pill_log
    await cmd_pill_log(callback.message)
    await callback.answer()


@router.message(F.text == "❓ FAQ")
async def cmd_faq_menu(message: types.Message):
    from handlers.base import cmd_faq
    await cmd_faq(message)
