from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import re

CHOOSING, FORMATTING = range(2)

reply_keyboard = [
    ["📲 Telegram Link", "💬 WhatsApp Link"],
    ["➕ Add +", "🔙 Back"]
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

# ✅ Updated number cleaner
def clean_number(text: str) -> str:
    digits = re.sub(r'\D', '', text)

    if text.startswith('+'):
        return '+' + digits
    elif text.startswith('00'):
        return '+' + digits[2:]
    elif digits.startswith('0'):
        return None  # likely local number, reject
    else:
        return '+' + digits  # assume full international format like 254...

def is_valid_number(number: str) -> bool:
    digits = re.sub(r'\D', '', number)
    return 8 <= len(digits) <= 15

def extract_numbers(text: str) -> list:
    possible = re.split(r'[,\n\s]+', text)
    valid = []
    for item in possible:
        cleaned = clean_number(item)
        if cleaned and is_valid_number(cleaned):
            valid.append(cleaned)
    return valid

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me one or more international phone numbers (separated by comma, space or new lines).",
        reply_markup=ReplyKeyboardRemove()
    )
    return CHOOSING

async def handle_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    numbers = extract_numbers(user_input)

    if not numbers:
        await update.message.reply_text("⚠️ No valid international numbers found. Please try again.")
        return CHOOSING

    context.user_data['numbers'] = numbers

    await update.message.reply_text(
        f"✅ Found {len(numbers)} valid number(s).\nChoose what you want:",
        reply_markup=markup
    )
    return FORMATTING

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    numbers = context.user_data.get('numbers', [])

    if not numbers:
        await update.message.reply_text("⚠️ No numbers stored. Please send them again.", reply_markup=ReplyKeyboardRemove())
        return CHOOSING

    result_lines = []
    for i, num in enumerate(numbers):
        raw = num.lstrip('+')
        if choice == "📲 Telegram Link":
            result_lines.append(f"{i+1}. https://t.me/+{raw}")
        elif choice == "💬 WhatsApp Link":
            result_lines.append(f"{i+1}. https://wa.me/{raw}")
        elif choice == "➕ Add +":
            result_lines.append(f"{i+1}. +{raw}")
        elif choice == "🔙 Back":
            await update.message.reply_text("🔄 Send new number(s):", reply_markup=ReplyKeyboardRemove())
            return CHOOSING

    result_text = "\n".join(result_lines)
    chunk_size = 4000
    for i in range(0, len(result_text), chunk_size):
        await update.message.reply_text(result_text[i:i+chunk_size])

    await update.message.reply_text("✅ Done!", reply_markup=ReplyKeyboardRemove())
    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Cancelled. Send /start to try again.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

if __name__ == '__main__':
    TOKEN = "7253108927:AAES6AUdEIExh28f4PsTJF9ILEhSvdyvIoQ"

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_numbers)],
            FORMATTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
