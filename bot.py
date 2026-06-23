import asyncio
import json
import os
from datetime import datetime, time, timedelta

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    BotCommandScopeChat,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)

TOKEN = os.getenv(
    "TOKEN",
    "8923490745:AAEPaZgP9MeFAKUVyrhHZ0jRIPI9mw_yCQ0"
)
CHAT_ID = -1003995302468

NAME, CONTACT, ADDRESS_TYPE, ADDRESS, PRODUCT, TIME, CONFIRM = range(7)

cancel_keyboard = ReplyKeyboardMarkup(
    [["🚫 Скасувати замовлення"]],
    resize_keyboard=True
)

address_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(
            "📍 Надіслати геолокацію",
            request_location=True
        )],
        ["✍️ Ввести адресу вручну"],
        ["🚫 Скасувати замовлення"]
    ],
    resize_keyboard=True
)

contact_keyboard = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton(
                "📞 Поділитися номером",
                request_contact=True
            )
        ],
        ["🚫 Скасувати замовлення"]
    ],
    resize_keyboard=True
)

main_keyboard = ReplyKeyboardMarkup(
    [["🟢 Start", "🛒 Замовити"]],
    resize_keyboard=True
)

main_keyboard = ReplyKeyboardMarkup(
    [["🟢 Start", "🛒 Замовити"]],
    resize_keyboard=True
)

GROUP_KEYBOARD = ReplyKeyboardMarkup(
    [["🚫 Чорний список"]],
    resize_keyboard=True
)

ORDERS_FILE = "orders.json"
BOOKING_FILE = "booked_slots.json"
BLACKLIST_FILE = "blacklist.json"

WORK_START = time(12, 0)
WORK_END = time(20, 0)
STEP_MINUTES = 15


def load_bookings():
    if not os.path.exists(BOOKING_FILE):
        return {}

    try:
        with open(BOOKING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_bookings(data):
    with open(BOOKING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return []

    try:
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_blacklist(data):
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def show_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):

    blacklist = load_blacklist()

    if not blacklist:
        await update.message.reply_text(
            "✅ Чорний список порожній."
        )
        return

    text = "🚫 ЧОРНИЙ СПИСОК\n\n"
    buttons = []

    for user in blacklist:

        username = user.get("username")

        if username and username != "none":
            text += (
                f"👤 @{username}\n"
                f"🆔 {user['id']}\n\n"
            )
        else:
            text += (
                f"👤 {user['name']}\n"
                f"🆔 {user['id']}\n\n"
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    f"✅ Розбанити {user['name']}",
                    callback_data=f"unban_{user['id']}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "⬅️ Закрити",
                callback_data="close_blacklist"
            )
        ]
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def unban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()


    user_id = int(
        query.data.replace("unban_", "")
    )


    blacklist = load_blacklist()


    for user in blacklist:

        if user["id"] == user_id:

            blacklist.remove(user)

            save_blacklist(blacklist)


            await query.edit_message_text(
                f"✅ {user['name']} розблокований."
            )

            return


    await query.edit_message_text(
        "❌ Користувача вже немає у чорному списку."
    )


def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return {}

    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_orders(data):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return {}

    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_orders(data):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_available_slots():

    now = datetime.now()

    bookings = load_bookings()

    today = datetime.now().strftime("%Y-%m-%d")

    booked = bookings.get(today, [])

    slots = []

    current = datetime.combine(
        now.date(),
        WORK_START
    )

    end = datetime.combine(
        now.date(),
        WORK_END
    )

    while current <= end:

        slot = current.strftime("%H:%M")

        if current > now and slot not in booked:
            slots.append(slot)

        current += timedelta(
            minutes=STEP_MINUTES
        )

    return slots


def generate_time_keyboard():
    available_slots = get_available_slots()

    keyboard = []
    row = []

    for slot in available_slots:
        row.append(slot)

        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append(["🚫 Скасувати замовлення"])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Вітаємо в NeonPods!",
        reply_markup=main_keyboard
    )



async def check_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🚫 Скасувати замовлення":
        await update.message.reply_text(
            "❌ Замовлення скасовано.",
            reply_markup=main_keyboard
        )
        return True

    return False

