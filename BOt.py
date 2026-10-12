import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Message, CallbackQuery
from aiohttp import web

TOKEN = "8647123805:AAHu13g0TsMEkOLvtvcavx4UisNCERVSOrM"
ADMIN_ID = 6700507253

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База даних у пам'яті (зберігає рефералів, баланс, нікнейми)
users_db = {}

# Красивий Web App інтерфейс (меню зірок)
WEB_PAGE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Патрік Stars Меню</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #121c24; color: #fff; padding: 15px; text-align: center; margin: 0; }
        .card { background: rgba(255,255,255,0.06); padding: 18px; border-radius: 16px; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.1); }
        input { width: 100%; padding: 12px; margin: 8px 0; border-radius: 10px; border: 1px solid #444; background: #1a2733; color: #fff; box-sizing: border-box; font-size: 16px; }
        button { background: #2ea6ff; color: #fff; border: none; width: 100%; padding: 12px; border-radius: 10px; font-weight: bold; cursor: pointer; font-size: 16px; margin-top: 5px; }
        button:active { background: #1b8ad8; }
        .balance { font-size: 28px; color: #ffd700; font-weight: bold; margin: 5px 0; }
        .ref-box { background: #1a2733; padding: 10px; border-radius: 8px; font-size: 14px; word-break: break-all; color: #2ea6ff; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>👤 Ваш профіль</h2>
        <input type="text" id="nick" placeholder="Введіть ваш нікнейм">
        <button onclick="saveNick()">Зберегти нік</button>
    </div>
    
    <div class="card">
        <h2>⭐ Ваш баланс</h2>
        <div class="balance"><span id="tickets">0</span> 🎫</div>
        <p style="font-size: 13px; color: #aaa;">1 білет = 1 зірка (мін. виведення: 25)</p>
        <button onclick="exchange()" style="background: #27ae60;">Вивести зірки 🚀</button>
    </div>

    <div class="card">
        <h2>👥 Запросити друга</h2>
        <p style="font-size: 13px; color: #aaa;">Отримуйте по 3 зірки за кожного друга!</p>
        <div class="ref-box" id="refLink">Генерується...</div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();
        const userId = tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : 12345;
        const username = tg.initDataUnsafe.user ? tg.initDataUnsafe.user.username : "user";
        
        document.getElementById('refLink').innerText = `https://t.me/StarsGiveKway_bot?start=${userId}`;

        function saveNick() {
            let nick = document.getElementById('nick').value;
            fetch('/api/save', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({user_id: userId, nickname: nick})})
            .then(() => alert("✅ Нік успішно збережено!"));
        }

        function exchange() {
            fetch('/api/exchange', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({user_id: userId})})
            .then(res => res.json()).then(data => {
                if(data.success) {
                    document.getElementById('tickets').innerText = 0;
                    alert("🎉 Заявка на виведення успішно надіслана адміністратору!");
                } else {
                    alert("❌ Потрібно мінімум 25 білетів для виведення!");
                }
            });
        }

        fetch(`/api/get?user_id=${userId}`).then(res => res.json()).then(data => {
            if(data.tickets !== undefined) document.getElementById('tickets').innerText = data.tickets;
            if(data.nickname) document.getElementById('nick').value = data.nickname;
        });
    </script>
</body>
</html>
"""

async def index(request):
    return web.Response(text=WEB_PAGE, content_type='text/html')

async def api_get(request):
    uid = int(request.rel_url.query.get('user_id', 0))
    if uid not in users_db:
        users_db[uid] = {"nickname": "", "tickets": 10, "invited": 0}
    return web.json_response(users_db[uid])

async def api_save(request):
    data = await request.json()
    uid = data['user_id']
    if uid in users_db:
        users_db[uid]['nickname'] = data['nickname']
    return web.json_response({"ok": True})

async def api_exchange(request):
    data = await request.json()
    uid = data['user_id']
    if uid in users_db and users_db[uid]["tickets"] >= 25:
        t = users_db[uid]["tickets"]
        users_db[uid]["tickets"] = 0
        await bot.send_message(ADMIN_ID, f"🚨 **Запит на виведення зірок!**\nКористувач ID: `{uid}`\nСума: {t} білетів/зірок.")
        return web.json_response({"success": True})
    return web.json_response({"success": False})

@dp.message(Command("start"))
async def start(message: Message):
    uid = message.from_user.id
    
    # Обробка рефералки (якщо зайшов за посиланням друга)
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != uid and referrer_id in users_db:
            users_db[referrer_id]["tickets"] += 3  # Нараховуємо 3 зірки запрошуючому
            try:
                await bot.send_message(referrer_id, "🎉 За залученого друга вам нараховано +3 зірки! ⭐")
            except:
                pass

    if uid not in users_db:
        users_db[uid] = {"nickname": message.from_user.full_name, "tickets": 10, "invited": 0}

    webapp_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8080")
    
    # Створюємо клавіатуру із спонсорами та кнопкою перевірки (як у Патріка)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Підписатися", url="https://t.me/durov"), InlineKeyboardButton(text="📢 Підписатися", url="https://t.me/telegram")],
        [InlineKeyboardButton(text="📢 Підписатися", url="https://t.me/telegram")],
        [InlineKeyboardButton(text="✅ Провірити підписку", callback_data="check_sub")]
    ])
    
    text = (
        "💕 **Спасибо, что ты вернулся** \n\n"
        "✨ **ПОЛУЧАЙ ПО 3 ЗВЕЗДЫ ЗА ДРУГА И ИГРАЙ В PvP** ⭐\n\n"
        "Получай звезды за клики, задания и приглашенных друзей, выигрывай в PvP и участвуй в конкурсах 🎅.\n\n"
        "**Чтобы повторно активировать бота и получить 1 ⭐:**\n"
        "1️⃣ Подпишись на наших спонсоров (это займет 5 секунд)\n"
        "2️⃣ Нажми «Проверить подписку ✅»"
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery):
    webapp_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8080")
    
    # Кнопка відкриття Web App меню (як «Меню» внизу на скріншоті)
    menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Відкрити Меню Зірок", web_app=WebAppInfo(url=webapp_url))]
    ])
    
    await callback.message.edit_text(
        "✅ **Підписку успішно перевірено!**\n\nТвій подарунок зараховано. Тисни кнопку нижче, щоб відкрити головне меню та забрати зірки:",
        reply_markup=menu_keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def main():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/api/get', api_get)
    app.router.add_post('/api/save', api_save)
    app.router.add_post('/api/exchange', api_exchange)
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    await site.start()
    logging.info(f"Web server started on port {port}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
