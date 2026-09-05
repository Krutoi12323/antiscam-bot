import os
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
TOKEN = "8842726749:AAG1v-6yz64Xn9BWBNtpC-oYT4kW6ui6UIo"
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# Настройка порта и веб-сервера для Railway (устраняет ошибку "Unexposed service")
PORT = int(os.getenv("PORT", 8080))
PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost:8080")
if not PUBLIC_DOMAIN.startswith("http"):
    WEBAPP_URL = f"https://{PUBLIC_DOMAIN}/webapp"
else:
    WEBAPP_URL = f"{PUBLIC_DOMAIN}/webapp"

@router.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Симулировать входящий звонок (Mini App)", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="🆘 Экстренная помощь", callback_data="help_sos")]
    ])
    welcome_text = (
        "🤖 Бот успешно запущен и заработал!\n\n"
        "Утром каждый день как судный, когда наступает день идти в колледж, "
        "но давай прокачаем твою кибербезопасность.\n\n"
        "Я бот-тренажер «Антимошенник». Нажми кнопку ниже, чтобы запустить интерактивный звонок в Mini App:"
    )
    await message.answer(welcome_text, reply_markup=keyboard)

@router.callback_query(F.data == "help_sos")
async def help_sos(callback: CallbackQuery):
    sos_text = (
        "🆘 Что делать, если вас уже обманули:\n\n"
        "1. Срочно заблокируйте карты через мобильное приложение банка.\n"
        "2. Смените пароли от Госуслуг и почты.\n"
        "3. Обратитесь в полицию с заявлением."
    )
    await callback.message.answer(sos_text)
    await callback.answer()

dp.include_router(router)

# HTML-код встроенного Mini App с интерфейсом звонка
async def handle_index(request):
    return web.Response(text="Anti-Scam Bot Web Service is running!")

async def handle_webapp(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Входящий звонок</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                background-color: #17212b;
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: space-between;
                height: 100vh;
                padding: 40px 20px;
                box-sizing: border-box;
                text-align: center;
            }
            .caller-info {
                margin-top: 40px;
                width: 100%;
            }
            .avatar {
                width: 100px;
                height: 100px;
                background: linear-gradient(135deg, #e53935, #b71c1c);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 40px;
                margin: 0 auto 20px auto;
                box-shadow: 0 4px 15px rgba(229, 57, 53, 0.4);
            }
            h1 { font-size: 24px; margin: 10px 0; }
            p { color: #828b94; font-size: 16px; margin: 0; }
            .timer { font-size: 18px; color: #4ea4f3; margin-top: 15px; display: none; }
            .actions {
                display: flex;
                justify-content: space-around;
                width: 100%;
                max-width: 300px;
                margin-bottom: 40px;
            }
            .btn {
                width: 70px;
                height: 70px;
                border-radius: 50%;
                border: none;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 28px;
                cursor: pointer;
                transition: transform 0.1s;
            }
            .btn:active { transform: scale(0.95); }
            .btn-decline { background-color: #e53935; color: white; }
            .btn-accept { background-color: #4cd964; color: white; }
            .script-box {
                background: #242f3d;
                padding: 15px;
                border-radius: 12px;
                font-size: 14px;
                text-align: left;
                width: 100%;
                box-sizing: border-box;
                margin-top: 20px;
                display: none;
                border-left: 4px solid #e53935;
            }
        </style>
    </head>
    <body>
        <div class="caller-info">
            <div class="avatar">🏦</div>
            <h1>Служба безопасности</h1>
            <p id="callStatus">Входящий аудиовызов...</p>
            <div class="timer" id="callTimer">00:00</div>
            <div class="script-box" id="scriptBox">
                <strong>Мошенник:</strong> «Здравствуйте! По вашей карте зафиксирован сомнительный перевод на 15 000 рублей. Срочно назовите код из СМС для отмены операции!»
            </div>
        </div>

        <div class="actions" id="actionButtons">
            <button class="btn btn-decline" onclick="declineCall()" title="Сбросить">❌</button>
            <button class="btn btn-accept" onclick="acceptCall()" title="Ответить">📞</button>
        </div>

        <script>
            let tg = window.Telegram.WebApp;
            tg.expand();

            let timerInterval;
            let seconds = 0;

            function acceptCall() {
                document.getElementById('callStatus').innerText = "Разговор идет...";
                document.getElementById('callTimer').style.display = 'block';
                document.getElementById('scriptBox').style.display = 'block';
                document.querySelector('.btn-accept').style.display = 'none';

                timerInterval = setInterval(() => {
                    seconds++;
                    let mins = Math.floor(seconds / 60).toString().padStart(2, '0');
                    let secs = (seconds % 60).toString().padStart(2, '0');
                    document.getElementById('callTimer').innerText = `${mins}:${secs}`;
                }, 1000);
            }

            function declineCall() {
                clearInterval(timerInterval);
                document.getElementById('callStatus').innerText = "Звонок завершен";
                document.getElementById('actionButtons').style.display = 'none';
                document.getElementById('scriptBox').style.display = 'none';
                
                setTimeout(() => {
                    tg.close();
                }, 1200);
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/webapp', handle_webapp)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f"Web server started on port {PORT}")

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
