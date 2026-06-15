from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = "8923490745:AAGvBq3ZYA85JqG9Kb9N0gk6ab9dWrKjlDQ"
CHAT_ID = -1003995302468

# стани форми
NAME, CONTACT, ADDRESS, TIME, PRODUCT = range(5)

user_data = {}


# 🔘 КНОПКИ
keyboard = ReplyKeyboardMarkup(
    [["🟢 Start", "🛒 Замовити"]],
    resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Вітаємо в NeonPods!",
        reply_markup=keyboard
    )


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🟢 Start":
        await update.message.reply_text("Бот працює ✅ Обери 'Замовити' щоб оформити заявку")

    elif text == "🛒 Замовити":
        await update.message.reply_text("👋 Вітаємо в NeonPods!\n\nДля оформлення замовлення напишіть ваше ім'я:")
        return NAME

    return None


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["name"] = update.message.text
    await update.message.reply_text("📞 Вкажіть номер телефону або Telegram:")
    return CONTACT


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["contact"] = update.message.text
    await update.message.reply_text("📍 Вкажіть адресу доставки:")
    return ADDRESS


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["address"] = update.message.text
    await update.message.reply_text("🕒 На котру годину потрібна доставка?")
    return TIME


async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["time"] = update.message.text
    await update.message.reply_text("🛒 Вкажіть товар:")
    return PRODUCT


async def get_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["product"] = update.message.text

    # 🔥 повідомлення в групу
    text = f"""
🔥 НОВЕ ЗАМОВЛЕННЯ NEONPODS

👤 Ім'я: {user_data['name']}
📞 Контакт: {user_data['contact']}
🛒 Товар: {user_data['product']}
📍 Адреса: {user_data['address']}
🕒 Час: {user_data['time']}
"""

    await context.bot.send_message(chat_id=CHAT_ID, text=text)

    await update.message.reply_text(
        "✅ Дякуємо! Ваше замовлення прийнято. Менеджер скоро зв'яжеться з вами.",
        reply_markup=keyboard
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Скасовано", reply_markup=keyboard)
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🛒 Замовити$"), handle_buttons)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
            PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    print("Bot запущено 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()