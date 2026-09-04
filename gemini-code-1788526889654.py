import os
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера с вашим токеном
TOKEN = "8842726749:AAG1v-6yz64Xn9BWBNtpC-oYT4kW6ui6UIo"
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# Состояния для прохождения симуляции
class ScamSimStates(StatesGroup):
    waiting_for_action = State()

# Главное меню с выбором тем
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 Банки и финансы", callback_data="scenario_bank")],
        [InlineKeyboardButton(text="🏛 Госуслуги и документы", callback_data="scenario_gov")],
        [InlineKeyboardButton(text="📈 Инвестиции и крипта", callback_data="scenario_crypto")],
        [InlineKeyboardButton(text="🆘 Экстренная помощь", callback_data="help_sos")]
    ])
    return keyboard

# Клавиатура ответов во время «звонка»/диалога
def get_simulation_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Сбросить трубку / Заблокировать", callback_data="action_hangup")],
        [InlineKeyboardButton(text="🗣 Продолжить диалог", callback_data="action_continue")],
        [InlineKeyboardButton(text="❓ Спросить кодовое слово", callback_data="action_question")]
    ])
    return keyboard

@router.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "Утром каждый день как судный, когда наступает день идти в колледж, "
        "но давай прокачаем твою кибербезопасность.\n\n"
        "Я бот-тренажер «Антимошенник». Выбери тип угрозы, с которой хочешь столкнуться:"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu())

# Обработка выбора сценария
@router.callback_query(F.data.startswith("scenario_"))
async def start_scenario(callback: CallbackQuery, state: FSMContext):
    scenario_type = callback.data.split("_")[1]
    
    if scenario_type == "bank":
        await callback.message.answer("⚠️ *Входящий аудиовызов от абонента: Сбербанк / ВТБ*")
        await callback.message.answer(
            "🔊 *[Аудиосообщение]*: «Здравствуйте! Это служба безопасности банка. "
            "По вашей карте зафиксирована подозрительная транзакция на 15 000 рублей. "
            "Для отмены перевода срочно назовите код из СМС, который вам сейчас пришел!»",
            reply_markup=get_simulation_keyboard()
        )
        await state.set_state(ScamSimStates.waiting_for_action)
    elif scenario_type == "gov":
        await callback.message.answer("🔊 *[Аудиосообщение]*: «Здравствуйте, это единый портал Госуслуг. Ваш аккаунт пытаются взломать, зафиксирован вход из другого региона. Назовите номер СНИЛС для блокировки угрозы!»", reply_markup=get_simulation_keyboard())
        await state.set_state(ScamSimStates.waiting_for_action)
    elif scenario_type == "crypto":
        await callback.message.answer("🔊 *[Аудиосообщение]*: «Привет! Я криптотрейдер, запуск новой монеты дает х100 завтра. Переведи от 1000 рублей на кошелек, и я удвою твой депозит за час!»", reply_markup=get_simulation_keyboard())
        await state.set_state(ScamSimStates.waiting_for_action)
        
    await callback.answer()

# Обработка действий пользователя в симуляции
@router.callback_query(ScamSimStates.waiting_for_action, F.data.startswith("action_"))
async def process_simulation_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    
    if action == "hangup":
        result_text = (
            "🎉 *Успех! Вы распознали мошенника.*\n\n"
            "🧠 *Разбор полетов:* Банки и госорганы никогда не просят назвать коды из СМС или СНИЛС по телефону. Вы вовремя сбросили трубку и защитили свои деньги."
        )
    elif action == "continue":
        result_text = (
            "❌ *Вы попались на крючок!*\n\n"
            "🧠 *Разбор полетов:* Продолжая диалог, вы дали мошенникам заговорить вам зубы за счет создания ложной срочности и страха потери средств. Злоумышленники победили."
        )
    elif action == "question":
        result_text = (
            "⚠️ *Частичный успех.*\n\n"
            "🧠 *Разбор полетов:* Мошенники умеют мастерски обходить вопросы. Самый надежный способ — положить трубку и перезвонить на официальный номер банка самостоятельно."
        )
    else:
        result_text = "Неизвестное действие."

    await callback.message.answer(result_text, reply_markup=get_main_menu())
    await state.clear()
    await callback.answer()

# Экстренная помощь
@router.callback_query(F.data == "help_sos")
async def help_sos(callback: CallbackQuery):
    sos_text = (
        "🆘 *Что делать, если вас уже обманули:*\n\n"
        "1. *Срочно заблокируйте карты* через мобильное приложение банка или горячую линию.\n"
        "2. *Смените пароли* от Госуслуг, почты и банковских приложений.\n"
        "3. *Сохраните доказательства:* сделайте скриншоты переписок, запишите номера телефонов.\n"
        "4. *Обратитесь в полицию* с заявлением о мошенничестве."
    )
    await callback.message.answer(sos_text, reply_markup=get_main_menu())
    await callback.answer()

# Запуск бота
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())