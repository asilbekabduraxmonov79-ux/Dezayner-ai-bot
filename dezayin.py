import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from groq import Groq
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ========== KONFIGURATSIYA ==========
API_TOKEN = "8635262238:AAHuWIdE8fVoYiUbyx9kDz_kZjLPFdx"
GROQ_API_KEY = "gsk_jmCGFKhSp1SFp04Cd6aJwGdyb3FYI93WvDP"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
groq_client = Groq(api_key=GROQ_API_KEY)

# ========== MA'LUMOTLAR ==========
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def add_subscription(user_id, plan, days):
    users = load_users()
    user_id = str(user_id)
    expiry = datetime.now() + timedelta(days=days)
    users[user_id] = {"plan": plan, "expiry": expiry.isoformat()}
    save_users(users)

# ========== MENYU ==========
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Reklama yoz"), KeyboardButton(text="📱 Post yoz")],
        [KeyboardButton(text="🌐 Tarjima"), KeyboardButton(text="💰 Tariflar")],
        [KeyboardButton(text="👤 Mening obunam")]
    ],
    resize_keyboard=True
)

# ========== HOLATLAR ==========
class ReklamaState(StatesGroup):
    mahsulot = State()
    maqsad = State()
    uslub = State()

class PostState(StatesGroup):
    mavzu = State()
    platforma = State()

class TarjimaState(StatesGroup):
    matn = State()
    til = State()

# ========== AI FUNKSIYA ==========
async def ai_sorov(prompt: str) -> str:
    try:
        response = await asyncio.to_thread(
            groq_client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Xatolik: {e}"

# ========== KOMANDALAR ==========
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        add_subscription(user_id, "free_trial", 7)
        await message.answer("🎉 Xush kelibsiz! 7 kun bepul sinov vaqti berildi!")
    
    await message.answer("🤖 Dezayner AI Bot", reply_markup=main_keyboard)

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    ADMIN_IDS = [5599261398]
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Siz admin emassiz!")
        return
    
    users = load_users()
    await message.answer(f"📊 Statistika: {len(users)} foydalanuvchi")

@dp.message(Command("add"))
async def add_user(message: types.Message):
    ADMIN_IDS = [5599261398]
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()
    if len(args) >= 4:
        add_subscription(args[1], args[2], int(args[3]))
        await message.answer(f"✅ Obuna berildi!")

@dp.message(lambda msg: msg.text == "💰 Tariflar")
async def tarif(message: types.Message):
    await message.answer("💰 Tariflar:\nStandart: 100,000 so'm/oy\nPremium: 200,000 so'm/oy")

@dp.message(lambda msg: msg.text == "📝 Reklama yoz")
async def reklama_start(message: types.Message, state: FSMContext):
    await state.set_state(ReklamaState.mahsulot)
    await message.answer("Mahsulot nomini yozing:")

@dp.message(ReklamaState.mahsulot)
async def reklama_mahsulot(message: types.Message, state: FSMContext):
    await state.update_data(mahsulot=message.text)
    await state.set_state(ReklamaState.maqsad)
    await message.answer("Maqsad: sotish / tanishtiruv?")

@dp.message(ReklamaState.maqsad)
async def reklama_maqsad(message: types.Message, state: FSMContext):
    await state.update_data(maqsad=message.text)
    await state.set_state(ReklamaState.uslub)
    await message.answer("Uslub: professional / qisqa / kreativ?")

@dp.message(ReklamaState.uslub)
async def reklama_uslub(message: types.Message, state: FSMContext):
    await state.update_data(uslub=message.text)
    data = await state.get_data()
    await message.answer("⏳ Tayyorlanmoqda...")
    javob = await ai_sorov(f"{data['mahsulot']} uchun {data['maqsad']} maqsadida reklama yoz")
    await message.answer(f"✅ Reklama:\n\n{javob}")
    await state.clear()

@dp.message()
async def echo(message: types.Message):
    await message.answer("❓ Tushunmadim. Tugmalardan foydalaning!", reply_markup=main_keyboard)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
