from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    enter_code = State()
    enter_url = State()
    confirm = State()
