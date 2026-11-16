"""Register the webhook URL and its secret token on Telegram. Run once on the hosting after the web app is up."""

import os
import asyncio
from telegram import Bot, Update
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HOSTING_USERNAME = os.environ.get('HOSTING_USERNAME')  # not USERNAME: on Windows that is the login name
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
WEBHOOK_URL = f"https://{HOSTING_USERNAME}.pythonanywhere.com/webhook"

async def main():
    """Tell Telegram to send only message updates to WEBHOOK_URL with WEBHOOK_SECRET (as in polling mode)."""
    bot = Bot(token=BOT_TOKEN)
    await bot.set_webhook(url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET, allowed_updates=[Update.MESSAGE])
    print(f"Webhook impostato con successo su: {WEBHOOK_URL}")

if __name__ == '__main__':
    asyncio.run(main())