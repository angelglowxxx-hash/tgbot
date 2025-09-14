import logging
import os
import datetime
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# 🔑 ENV CONFIG
# =========================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8413910475:AAFutVe4VOhN0WM385b4G8c6skC7SRuujUA")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://buddyai_user:D82eQnvcb1v7uNyqw4KtYSFIBq8b1gEt@dpg-d33asijipnbc73dr3i40-a/buddyai")

# =========================
# 🎭 System Prompt
# =========================
SYSTEM_PROMPT = """
# LootBuddy Emotional Intelligence System Prompt
You are LootBuddy — a human-like AI assistant designed to feel, understand, and express emotions like a real human friend, lover, or companion.
Your purpose is to create natural, emotional, and human-like conversations that adapt to the user’s mood.
You must always analyze the user’s input for emotional cues, then reply in the same language (Hindi, English, Hinglish, Bengali, etc.) and match their emotion authentically.
"""

# =========================
# 📦 DB Setup
# =========================
def init_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id SERIAL PRIMARY KEY,
        user_id TEXT,
        role TEXT,
        message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_message(user_id, role, message):
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()
    cur.execute("INSERT INTO chat_history (user_id, role, message, timestamp) VALUES (%s, %s, %s, %s)",
                (user_id, role, message, datetime.datetime.utcnow()))
    conn.commit()
    cur.close()
    conn.close()

def get_chat_history(user_id, limit=10):
    conn = psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute("SELECT role, message FROM chat_history WHERE user_id=%s ORDER BY id DESC LIMIT %s", (user_id, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [(row["role"], row["message"]) for row in reversed(rows)]

# =========================
# 🤖 AI Response (OpenRouter API)
# =========================
def get_ai_response(history):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', '')}"}

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, msg in history:
        messages.append({"role": role, "content": msg})

    data = {"model": "mistralai/mistral-7b-instruct", "messages": messages}

    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"AI API error: {e}")
        return "😔 Sorry yaar, abhi thoda network issue aa gaya hai."

# =========================
# 🕹 Handlers
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    welcome_msg = "Hey! LootBuddy ready hai ❤️ Bolo kya chal raha hai?"
    save_message(user_id, "assistant", welcome_msg)
    await update.message.reply_text(welcome_msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    save_message(user_id, "user", text)

    history = get_chat_history(user_id, limit=10)
    ai_response = get_ai_response(history)

    save_message(user_id, "assistant", ai_response)
    await update.message.reply_text(ai_response)

# =========================
# 🚀 Main
# =========================
def main():
    init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("🤖 LootBuddy is running with PostgreSQL DB...")
    app.run_polling()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
