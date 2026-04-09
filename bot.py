import os, asyncio, threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# إعدادات البوت
TOKEN = "7454600169:AAFt_5OQrdfyZddCArLMTHdVOsmI-xitaOg"

# --- سيرفر ويب بسيط لـ Render ---
app = Flask(__name__)

@app.route( / )
def home():
    return "Bot is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- معالجة الرسائل ---
async def start_handler(update: Update, context):
    await update.message.reply_text("أهلاً خالد! البوت يعمل الآن بنجاح.")

async def main():
    # تشغيل Flask في الخلفية
    threading.Thread(target=run_flask, daemon=True).start()
    
    # بناء البوت
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT, start_handler))
    
    # بدء البوت
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        # إبقاء البوت يعمل للأبد
        while True:
            await asyncio.sleep(3600)

if __name__ ==  __main__ :
    asyncio.run(main())
