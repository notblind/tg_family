from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from database.session import get_session
from database.models import Task

router = Router()


class TaskStates(StatesGroup):
    add_task_name = State()
    add_task_deadline = State()


@router.message(F.text == "/add_task")
async def cmd_add_task(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data="cancel_add_task")
    keyboard.adjust(1)

    await message.answer(
        "Введите название задачи:",
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(TaskStates.add_task_name)


@router.message(TaskStates.add_task_name)
async def process_add_task_name(message: types.Message, state: FSMContext):
    task_name = message.text.strip()
    if not task_name:
        await message.answer("Название задачи не может быть пустым")
        return

    await state.update_data(task_name=task_name)

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Без дедлайна", callback_data="task_no_deadline")
    keyboard.button(text="Сегодня", callback_data="task_deadline_today")
    keyboard.button(text="Завтра", callback_data="task_deadline_tomorrow")
    keyboard.button(text="Через 3 дня", callback_data="task_deadline_3days")
    keyboard.button(text="Через неделю", callback_data="task_deadline_week")
    keyboard.button(text="Выбрать дату", callback_data="task_deadline_custom")
    keyboard.button(text="❌ Отмена", callback_data="cancel_add_task")
    keyboard.adjust(2)

    await message.answer(
        f"Задача: {task_name}\n\n"
        "Выберите дедлайн:",
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(TaskStates.add_task_deadline)


@router.callback_query(F.data == "task_no_deadline")
async def callback_task_no_deadline(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    task_name = data["task_name"]

    async with get_session() as session:
        task = Task(text=task_name, deadline=None)
        session.add(task)
        await session.commit()

    await state.clear()
    await callback.message.edit_text(f"✅ Задача добавлена: {task_name} (без дедлайна)")
    await callback.answer()


@router.callback_query(F.data == "task_deadline_today")
async def callback_task_deadline_today(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    task_name = data["task_name"]
    deadline = datetime.now().replace(hour=23, minute=59, second=0, microsecond=0)

    async with get_session() as session:
        task = Task(text=task_name, deadline=deadline)
        session.add(task)
        await session.commit()

    await state.clear()
    await callback.message.edit_text(f"✅ Задача добавлена: {task_name} (до {deadline.strftime('%d.%m %H:%M')})")
    await callback.answer()


@router.callback_query(F.data == "task_deadline_tomorrow")
async def callback_task_deadline_tomorrow(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    task_name = data["task_name"]
    from datetime import timedelta
    deadline = (datetime.now() + timedelta(days=1)).replace(hour=23, minute=59, second=0, microsecond=0)

    async with get_session() as session:
        task = Task(text=task_name, deadline=deadline)
        session.add(task)
        await session.commit()

    await state.clear()
    await callback.message.edit_text(f"✅ Задача добавлена: {task_name} (до {deadline.strftime('%d.%m %H:%M')})")
    await callback.answer()


@router.callback_query(F.data == "task_deadline_3days")
async def callback_task_deadline_3days(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    task_name = data["task_name"]
    from datetime import timedelta
    deadline = (datetime.now() + timedelta(days=3)).replace(hour=23, minute=59, second=0, microsecond=0)

    async with get_session() as session:
        task = Task(text=task_name, deadline=deadline)
        session.add(task)
        await session.commit()

    await state.clear()
    await callback.message.edit_text(f"✅ Задача добавлена: {task_name} (до {deadline.strftime('%d.%m %H:%M')})")
    await callback.answer()


@router.callback_query(F.data == "task_deadline_week")
async def callback_task_deadline_week(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    task_name = data["task_name"]
    from datetime import timedelta
    deadline = (datetime.now() + timedelta(days=7)).replace(hour=23, minute=59, second=0, microsecond=0)

    async with get_session() as session:
        task = Task(text=task_name, deadline=deadline)
        session.add(task)
        await session.commit()

    await state.clear()
    await callback.message.edit_text(f"✅ Задача добавлена: {task_name} (до {deadline.strftime('%d.%m %H:%M')})")
    await callback.answer()


@router.callback_query(F.data == "task_deadline_custom")
async def callback_task_deadline_custom(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите дедлайн в формате ДД.ММ ЧЧ:ММ\n\n"
        "Пример: 25.10 18:00"
    )
    await callback.answer()


@router.message(TaskStates.add_task_deadline)
async def process_add_task_deadline(message: types.Message, state: FSMContext):
    try:
        deadline_str = message.text.strip()
        deadline = datetime.strptime(deadline_str, "%d.%m %H:%M")
        deadline = deadline.replace(year=datetime.now().year)

        data = await state.get_data()
        task_name = data["task_name"]

        async with get_session() as session:
            task = Task(text=task_name, deadline=deadline)
            session.add(task)
            await session.commit()

        await state.clear()
        await message.answer(f"✅ Задача добавлена: {task_name} (до {deadline.strftime('%d.%m %H:%M')})")
    except ValueError:
        await message.answer(
            "Неверный формат. Используйте ДД.ММ ЧЧ:ММ\n\n"
            "Пример: 25.10 18:00"
        )


@router.message(F.text == "/tasks")
async def cmd_tasks(message: types.Message):
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Task).where(Task.is_completed == False).order_by(Task.deadline)
        )
        tasks = result.scalars().all()

    if not tasks:
        await message.answer("Список задач пуст")
        return

    keyboard = InlineKeyboardBuilder()
    text = "📋 Задачи:\n\n"
    now = datetime.now()

    for task in tasks:
        if task.deadline:
            if task.deadline < now:
                text += f"⚠️ {task.text} (ПРОСРОЧЕНО: {task.deadline.strftime('%d.%m %H:%M')})\n"
            else:
                text += f"📌 {task.text} (до {task.deadline.strftime('%d.%m %H:%M')})\n"
        else:
            text += f"📌 {task.text} (без дедлайна)\n"

        keyboard.button(text=f"✅ {task.text[:20]}...", callback_data=f"complete_task_{task.id}")

    keyboard.adjust(1)

    await message.answer(text, reply_markup=keyboard.as_markup())


@router.message(F.text == "/tasks_all")
async def cmd_tasks_all(message: types.Message):
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Task).order_by(Task.is_completed, Task.deadline))
        tasks = result.scalars().all()
    
    if not tasks:
        await message.answer("Список задач пуст")
        return
    
    text = "📋 Все задачи:\n\n"
    
    for task in tasks:
        status = "✅" if task.is_completed else "📌"
        if task.deadline:
            text += f"{status} {task.text} (до {task.deadline.strftime('%d.%m %H:%M')})\n"
        else:
            text += f"{status} {task.text} (без дедлайна)\n"
    
    await message.answer(text)


@router.message(F.text.startswith("/complete_task_"))
async def cmd_complete_task(message: types.Message):
    try:
        task_id = int(message.text.split("_")[-1])
        async with get_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if task:
                task.is_completed = True
                await session.commit()
                await message.answer(f"✅ Задача выполнена: {task.text}")
            else:
                await message.answer("Задача не найдена")
    except (ValueError, IndexError):
        await message.answer("Неверный формат команды")


@router.callback_query(F.data.startswith("complete_task_"))
async def callback_complete_task(callback: types.CallbackQuery):
    try:
        task_id = int(callback.data.split("_")[-1])
        async with get_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if task:
                task.is_completed = True
                await session.commit()
                await callback.message.edit_text(f"✅ Задача выполнена: {task.text}")
            else:
                await callback.answer("Задача не найдена")
    except (ValueError, IndexError):
        await callback.answer("Неверный формат")
    await callback.answer()


@router.message(F.text.startswith("/delete_task_"))
async def cmd_delete_task(message: types.Message):
    try:
        task_id = int(message.text.split("_")[-1])
        async with get_session() as session:
            from sqlalchemy import select, delete
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if task:
                await session.delete(task)
                await session.commit()
                await message.answer(f"🗑️ Задача удалена: {task.text}")
            else:
                await message.answer("Задача не найдена")
    except (ValueError, IndexError):
        await message.answer("Неверный формат команды")
