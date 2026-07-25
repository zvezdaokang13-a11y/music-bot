import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from shazamio import Shazam

API_TOKEN = "8706389884:AAG8CiAOz4pNx35B7A0tzKnTJsPgsW69a4Q"
CHANNEL_USERNAME = "@farid_kanal_taj"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
shazam = Shazam()

async def check_sub(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return False

def get_sub_keyboard():
    channel_url = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Обуна шудан ба канал", url=channel_url)],
        [InlineKeyboardButton(text="✅ Санҷидани обуна", callback_data="check_subscription")]
    ])

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    if await check_sub(message.from_user.id):
        await message.answer("Салом! Порчаи мусиқӣ, паёми овозӣ ё видеоро фиристед.")
    else:
        await message.answer("Барои истифодабарии бот аввал ба канал обуна шавед!", reply_markup=get_sub_keyboard())

@dp.callback_query(F.data == "check_subscription")
async def check_callback(callback: types.CallbackQuery):
    if await check_sub(callback.from_user.id):
        await callback.message.edit_text("✅ Раҳмат! Ҳозир метавонед видео ё овози худро фиристед.")
    else:
        await callback.answer("❌ Шумо ҳанӯз ба канал обуна нашудаед!", show_alert=True)

@dp.message(F.voice | F.audio | F.video | F.video_note)
async def handle_media(message: types.Message):
    if not await check_sub(message.from_user.id):
        await message.answer("⚠️ Барои истифодаи бот аввал ба канал обуна шавед!", reply_markup=get_sub_keyboard())
        return

    msg = await message.answer("⏳ Мусиқӣ коркард ва ҷустуҷӯ шуда истодааст...")
    
    file_id = message.voice.file_id if message.voice else (
        message.audio.file_id if message.audio else (
            message.video.file_id if message.video else message.video_note.file_id
        )
    )
    
    file = await bot.get_file(file_id)
    input_file = f"temp_{message.from_user.id}.mp4"
    await bot.download_file(file.file_path, input_file)

    try:
        out = await shazam.recognize(input_file)
        track = out.get('track')
        
        if not track:
            await msg.edit_text("❌ Ин мусиқиро пайдо карда натавонистам.")
            if os.path.exists(input_file): os.remove(input_file)
            return

        title = track.get('title', 'Номаълум')
        subtitle = track.get('subtitle', 'Номаълум')
        
        await msg.edit_text(f"✅ **Мусиқӣ пайдо шуд!**\n\n🎵 **Суруд:** {title}\n👤 **Иҷрокунанда:** {subtitle}", parse_mode="Markdown")

    except Exception as e:
        print(f"Error: {e}")
        await msg.edit_text("❌ Ҳангоми ҷустуҷӯ хатогӣ рӯй дод.")
    
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
