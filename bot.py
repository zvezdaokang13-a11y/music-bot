import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shazamio import Shazam
from yt_dlp import YoutubeDL

# Токени бот ва канали шумо
API_TOKEN = "8706389884:AAG8CiAOz4pNx35B7A0tzKnTJsPgsW69a4Q" # ⚠️ ДИҚҚАТ: Инҷо токени пурраи худро ҷобаҷо кунед!
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
        await message.answer("Салом! Обунагӣ тасдиқ шуд. Порчаи мусиқӣ ё видеоро фиристед.")
    else:
        await message.answer("Барои истифодабарии бот аввал ба канал обуна шавед!", reply_markup=get_sub_keyboard())

@dp.callback_query(F.data == "check_subscription")
async def check_callback(callback: types.CallbackQuery):
    if await check_sub(callback.from_user.id):
        await callback.message.edit_text("✅ Раҳмат! Ҳозир метавонед порчаи мусиқиро фиристед.")
    else:
        await callback.answer("❌ Шумо ҳанӯз ба канал обуна нашудаед!", show_alert=True)

@dp.message(F.voice | F.audio | F.video)
async def handle_audio(message: types.Message):
    if not await check_sub(message.from_user.id):
        await message.answer("⚠️ Барои истифодаи бот аввал ба канал обуна шавед!", reply_markup=get_sub_keyboard())
        return

    msg = await message.answer("⏳ Мусиқӣ коркард ва ҷустуҷӯ шуда истодааст...")
    
    file_id = message.voice.file_id if message.voice else (message.audio.file_id if message.audio else message.video.file_id)
    file = await bot.get_file(file_id)
    file_path = f"temp_{message.from_user.id}.mp3"
    await bot.download_file(file.file_path, file_path)

    try:
        out = await shazam.recognize(file_path)
        track = out.get('track')
        
        if not track:
            await msg.edit_text("❌ Ин мусиқиро пайдо карда натавонистам.")
            if os.path.exists(file_path): os.remove(file_path)
            return

        title = track['title']
        subtitle = track['subtitle']
        search_query = f"{title} {subtitle}"
        
        await msg.edit_text(f"🎵 Мусиқӣ пайдо шуд: **{search_query}**\n⏳ Боргирии файли MP3...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'song_{message.from_user.id}.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(f"ytsearch1:{search_query}", download=True)
            filename = f"song_{message.from_user.id}.mp3"

        audio_file = types.FSInputFile(filename)
        await message.answer_audio(audio_file, caption=f"🎧 **{title}** - {subtitle}")

        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(filename): os.remove(filename)
        await msg.delete()

    except Exception:
        await msg.edit_text("❌ Ҳангоми ҷустуҷӯ хатогӣ рӯй дод.")
        if os.path.exists(file_path): os.remove(file_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
