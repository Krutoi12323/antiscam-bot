import asyncio
import logging
import os
import tempfile
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo, FSInputFile
from gtts import gTTS
import speech_recognition as sr
from pydub import AudioSegment

# Токен твоего бота
TOKEN = "8842726749:AAEYhZy0mLV_sgQAO0Y6xJDI6ly65G3G8lY"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Состояния FSM для диалога
class DialogState(StatesGroup):
    waiting_for_name = State()
    chatting = State()


# Обновленный дизайн Mini App с кнопками вызова и экстренных действий
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Антимошенник - Экстренный вызов</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--tg-theme-bg-color, #1c1c1e);
            color: var(--tg-theme-text-color, #ffffff);
            margin: 0; padding: 16px; display: flex; flex-direction: column;
            align-items: center; justify-content: center; height: 100vh; box-sizing: border-box; text-align: center;
        }
        .card {
            background: var(--tg-theme-secondary-bg-color, #2c2c2e);
            padding: 20px; border-radius: 20px; width: 100%; max-width: 340px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        }
        .icon { font-size: 48px; margin-bottom: 10px; }
        h2 { margin: 0 0 8px 0; color: #ff3b30; font-size: 22px; }
        p { font-size: 14px; opacity: 0.85; line-height: 1.4; margin-bottom: 20px; }
        .btn-group { display: flex; flex-direction: column; gap: 10px; }
        .btn {
            background-color: #3a3a3c; color: white; border: none; padding: 14px;
            border-radius: 12px; font-size: 15px; font-weight: 600; width: 100%; cursor: pointer;
            display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none;
        }
        .btn-danger { background-color: #ff3b30; color: white; }
        .btn-call { background-color: #34c759; color: white; }
        .btn:active { opacity: 0.8; }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🚨</div>
        <h2>Осторожно, мошенники!</h2>
        <p>Если вам звонят неизвестные и требуют перевести деньги или взять кредит — немедленно прервите вызов.</p>
        
        <div class="btn-group">
            <button class="btn btn-danger" onclick="actionHangup()">🔴 Положить трубку</button>
            <a href="tel:112" class="btn btn-call">📞 Экстренный вызов (112)</a>
            <button class="btn" onclick="actionReport()">⚠️ Сообщить боту</button>
        </div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();

        function actionHangup() {
            tg.sendData("hangup_action");
            tg.close();
        }

        function actionReport() {
            tg.sendData("report_fraud_action");
            tg.close();
        }
    </script>
</body>
</html>
"""


# Функция для генерации голосового сообщения из текста
async def send_voice_reply(message: types.Message, text_to_speak: str):
    await message.answer(text_to_speak)
    try:
        tts = gTTS(text=text_to_speak, lang='ru', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
            tmp_path = tmp.name
            tts.save(tmp_path)
        
        voice = FSInputFile(tmp_path)
        await message.answer_voice(voice=voice)
        os.unlink(tmp_path)
    except Exception as e:
        logging.error(f"Ошибка генерации голоса: {e}")


# Логика анализа текста и формирования ответа
async def handle_dialog_logic(message: types.Message, user_text: str, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "Друг")
    text_lower = user_text.lower()

    if any(word in text_lower for word in ['полици', 'мвд', 'следствен', 'капитан', 'майор', 'суд']):
        reply = f"Внимание, {name}! Настоящие сотрудники полиции никогда не решают вопросы по телефону. Немедленно положите трубку!"
    elif any(word in text_lower for word in ['безопасн', 'счет', 'резервн']):
        reply = f"Опасно, {name}! Понятия безопасного счета не существует. Это мошенники, сбросьте вызов."
    elif any(word in text_lower for word in ['код из смс', 'цифр', 'пароль']):
        reply = f"Ни в коем случае не называйте коды из СМС, {name}! Это украдет ваши деньги."
    else:
        reply = f"Я выслушал вас, {name}. Судя по вашим словам: «{user_text}», будьте осторожны и не поддавайтесь панике."

    await send_voice_reply(message, reply)


# Обработчик команды /start
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(DialogState.waiting_for_name)
    text = "👋 Привет! Я бот-консультант «Антимошенник». Вы можете разговаривать со мной голосом! Как к вам обращаться?"
    await send_voice_reply(message, text)


# Получение имени пользователя (FSM)
@dp.message(DialogState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await state.set_state(DialogState.chatting)
    text = f"Рад знакомству, {name}! Теперь вы можете отправлять мне голосовые сообщения, и я буду отвечать вам голосом."
    await send_voice_reply(message, text)


# Текстовый ввод в режиме диалога
@dp.message(DialogState.chatting, F.text)
async def process_text_chat(message: types.Message, state: FSMContext):
    await handle_dialog_logic(message, message.text, state)


# Голосовой ввод в режиме диалога (распознавание речи)
@dp.message(DialogState.chatting, F.voice)
async def process_voice_chat(message: types.Message, state: FSMContext):
    ogg_path = f"voice_{message.from_user.id}.ogg"
    wav_path = f"voice_{message.from_user.id}.wav"
    
    try:
        file_info = await bot.get_file(message.voice.file_id)
        await bot.download_file(file_info.file_path, ogg_path)
        
        sound = AudioSegment.from_file(ogg_path, format="ogg")
        sound.export(wav_path, format="wav")
        
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
            recognized_text = r.recognize_google(audio_data, language="ru-RU")
        
        if os.path.exists(ogg_path): os.remove(ogg_path)
        if os.path.exists(wav_path): os.remove(wav_path)
        
        await handle_dialog_logic(message, recognized_text, state)
        
    except Exception as e:
        logging.error(f"Ошибка распознавания голоса: {e}")
        if os.path.exists(ogg_path): os.remove(ogg_path)
        if os.path.exists(wav_path): os.remove(wav_path)
        await send_voice_reply(message, "Не удалось разобрать голосовое сообщение. Попробуйте записать его еще раз четче.")


# Обработка данных из Mini App (кнопки в приложении)
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    data = message.web_app_data.data
    if data == "hangup_action":
        await send_voice_reply(message, "Отлично! Вызов прерван. Вы в безопасности.")
    elif data == "report_fraud_action":
        await send_voice_reply(message, "Номер успешно занесен в базу подозрительных. Спасибо за бдительность!")


async def set_default_commands(bot: Bot):
    web_app_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "https://example.com")
    if not web_app_url.startswith("http"):
        web_app_url = f"https://{web_app_url}"
    full_url = f"{web_app_url.rstrip('/')}/webapp"
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="🚨 Экстренный вызов", web_app=WebAppInfo(url=full_url))
    )


async def handle_index(request):
    return web.Response(text=HTML_PAGE, content_type="text/html")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/webapp", handle_index)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    await set_default_commands(bot)
    asyncio.create_task(start_web_server())
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
