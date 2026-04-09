import os, re, asyncio, threading
from flask import Flask
from PIL import Image, ImageDraw, ImageFont
from telegram import InputSticker, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import StickerFormat

# إعدادات البوت
TOKEN = "7454600169:AAFt_5OQrdfyZddCArLMTHdVOsmI-xitaOg"
RIGHTS_TEXT = "@AhmshY"

# --- سيرفر الويب لضمان عدم التوقف ---
app = Flask(__name__)

@app.route( / )
def home():
    return "Bot is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- وظيفة معالجة الصور ---
def process_img(in_p, out_p):
    try:
        with Image.open(in_p).convert("RGBA") as base:
            base.thumbnail((512, 512))
            overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), RIGHTS_TEXT, font=font)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            pos = (base.width - tw - 15, base.height - th - 15)
            draw.rectangle([pos[0]-4, pos[1]-4, pos[0]+tw+4, pos[1]+th+4], fill=(0,0,0,80))
            draw.text(pos, RIGHTS_TEXT, fill=(255,255,255,255), font=font)
            Image.alpha_composite(base, overlay).convert("RGB").save(out_p, "WEBP")
            return True
    except: return False

# --- معالجة الرسائل ---
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text or "addstickers/" not in update.message.text:
        return

    match = re.search(r"addstickers/(.+)", update.message.text)
    if not match: return

    pack_name = match.group(1)
    uid = update.message.from_user.id
    msg = await update.message.reply_text("🔄 جاري إضافة الحقوق للحزمة...")

    try:
        s_set = await context.bot.get_sticker_set(pack_name)
        new_name = f"stk_{uid}_{pack_name[:10]}_by_{context.bot.username}"
        
        for s in s_set.stickers:
            if s.is_animated or s.is_video: continue
            f = await context.bot.get_file(s.file_id)
            await f.download_to_drive("in.webp")
            if process_img("in.webp", "out.webp"):
                with open("out.webp", "rb") as sticker_file:
                    instk = InputSticker(sticker_file, [s.emoji or "✨"], format=StickerFormat.STATIC)
                    try:
                        await context.bot.add_sticker_to_set(user_id=uid, name=new_name, sticker=instk)
                    except:
                        await context.bot.create_new_sticker_set(user_id=uid, name=new_name, title=f"حقوق {RIGHTS_TEXT}", stickers=[instk])
        
        await msg.edit_text(f"✅ تم! الرابط:\nhttps://t.me/addstickers/{new_name}")
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)}")

# --- التشغيل الرئيسي ---
async def main():
    # تشغيل Flask في خيط منفصل
    threading.Thread(target=run_flask, daemon=True).start()
    
    # إعداد بوت تليجرام
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    async with application:
        await application.initialize()
        await application.start_polling(drop_pending_updates=True)
        # إبقاء البوت يعمل
        while True:
            await asyncio.sleep(3600)

if __name__ ==  __main__ :
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