async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    blacklist = load_blacklist()

    for user in blacklist:

        if user["id"] == user_id:

            await update.message.reply_text(
                "🚫 Ви заблоковані."
            )

            return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text(
    "👤 Введіть ваше ім'я:",
    reply_markup=cancel_keyboard
)

    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if await check_cancel(update, context):
        return ConversationHandler.END

    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "📞 Натисніть кнопку нижче:",
        reply_markup=contact_keyboard
    )

    return CONTACT

async def get_contact_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    contact = update.message.contact

    context.user_data["phone"] = contact.phone_number
    context.user_data["contact"] = contact.phone_number

    await update.message.reply_text(
        "📍 Як вказати адресу?",
        reply_markup=address_keyboard
    )

    return ADDRESS_TYPE


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if await check_cancel(update, context):
        return ConversationHandler.END

    context.user_data["contact"] = update.message.text

    await update.message.reply_text(
        "📍 Як вказати адресу?",
        reply_markup=address_keyboard
    )

    return ADDRESS_TYPE

async def choose_address_type(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "✍️ Ввести адресу вручну":
        await update.message.reply_text(
            "📍 Введіть адресу доставки:",
            reply_markup=cancel_keyboard
        )
        return ADDRESS

    if text == "📍 Надіслати геолокацію":
        await update.message.reply_text(
            "📍 Натисніть кнопку геолокації внизу та відправте місцезнаходження."
        )
        return ADDRESS_TYPE

    return ADDRESS_TYPE


async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):

    location = update.message.location

    context.user_data["address"] = "📍 Геолокація"
    context.user_data["lat"] = location.latitude
    context.user_data["lon"] = location.longitude

    await update.message.reply_text(
        "🛒 Вкажіть товар:",
        reply_markup=cancel_keyboard
    )

    return PRODUCT


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if await check_cancel(update, context):
        return ConversationHandler.END

    context.user_data["address"] = update.message.text

    await update.message.reply_text(
    "🛒 Вкажіть товар:",
    reply_markup=cancel_keyboard
)

    return PRODUCT


async def get_product(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if await check_cancel(update, context):
        return ConversationHandler.END

    context.user_data["product"] = update.message.text

    await update.message.reply_text(
        "🕒 Оберіть час доставки:",
        reply_markup=generate_time_keyboard()
    )

    return TIME


async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print("GET_TIME:", update.message.text)

    if await check_cancel(update, context):
        return ConversationHandler.END

    chosen_time = update.message.text

    available_slots = get_available_slots()

    if chosen_time not in available_slots:
        await update.message.reply_text(
            "❌ Будь ласка, оберіть час кнопкою.",
            reply_markup=generate_time_keyboard()
        )
        return TIME

    context.user_data["time"] = chosen_time    
    
    confirm_keyboard = ReplyKeyboardMarkup(
        [["✅ Підтвердити", "❌ Скасувати"]],
        resize_keyboard=True
    )

    text = f"""
📋 ПЕРЕВІРТЕ ЗАМОВЛЕННЯ

👤 Ім'я: {context.user_data['name']}
📞 Контакт: {context.user_data['contact']}
📍 Адреса: {context.user_data['address']}
🛒 Товар: {context.user_data['product']}
🕒 Час: {context.user_data['time']}
"""

    await update.message.reply_text(
        text,
        reply_markup=confirm_keyboard
    )

    return CONFIRM

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text

    if answer == "❌ Скасувати":
        await update.message.reply_text(
            "❌ Замовлення скасовано.",
            reply_markup=main_keyboard
        )
        return ConversationHandler.END

    if answer == "✅ Підтвердити":

        bookings = load_bookings()
        today = datetime.now().strftime("%Y-%m-%d")

        if today not in bookings:
            bookings[today] = []

        if context.user_data["time"] not in bookings[today]:
            bookings[today].append(
                context.user_data["time"]
            )

        save_bookings(bookings)

        order_text = f"""
🔥 НОВЕ ЗАМОВЛЕННЯ NEONPODS

👤 Ім'я: {context.user_data['name']}
📞 Контакт: {context.user_data.get('phone', context.user_data['contact'])}
🔗 Нік: @{update.effective_user.username or 'немає'}

🛒 Товар: {context.user_data['product']}
📍 Адреса: {context.user_data['address']}
🕒 Час: {context.user_data['time']}
"""

        cancel_button = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "❌ Скасувати",
            callback_data=f"cancel_{context.user_data['time']}"
        ),
        InlineKeyboardButton(
            "🚫 Бан",
            callback_data=f"ban|{update.effective_user.id}|{context.user_data['name']}|{update.effective_user.username or 'none'}"
        )
    ]
])

        sent_message = await context.bot.send_message(
            chat_id=CHAT_ID,
            text=order_text,
            reply_markup=cancel_button
        )

        orders = load_orders()

        user_id = str(update.effective_user.id)

        if user_id not in orders:
            orders[user_id] = []

        orders[user_id].append({
            "message_id": sent_message.message_id,
            "slot": context.user_data["time"],
            "name": context.user_data["name"],
            "username": update.effective_user.username,
            "customer_id": update.effective_user.id
        })

        save_orders(orders)

        if "lat" in context.user_data:
            await context.bot.send_location(
            chat_id=CHAT_ID,
            latitude=context.user_data["lat"],
            longitude=context.user_data["lon"]
        )

        await update.message.reply_text(
            "✅ Замовлення прийнято!\nМенеджер скоро зв'яжеться з вами.",
            reply_markup=main_keyboard
        )

        return ConversationHandler.END

    return CONFIRM


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Замовлення скасовано.",
        reply_markup=main_keyboard
    )

    return ConversationHandler.END

