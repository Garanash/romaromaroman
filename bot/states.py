from aiogram.fsm.state import State, StatesGroup

class OrderFSM(StatesGroup):
    name = State()
    phone = State()
    address = State()
    material = State()
    area = State()
    extras = State()
    photos = State()
    date = State()
    time = State()  # новое состояние для времени
    confirm = State() 