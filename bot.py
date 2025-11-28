import logging
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Bot tokenini o'rnating
BOT_TOKEN = "8310166615:AAGc40Zdu4OS1mUtITAH0IlItKWb9tpYfpc"

# Admin ID lar ro'yxati (bir nechta admin)
ADMIN_IDS = [7800649803, 8389368712]   # 2 ta admin qo'yilgan, xohlasang yana qo'sh

# Ma'lumotlarni saqlash uchun
DATA_FILE = "bot_data.json"

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Ma'lumotlarni yuklash
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            if "videos" not in data:
                data["videos"] = []
            return data
    except:
        return {"videos": []}

# Ma'lumotlarni saqlash
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Start komandasi
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in ADMIN_IDS:
        data = load_data()
        video_count = len(data["videos"])
        await update.message.reply_text(
            f"👋 Salom Admin!\n"
            f"📹 Video yuklash uchun video yuboring\n"
            f"📊 Jami videolar: {video_count} ta\n"
            f"🔐 Har bir video uchun alohida kod berasiz"
        )
    else:
        await update.message.reply_text("👋 Salom!\nVideo ko'rish uchun kod yuboring.")

# Video qabul qilish
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Faqat admin video yuklay oladi!")
        return
    
    video_file = update.message.video
    if video_file:

        await update.message.reply_text(
            "📹 Video qabul qilindi!\n"
            "🔐 Ushbu video uchun kodni yuboring:"
        )
        
        context.user_data["pending_video"] = {
            "file_id": video_file.file_id,
            "file_unique_id": video_file.file_unique_id,
            "file_size": video_file.file_size,
            "timestamp": datetime.now().isoformat()
        }

# Kod qabul qilish
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text
    data = load_data()

    # ADMIN KOD KIRITISH BLOKI
    if user_id in ADMIN_IDS and "pending_video" in context.user_data:
        video_data = context.user_data["pending_video"]

        for video in data["videos"]:
            if video["code"] == user_input:
                await update.message.reply_text("❌ Bu kod bor! Yangi kod yuboring.")
                return

        new_video = {
            **video_data,
            "code": user_input,
            "video_number": len(data["videos"]) + 1,
            "used_by": []
        }

        data["videos"].append(new_video)
        save_data(data)

        del context.user_data["pending_video"]

        await update.message.reply_text(
            f"✅ Video #{new_video['video_number']} saqlandi!\n"
            f"🔐 Kod: {user_input}"
        )
        return

    # Admin lekin video kutmayotgan bo'lsa
    if user_id in ADMIN_IDS:
        await update.message.reply_text("ℹ️ Avval video yuboring.")
        return

    # FOYDALANUVCHI KOD YUBORSA
    found_video = None
    for video in data["videos"]:
        if video["code"] == user_input:
            found_video = video
            break

    if found_video:
        user_info = f"{update.effective_user.first_name} (ID: {user_id})"
        if user_info not in found_video["used_by"]:
            found_video["used_by"].append(user_info)
            save_data(data)

        try:
            await update.message.reply_video(
                video=found_video["file_id"],
                caption=f"🎉 Video #{found_video['video_number']} ochildi!"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {str(e)}")
    else:
        await update.message.reply_text("❌ Noto'g'ri kod!")

# Admin uchun ro‘yxat
async def handle_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    data = load_data()

    if not data["videos"]:
        await update.message.reply_text("📹 Hozircha video yo‘q")
        return

    msg = "📋 Videolar ro'yxati:\n\n"
    for video in data["videos"]:
        msg += f"#{video['video_number']} - Kod: {video['code']}\n"
        msg += f"Foydalanganlar: {len(video['used_by'])} ta\n\n"

    await update.message.reply_text(msg)

# Boshqa xabarlar
async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        await update.message.reply_text("ℹ️ Admin: Video yuboring yoki /list bosing.")
    else:
        await update.message.reply_text("ℹ️ Video ko‘rish uchun kod yuboring.")

# Xatolik
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Xatolik:", exc_info=context.error)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    data = load_data()
    save_data(data)
    print("✅ JSON tayyor")

    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/start"), handle_start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/list"), handle_list))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    application.add_handler(MessageHandler(filters.ALL, handle_other))

    application.add_error_handler(error_handler)

    print("🤖 Bot ishga tushdi!")
    application.run_polling()

if __name__ == "__main__":
    main()
