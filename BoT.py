import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Message, CallbackQuery

TOKEN = "8647123805:AAHu13g0TsMEkOLvtvcavx4UisNCERVSOrM"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Бази даних в пам'яті
users_db = {}
admin_ids = [6700507253]  # Твій ID
sponsors = [{"name": "Канал спонсор", "url": "https://t.me/telegram"}]
bot_star_pool = 5000  # Пул зірок для виведення

# Головне меню внизу
def get_main_keyboard(is_admin=False):
    kb = [
        [KeyboardButton(text="⭐ Заработать звезды"), KeyboardButton(text="🎯 PvP игры")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💸 Вывод звезд")],
        [KeyboardButton(text="📋 Задания"), KeyboardButton(text="📖 Инструкция")],
        [KeyboardButton(text="🏆 Топ"), KeyboardButton(text="🛒 Магазин звезд")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="🛠 Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: Message):
    uid = message.from_user.id
    is_admin = (uid in admin_ids)
    
    # Рефералка
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id != uid and ref_id in users_db:
            users_db[ref_id]["tickets"] += 3
            try:
                await bot.send_message(ref_id, "🎉 За приглашенного друга вам начислено +3 звезды! ⭐")
            except:
                pass

    if uid not in users_db:
        users_db[uid] = {"nickname": message.from_user.full_name, "tickets": 10}

    sponsor_buttons = []
    for sp in sponsors:
        sponsor_buttons.append([InlineKeyboardButton(text=f"📢 {sp['name']}", url=sp['url']), InlineKeyboardButton(text="⚙️ Запустить", url=sp['url'])])
    sponsor_buttons.append([InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=sponsor_buttons)
    
    text = (
        "💕 **Спасибо, что ты вернулся** \n\n"
        "✨ **ПОЛУЧАЙ ПО 3 ЗВЕЗДЫ ЗА ДРУГА И ИГРАЙ В PvP** ⭐\n\n"
        "Получай звезды за клики, задания и приглашенных друзей, выигрывай в PvP и участвуй в конкурсах 🎅.\n\n"
        "**Чтобы повторно активировать бота и получить 1 ⭐:**\n"
        "1️⃣ Подпишись на наших спонсоров (это займет 5 секунд)\n"
        "2️⃣ Нажми «Проверить подписку ✅»"
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("secret_admin_777"))
async def make_me_admin(message: Message):
    uid = message.from_user.id
    if uid not in admin_ids:
        admin_ids.append(uid)
    await message.answer("✅ Права администратора успешно активированы!", reply_markup=get_main_keyboard(True))

@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery):
    uid = callback.from_user.id
    is_admin = (uid in admin_ids)
    
    await callback.message.edit_text(
        "✅ **Вы успешно активировали(а) бота!**\n\nДобро пожаловать в главное меню 👇",
        parse_mode="Markdown"
    )
    await callback.message.answer("Главное меню открыто:", reply_markup=get_main_keyboard(is_admin))
    await callback.answer("Успешно!")

@dp.message(F.text == "⭐ Заработать звезды")
async def clicker_menu(message: Message):
    uid = message.from_user.id
    if uid in users_db:
        users_db[uid]["tickets"] += 0.10
    bal = round(users_db.get(uid, {}).get("tickets", 10), 2)
    await message.answer(f"⚡️ Вы кликнули и получили **+0.10 ⭐**!\nВаш текущий баланс: {bal} ⭐", parse_mode="Markdown")

@dp.message(F.text == "🎯 PvP игры")
async def pvp_info(message: Message):
    await message.answer("⚔️ **PvP Игры**\n\nВыбирайте игру, делайте ставку звёздами и побеждайте реальных игроков в реальном времени!", parse_mode="Markdown")

@dp.message(F.text == "👤 Профиль")
async def my_profile(message: Message):
    uid = message.from_user.id
    user = users_db.get(uid, {"nickname": message.from_user.full_name, "tickets": 10})
    link = f"https://t.me/StarsGiveKway_bot?start={uid}"
    text = (
        f"👤 **Ваш профиль**\n\n"
        f"Имя: {user['nickname']}\n"
        f"ID: `{uid}`\n"
        f"Баланс: **{round(user['tickets'], 2)} ⭐**\n\n"
        f"🔗 Ваша реферальная ссылка:\n`{link}`"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "💸 Вывод звезд")
async def withdraw_stars(message: Message):
    uid = message.from_user.id
    bal = users_db.get(uid, {}).get("tickets", 10)
    if bal >= 25:
        users_db[uid]["tickets"] = 0
        await message.answer(f"✅ Заявка на вывод {bal} ⭐ успешно создана! Ожидайте выплату.")
        for adm in admin_ids:
            try:
                await bot.send_message(adm, f"🚨 Запрос на вывод {bal} звезд от пользователя `{uid}`!")
            except:
                pass
    else:
        await message.answer(f"❌ Минимальная сумма для вывода — 25 звезд. У вас сейчас {round(bal, 2)} ⭐.")

@dp.message(F.text == "📋 Задания")
async def tasks_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Подписаться на канал дня (+5 ⭐)", url="https://t.me/telegram")],
        [InlineKeyboardButton(text="✅ Я выполнил(а)", callback_data="claim_task")]
    ])
    await message.answer("📋 **Доступные задания:**\n\nВыполняйте задания партнеров и получайте бесплатные звезды!", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "claim_task")
async def claim_task(callback: CallbackQuery):
    uid = callback.from_user.id
    if uid in users_db:
        users_db[uid]["tickets"] += 5
    await callback.answer("🎉 Задание выполнено! Вам начислено +5 ⭐", show_alert=True)

@dp.message(F.text == "📖 Инструкция")
async def instruction(message: Message):
    await message.answer("📖 **Как зарабатывать в боте?**\n\n1. Кликайте на кнопку «Заработать звезды».\n2. Приглашайте друзей по реферальной ссылке (+3 звезды за каждого).\n3. Выполняйте задания и участвуйте в PvP.", parse_mode="Markdown")

@dp.message(F.text == "🏆 Топ")
async def top_users(message: Message):
    await message.answer("🏆 **Топ-10 пользователей за день:**\n\n1. Александр — 45 звезд\n2. Максим — 38 звезд\n3. Юрий — 30 звезд\n...\nПопадайте в топ и получайте супер-призы каждый вечер!", parse_mode="Markdown")

@dp.message(F.text == "🛒 Магазин звезд")
async def shop(message: Message):
    await message.answer("🛒 **Магазин звезд и подарков**\n\nСамые дешевые Telegram Stars и премиум-подарки специально для вас! Обращайтесь к администратору бота.", parse_mode="Markdown")

@dp.message(F.text == "🛠 Админ-панель")
async def admin_panel_btn(message: Message):
    if message.from_user.id not in admin_ids:
        return
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Пул звезд в боте", callback_data="admin_pool")],
        [InlineKeyboardButton(text="➕ Добавить спонсора", callback_data="admin_add_sponsor")],
        [InlineKeyboardButton(text="🎁 Выдать звезды юзеру", callback_data="admin_give")]
    ])
    await message.answer(f"🛠 **Панель администратора**\n\nДоступно звезд в пуле бота: **{bot_star_pool} ⭐**", reply_markup=admin_kb, parse_mode="Markdown")

