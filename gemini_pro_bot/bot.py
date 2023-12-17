import os
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    Application,
)
from dotenv import load_dotenv
from gemini_pro_bot.handlers import (
    start,
    help_command,
    newchat_command,
    handle_message,
    handle_image,
)

load_dotenv()


def start_bot() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new", newchat_command))

    # Any text message is sent to LLM to generate a response
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Any image is sent to LLM to generate a response
    application.add_handler(
        MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_image)
    )
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
