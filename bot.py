import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiohttp import web

TOKEN = "8647123805:AAHu13g0TsMEkOLvtvcavx4UisNCERVSOrM"
ADMIN_ID = 6700507253  # Твій правильний ID

bot = Bot(token=TOKEN)
dp = Dispatcher()
users_db = {}

# Красивий HTML/CSS сайт (меню)
WEB_PAGE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stars Menu</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body { font-family: sans-serif; background: #18222d; color: #fff; padding: 20px; text-align: center; }
        .card { background: rgba(255,255,255,0.08); padding: 20px; border-radius: 15px; margin-bottom: 15px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #555; background: #222; color: #fff; box-sizing: border-box; }
        button { background: #2ea6ff; color: #fff; border: none; width: 100%; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .balance { font-size: 26px; color: #ffd700; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>👤 Профіль</h2>
        <input type="text" id="nick" placeholder="Введи свій нікнейм">
        <button onclick="saveNick()">Зберегти</button>
    </div>
    <div class="card">
        <h2>🎁 Твій баланс</h2>
        <div class="balance"><span id="tickets">0</span> 🎫</div>
        <p>1 білет = 1 зірка (мін. виведення: 25)</p>
        <button onclick="exchange()">Вивести зірки</button>
    </div>
    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();
        const userId = tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : 12345;

        function saveNick() {
            let nick = document.getElementById('nick').value;
            fetch('/api/save', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({user_id: userId, nickname: nick})})
            .then(() => alert("Збережено!"));
        }

        function exchange() {
            fetch('/api/exchange', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({user_id: userId})})
            .then(res => res.json()).then(data => {
                if(data.success) {
                    document.getElementById('tickets').innerText = 0;
                    alert("Заявка на виведення відправлена адміну!");
                } else {
                    alert("Потрібно мінімум 25 білетів!");
                }
            });
        }

        fetch(`/api/get?user_id=${userId}`).then(res => res.json()).then(data => {
            if(data.tickets) document.getElementById('tickets').innerText = data.tickets;
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
    if uid not in users_db: users_db[uid] = {"nickname": "", "tickets": 10}
    return web.json_response(users_db[uid])

async def api_save(request):
    data = await request.json()
    if data['user_id'] in users_db: users_db[data['user_id']]['nickname'] = data['nickname']
    return web.json_response({"ok": True})

async def api_exchange(request):
    data = await request.json()
    uid = data['user_id']
    if uid in users_db and users_db[uid]["tickets"] >= 25:
        t = users_db[uid]["tickets"]
        users_db[uid]["tickets"] = 0
        await bot.send_message(ADMIN_ID, f"🚨 Запит на виведення {t} зірок від користувача ID: {uid}")
        return web.json_response({"success": True})
    return web.json_response({"success": False})

@dp.message(Command("start"))
async def start(message: types.Message):
    webapp_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8080")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Відкрити Меню Зірок", web_app=WebAppInfo(url=webapp_url))]
    ])
    await message.answer("Привіт! Натисни кнопку нижче, щоб відкрити меню:", reply_markup=kb)

async def main():
    app = web.Application()
    app.router.add.get('/', index)
    app.router.add.get('/api/get', api_get)
    app.router.add.post('/api/save', api_save)
    app.router.add.post('/api/exchange', api_exchange)
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    # Спершу запускаємо веб-сервер, щоб Render побачив відкритий порт
    await site.start()
    logging.info(f"Web server started on port {port}")
    
    # А потім запускаємо опитування бота у фоновому режимі
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
