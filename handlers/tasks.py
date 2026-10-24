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
    text = State()
    deadline = State()


@router.message(F.text == "/add_task")
async def cmd_add_task(message: types.Message, state: FSMContext):
    await message.answer("Введите описание задачи:")
    await state.set_state(TaskStates.text)


@router.message(TaskStates.text)
async def process_task_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer(
        "Введите дедлайн в формате ДД.ММ ЧЧ:ММ (например, 25.10 18:00), "
        "или отправьте /skip если дедлайна нет:"
    )
    await state.set_state(TaskStates.deadline)


@router.message(TaskStates.deadline)
async def process_task_deadline(message: types.Message, state: FSMContext):
    if message.text == "/skip":
        deadline = None
    else:
        try:
            deadline = datetime.strptime(message.text, "%d.%m %H:%M")
            # Set year to current year
            deadline = deadline.replace(year=datetime.now().year)
        except ValueError:
            await message.answer("Неверный формат. Используйте ДД.ММ ЧЧ:ММ (например, 25.10 18:00):")
            return
    
    await state.update_data(deadline=deadline)
    data = await state.get_data()
    
    async with get_session() as session:
        task = Task(
            text=data['text'],
            deadline=deadline
        )
        session.add(task)
        await session.commit()
    
    deadline_text = deadline.strftime("%d.%m %H:%M") if deadline else "без дедлайна"
    await message.answer(f"✅ Задача добавлена: {data['text']} (дедлайн: {deadline_text})")
    await state.clear()


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
    
    await message.answer(text)


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