async def cancel_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    slot = query.data.replace("cancel_", "")

    bookings = load_bookings()
    today = datetime.now().strftime("%Y-%m-%d")

    if today in bookings:
        if slot in bookings[today]:
            bookings[today].remove(slot)
            save_bookings(bookings)

    orders = load_orders()

    for user_id, user_orders in orders.items():

        for order in user_orders:

            if order["slot"] == slot:

                try:
                    await context.bot.send_message(
                        chat_id=order["customer_id"],
                        text="❌ Ваше замовлення було скасовано адміністратором."
                    )
                except:
                    pass

                break

    await query.message.delete()

async def ban_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split("|")

    user_id = data[1]
    name = data[2]
    username = data[3]

    blacklist = load_blacklist()
    orders = load_orders()

    exists = False

    for user in blacklist:
        if user["id"] == int(user_id):
            exists = True

    if not exists:
        blacklist.append({
            "id": int(user_id),
            "name": name,
            "username": username
        })

        save_blacklist(blacklist)

    if user_id in orders:

        bookings = load_bookings()
        today = get_today()

        for order in orders[user_id]:

            try:
                await context.bot.delete_message(
                    chat_id=CHAT_ID,
                    message_id=order["message_id"]
                )
            except:
                pass

            slot = order["slot"]

            if today in bookings:
                if slot in bookings[today]:
                    bookings[today].remove(slot)

        save_bookings(bookings)

        del orders[user_id]
        save_orders(orders)

    await query.message.reply_text(
        f"🚫 @{username} заблоковано."
    )

async def setup_group_commands(app):

    await app.bot.set_my_commands(
        [
            ("blacklist", "🚫 Чорний список")
        ],
        scope=BotCommandScopeChat(
            chat_id=CHAT_ID
        )
    )

async def group_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🔧 Меню групи активоване",
        reply_markup=GROUP_KEYBOARD
    )

async def close_blacklist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    await query.message.delete()

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^🛒 Замовити$"),
                order_start
            )
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CONTACT: [
                MessageHandler(filters.CONTACT, get_contact_button),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)
            ],
            ADDRESS_TYPE: [
                MessageHandler(filters.LOCATION, get_location),
                MessageHandler(filters.TEXT, choose_address_type),
            ],
            ADDRESS: [
                MessageHandler(filters.TEXT, get_address)
            ],
            PRODUCT: [
                MessageHandler(filters.TEXT, get_product)
            ],
            TIME: [
                MessageHandler(filters.ALL, get_time)
            ],
            CONFIRM: [
                MessageHandler(filters.ALL, confirm_order)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", group_menu))
    app.add_handler(conv)

    app.add_handler(
        CallbackQueryHandler(
            cancel_order_callback,
            pattern="^cancel_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            ban_user_callback,
            pattern="^ban"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            unban_callback,
            pattern="^unban_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            close_blacklist_callback,
            pattern="^close_blacklist$"
        )
    )

    app.add_handler(
        CommandHandler(
            "blacklist",
            show_blacklist
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex("^🚫 Чорний список$"),
            show_blacklist
        )
    )

    print("NeonPods Bot запущено 🚀")

    app.run_polling()


if __name__ == "__main__":
    main()