import os
import re
import threading
from flask import Flask
from PIL import Image, ImageDraw, ImageFont
from telegram import InputSticker, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import StickerFormat
from telegram.request import HTTPXRequest

# إعدادات البوت الأساسية
TOKEN = "7454600169:AAFt_5OQrdfyZddCArLMTHdVOsmI-xitaOg"
RIGHTS_TEXT = "@AhmshY"

# إعداد سيرفر الويب المصغر ليتوافق مع منصة Render
app = Flask(__name__)

@app.route( / )
def home():
    return "Bot is Running Securely!"

def run_web_server():
    port = int(os.environ.get( PORT , 8080))
    app.run(host= 0.0.0.0 , port=port)

# دالة معالجة الصور وإضافة الحقوق
def process_image(in_path, out_path):
    try:
        with Image.open(in_path).convert("RGBA") as base:
            base.thumbnail((512, 512))
            overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            font = ImageFont.load_default()
            
            # حساب أبعاد النص لتحديد موقعه
            bbox = draw.textbbox((0, 0), RIGHTS_TEXT, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            
            # تحديد الموقع في الزاوية السفلية اليمنى
            pos = (base.width - tw - 15, base.height - th - 15)
            
            # رسم خلفية شبه شفافة للنص لضمان وضوحه
            draw.rectangle([pos[0]-4, pos[1]-4, pos[0]+tw+4, pos[1]+th+4], fill=(0, 0, 0, 80))
            
            # كتابة النص الخاص بالحقوق
            draw.text(pos, RIGHTS_TEXT, fill=(255, 255, 255, 255), font=font)
            
            # دمج الطبقات وحفظ الصورة بصيغة WEBP
            Image.alpha_composite(base, overlay).convert("RGB").save(out_path, "WEBP")
            return True
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

# دالة معالجة الرسائل الواردة (روابط الحزم)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return
        
    user_id = update.message.from_user.id
    
    # التحقق من صحة رابط حزمة الملصقات
    match = re.search(r"addstickers/(.+)", text)
    if not match:
        await update.message.reply_text("⚠️ الرجاء إرسال رابط حزمة ملصقات صحيح.")
        return

    pack_short_name = match.group(1)
    status_msg = await update.message.reply_text("🔄 جاري فحص الحزمة وبدء المعالجة، يرجى الانتظار...")

    try:
        # جلب بيانات الحزمة الأصلية
        sticker_set = await context.bot.get_sticker_set(pack_short_name)
        bot_info = await context.bot.get_me()
        
        # إنشاء اسم فريد للحزمة الجديدة لتجنب التكرار
        new_pack_name = f"stk_{user_id}_{pack_short_name[:10]}_by_{bot_info.username}"
        
        count = 0
        total = len(sticker_set.stickers)
        
        for sticker in sticker_set.stickers:
            # تخطي الملصقات المتحركة والفيديو
            if sticker.is_animated or sticker.is_video: 
                continue
                
            # تحميل الملصق
            file = await context.bot.get_file(sticker.file_id)
            await file.download_to_drive("temp_in.webp")
            
            # معالجة الملصق وإضافة الحقوق
            if process_image("temp_in.webp", "temp_out.webp"):
                with open("temp_out.webp", "rb") as f:
                    s_input = InputSticker(f, [sticker.emoji or "✨"], format=StickerFormat.STATIC)
                    
                    try:
                        # محاولة إضافة الملصق للحزمة إذا كانت موجودة مسبقاً
                        await context.bot.add_sticker_to_set(user_id=user_id, name=new_pack_name, sticker=s_input)
                    except Exception:
                        # إذا لم تكن موجودة، يتم إنشاء حزمة جديدة
                        await context.bot.create_new_sticker_set(
                            user_id=user_id, 
                            name=new_pack_name, 
                            title=f"حقوق {RIGHTS_TEXT}", 
                            stickers=[s_input]
                        )
                count += 1
                
                # تحديث رسالة الحالة كل 10 ملصقات
                if count % 10 == 0:
                    await status_msg.edit_text(f"⏳ تمت معالجة {count} من أصل {total} ملصق...")

        # إرسال رابط الحزمة الجديدة للمستخدم
        await status_msg.edit_text(f"✅ اكتملت المعالجة بنجاح!\nتم تعديل {count} ملصق.\nالرابط: https://t.me/addstickers/{new_pack_name}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء المعالجة: {str(e)}")
    finally:
        # تنظيف الملفات المؤقتة لتوفير المساحة
        for t in ["temp_in.webp", "temp_out.webp"]:
            if os.path.exists(t): 
                os.remove(t)

if __name__ ==  __main__ :
    # 1. تشغيل سيرفر الويب في الخلفية
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # 2. إعداد وتشغيل بوت التليجرام
    req = HTTPXRequest(connect_timeout=60.0, read_timeout=60.0)
    application = Application.builder().token(TOKEN).request(req).build()
    
    # استقبال الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("--- البوت والسيرفر يعملان بنجاح ---")
    
    # بدء تشغيل البوت
    application.run_polling(drop_pending_updates=True)
