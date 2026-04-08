import os, re
from PIL import Image, ImageDraw, ImageFont
from telegram import InputSticker, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import StickerFormat
from telegram.request import HTTPXRequest

TOKEN = "7454600169:AAFt_5OQrdfyZddCArLMTHdVOsmI-xitaOg"
RIGHTS_TEXT = "@AhmshY"

def process_image(in_p, out_p):
    try:
        with Image.open(in_p).convert("RGBA") as base:
            base.thumbnail((512, 512))
            overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), RIGHTS_TEXT, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pos = (base.width - tw - 15, base.height - th - 15)
            draw.rectangle([pos[0]-4, pos[1]-4, pos[0]+tw+4, pos[1]+th+4], fill=(0, 0, 0, 80))
            draw.text(pos, RIGHTS_TEXT, fill=(255, 255, 255, 255), font=font)
            Image.alpha_composite(base, overlay).convert("RGB").save(out_p, "WEBP")
            return True
    except: return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    
    # استخراج اسم الحزمة من الرابط باستخدام Regex
    match = re.search(r"addstickers/(.+)", text)
    if not match:
        await update.message.reply_text("⚠️ من فضلك أرسل رابط حزمة ملصقات صحيح.")
        return

    pack_short_name = match.group(1)
    status_msg = await update.message.reply_text("🔄 جاري فحص الحزمة وبدء المعالجة...")

    try:
        # جلب بيانات الحزمة الأصلية
        sticker_set = await context.bot.get_sticker_set(pack_short_name)
        bot_info = await context.bot.get_me()
        new_pack_name = f"stk_{user_id}_{pack_short_name[:10]}_by_{bot_info.username}"
        
        count = 0
        total = len(sticker_set.stickers)
        
        for sticker in sticker_set.stickers:
            if sticker.is_animated or sticker.is_video: continue # تخطي المتحرك
            
            file = await context.bot.get_file(sticker.file_id)
            await file.download_to_drive("temp_in.webp")
            
            if process_image("temp_in.webp", "temp_out.webp"):
                with open("temp_out.webp", "rb") as f
