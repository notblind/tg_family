from aiogram.fsm.state import State, StatesGroup


class BirthdayStates(StatesGroup):
    name = State()
    date = State()
    category = State()
    note = State()


class TaskStates(StatesGroup):
    text = State()
    deadline = State()


class PillStates(StatesGroup):
    name = State()
    reminder_time = State()
    days_of_week = State()
    duration = State()
    end_date = State()
