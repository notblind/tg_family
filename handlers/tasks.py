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
    add_task = State()


@router.message(F.text == "/add_task")
async def cmd_add_task(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data="cancel_add_task")
    keyboard.adjust(1)

    await message.answer(
        "Введите задачу в формате:\n"
        "Текст задачи - ДД.ММ ЧЧ:ММ\n\n"
        "Пример: Купить продукты - 25.10 18:00\n\n"
        "Если дедлайна нет, просто введите текст задачи.",
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(TaskStates.add_task)


@router.callback_query(F.data == "cancel_add_task")
async def cancel_add_task(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Добавление задачи отменено")
    await callback.answer()


@router.message(TaskStates.add_task)
async def process_add_task(message: types.Message, state: FSMContext):
    try:
        # Check if there's a deadline
        if ' - ' in message.text:
            parts = message.text.split(' - ')
            text = parts[0].strip()
            deadline_str = parts[1].strip()
            
            try:
                deadline = datetime.strptime(deadline_str, "%d.%m %H:%M")
                deadline = deadline.replace(year=datetime.now().year)
            except ValueError:
                await message.answer(
                    "Неверный формат дедлайна. Используйте ДД.ММ ЧЧ:ММ\n\n"
                    "Пример: Купить продукты - 25.10 18:00"
                )
                return
        else:
            text = message.text.strip()
            deadline = None
        
        async with get_session() as session:
            task = Task(
                text=text,
                deadline=deadline
            )
            session.add(task)
            await session.commit()
        
        deadline_text = deadline.strftime("%d.%m %H:%M") if deadline else "без дедлайна"
        await message.answer(f"✅ Задача добавлена: {text} (дедлайн: {deadline_text})")
        await state.clear()
    except Exception as e:
        await message.answer(
            "Неверный формат. Используйте: Текст задачи - ДД.ММ ЧЧ:ММ\n\n"
            "Или просто текст задачи без дедлайна."
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
        keyboard.button(text=f"❌ {task.text[:20]}...", callback_data=f"delete_task_{task.id}")

    keyboard.adjust(2)

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


@router.callback_query(F.data.startswith("delete_task_"))
async def callback_delete_task(callback: types.CallbackQuery):
    try:
        task_id = int(callback.data.split("_")[-1])
        async with get_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if task:
                await session.delete(task)
                await session.commit()
                await callback.message.edit_text(f"🗑️ Задача удалена: {task.text}")
            else:
                await callback.answer("Задача не найдена")
    except (ValueError, IndexError):
        await callback.answer("Неверный формат")
    await callback.answer()
