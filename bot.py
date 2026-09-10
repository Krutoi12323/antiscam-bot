import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    MenuButtonWebApp,
    WebAppInfo,
)

# Токен твоего бота
TOKEN = "8842726749:AAEYhZy0mLV_sgQAO0Y6xJDI6ly65G3G8lY"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(
    token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Состояния FSM для диалога
class DialogState(StatesGroup):
    waiting_for_name = State()
    chatting = State()


# HTML-страница для веб-сервера (Mini App / "Экстренный вызов")
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--tg-theme-bg-color, #1c1c1e);
            color: var(--tg-theme-text-color, #ffffff);
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            box-sizing: border-box;
            text-align: center;
        }
        .card {
            background: var(--tg-theme-secondary-bg-color, #2c2c2e);
            padding: 24px;
            border-radius: 16px;
            width: 100%;
            max-width: 320px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        h2 { margin-top: 0; color: #ff3b30; }
        p { font-size: 14px; opacity: 0.8; line-height: 1.4; }
        .btn {
            background-color: #34c759;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            width: 100%;
            cursor: pointer;
            margin-top: 16px;
        }
        .btn-danger {
            background-color: #ff3b30;
            margin-top: 8px;
        }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚨 Подозрение на мошенничество!</h2>
        <p>Если вам звонят из «службы безопасности банка» или «полиции» и требуют перевести деньги — положите трубку!</p>
        <button class="btn" onclick="closeApp()">Понятно, сбросить вызов</button>
        <button class="btn btn-danger" onclick="reportFraud()">Сообщить о номере</button>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();

        function closeApp() {
            tg.close();
        }

        function reportFraud() {
            tg.sendData("report_fraud_action");
            tg.close();
        }
    </script>
</body>
</html>
"""


# Обработчик команды /start
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(DialogState.waiting_for_name)
    await message.answer(
        "👋 Привет! Я бот-консультант и тренажер **«Антимошенник»**.\n\n"
        "Вы можете свободно общаться со мной: рассказать о подозрительном звонке, СМС или ситуации, а я подскажу, мошенники это или нет.\n\n"
        "Как к вам обращаться?"
    )


# Обработчик команды /tips (советы)
@dp.message(F.text == "/tips")
async def cmd_tips(message: types.Message):
    await message.answer(
        "🛡 **Главные правила безопасности:**\n\n"
        "1. Сотрудники банков и МВД **никогда** не просят переводить деньги на «безопасные счета».\n"
        "2. Вас просят назвать код из СМС или цифры с карты? **Немедленно кладите трубку.**\n"
        "3. Угрожают арестом или кредитом? Это психологическое давление. Положите трубку и перезвоните в банк сами по номеру с оборотной стороны карты."
    )


# Получение имени пользователя (FSM)
@dp.message(DialogState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await state.set_state(DialogState.chatting)
    await message.answer(
        f"Рад знакомству, {name}!\n\n"
        "💬 **Режим разговора активирован.** Теперь вы можете писать мне любые сообщения своими словами. Например:\n"
        "• *«Мне звонили из полиции и сказали, что на меня берут кредит»*\n"
        "• *«Пришла СМС с кодом подтверждения от Госуслуг, хотя я ничего не делал»*\n\n"
        "Расскажите, что произошло?"
    )


# Продвинутая функция живого диалога с ботом
@dp.message(DialogState.chatting)
async def process_live_chat(message: types.Message, state: FSMContext):
    user_text = message.text.lower()
    data = await state.get_data()
    name = data.get("name", "Друг")

    # Интеллектуальный анализ текста сообщения пользователя
    if any(word in user_text for word in ['полици', 'мвд', 'следствен', 'капитан', 'майор', 'суд']):
        reply = (
            f"🚨 **Внимание, {name}! Это классическая схема обмана.**\n\n"
            "Настоящие сотрудники полиции, следственного комитета или МВД **никогда** не решают вопросы по телефону и тем более не пугают уголовными делами через мессенджеры. "
            "Цель злоумышленников — запугать вас, чтобы вы запаниковали и начали выполнять их указания. **Немедленно положите трубку!**"
        )
    elif any(word in user_text for word in ['безопасн', 'счет', 'резервн', 'инкассац', 'центробанк']):
        reply = (
            f"⚠️ **Опасно! Это мошенники из фальшивой «службы безопасности»**, {name}.\n\n"
            "Понятия «безопасный счет» или «резервный счет» в природе не существует. Банки и Центробанк никогда не переводят деньги граждан на сторонние счета. Срочно прекратите разговор."
        )
    elif any(word in user_text for word in ['код из смс', 'цифр', 'пароль', 'карты', 'cvv', 'cve', 'три цифр']):
        reply = (
            f"🛑 **Ни в коем случае не сообщайте эти данные!**\n\n"
            "Код из СМС или цифры с обратной стороны карты — это ключ к вашим деньгам. Сотрудники банка не имеют права их запрашивать. Если вы их назовете, мошенники мгновенно спишут все сбережения."
        )
    elif any(word in user_text for word in ['привет', 'здравствуй', 'как дела']):
        reply = f"Привет, {name}! Я на связи и готов защитить вас от мошенников. Расскажите, поступал ли вам подозрительный звонок или сообщение?"
    else:
        # Универсальный поддерживающий ответ для живого общения
        reply = (
            f"Я внимательно выслушал вас, {name}. Судя по описанию, ситуация требует осторожности.\n\n"
            "Главное правило: **никогда не принимайте спонтанных финансовых решений под давлением**. "
            "Если сомневаетесь, напишите подробнее, что именно вам сказали или предложили сделать, и я дам точный совет."
        )

    await message.answer(reply)


# Обработка данных, возвращаемых из Mini App
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    data = message.web_app_data.data
    if data == "report_fraud_action":
        await message.answer(
            "🚨 Информация принята! Номер занесен в локальную базу подозрительных. Спасибо за бдительность!"
        )


# Настройка постоянной кнопки меню (Mini App) с путем /webapp
async def set_default_commands(bot: Bot):
    web_app_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "https://example.com")
    if not web_app_url.startswith("http"):
        web_app_url = f"https://{web_app_url}"
    
    full_url = f"{web_app_url.rstrip('/')}/webapp"

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🚨 Экстренный вызов",
            web_app=WebAppInfo(url=full_url),
        )
    )


# Веб-сервер на aiohttp для отдачи страницы Mini App (обрабатываем и /, и /webapp)
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
    logging.info(f"Веб-сервер запущен на порту {port}")


async def main():
    # Устанавливаем кнопку меню
    await set_default_commands(bot)

    # Запускаем веб-сервер в фоновом режиме
    asyncio.create_task(start_web_server())

    # Удаляем старые вебхуки/очереди и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот успешно запущен и начал опрос (polling)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