@dp.callback_query(F.data == "admin_pool")
async def admin_pool_cb(callback: CallbackQuery):
    await callback.answer(f"Пул для выплат: {bot_star_pool} звезд. Пополнить: /addpool СУММА", show_alert=True)

@dp.callback_query(F.data == "admin_add_sponsor")
async def admin_add_sponsor_cb(callback: CallbackQuery):
    await callback.message.answer("Команда для добавления спонсора:\n`/addsponsor НАЗВАНИЕ ССЫЛКА`")
    await callback.answer()

@dp.callback_query(F.data == "admin_give")
async def admin_give_cb(callback: CallbackQuery):
    await callback.message.answer("Команда для выдачи звезд:\n`/give ID СУММА`")
    await callback.answer()

@dp.message(Command("addsponsor"))
async def add_sponsor_cmd(message: Message):
    if message.from_user.id not in admin_ids:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) == 3:
        name, url = parts[1], parts[2]
        sponsors.append({"name": name, "url": url})
        await message.answer(f"✅ Спонсор «{name}» успешно добавлен!")
    else:
        await message.answer("❌ Формат: `/addsponsor Название Ссылка`", parse_mode="Markdown")

@dp.message(Command("addpool"))
async def add_pool_cmd(message: Message):
    if message.from_user.id not in admin_ids:
        return
    parts = message.text.split()
    global bot_star_pool
    if len(parts) == 2 and parts[1].isdigit():
        amt = int(parts[1])
        bot_star_pool += amt
        await message.answer(f"✅ Пул пополнен на {amt} ⭐! Всего: {bot_star_pool} ⭐")
    else:
        await message.answer("❌ Формат: `/addpool СУММА`")

@dp.message(Command("give"))
async def give_stars_cmd(message: Message):
    if message.from_user.id not in admin_ids:
        return
    parts = message.text.split()
    if len(parts) == 3 and parts[1].isdigit():
        target_id = int(parts[1])
        amount = float(parts[2])
        if target_id in users_db:
            users_db[target_id]["tickets"] += amount
            await message.answer(f"✅ Пользователю `{target_id}` начислено {amount} ⭐!")
            try:
                await bot.send_message(target_id, f"🎉 Администратор пополнил ваш баланс на {amount} ⭐!")
            except:
                pass
        else:
            await message.answer("❌ Пользователь еще не запускал бота!")
    else:
        await message.answer("❌ Формат: `/give ID СУММА`")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен!")
    dp.run_polling(bot)
