import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from transformers import pipeline

# Logging
logging.basicConfig(level=logging.INFO)

# Load free HuggingFace model (distilgpt2)
chatbot = pipeline("text-generation", model="distilgpt2")

# Telegram Bot Token (set in Render Environment Variable)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# System prompt (ChatGPT style personality)
SYSTEM_PROMPT = """You are LootBuddy AI 🤖. 
You reply in a natural, friendly, human-like way. 
Act like ChatGPT: explain clearly, keep conversation flowing, and never refuse normal questions.
"""

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 LootBuddy AI here! Ask me anything...")

# Chat handler
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    logging.info(f"User said: {user_input}")

    # Generate response
    raw_response = chatbot(SYSTEM_PROMPT + "\nUser: " + user_input + "\nAI:", 
                           max_length=150, 
                           num_return_sequences=1, 
                           pad_token_id=50256)[0]["generated_text"]

    # Clean response
    cleaned = raw_response.split("AI:")[-1].strip()
    if cleaned.startswith(user_input):
        cleaned = cleaned[len(user_input):].strip()

    # Safety fallback
    if not cleaned:
        cleaned = "Hmm... interesting! Tell me more 🙂"

    await update.message.reply_text(cleaned)

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN not set in environment!")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logging.info("🤖 LootBuddy bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
