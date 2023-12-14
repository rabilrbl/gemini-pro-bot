import asyncio
import os
import google.generativeai as genai

from telegram import Update, ForceReply
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, Application

from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


model = genai.GenerativeModel('gemini-pro')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        # reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")
    

# Define the function that will handle incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    init_msg = await update.message.reply_text(text="Generating...", reply_to_message_id=update.message.message_id)
    inited = True
    # Generate a response using the text-generation pipeline
    response = model.generate_content(text, stream=True)
    
    # Stream the responses
    for chunk in response:
        try:
            if chunk.text:
                message = chunk.text
                if inited:
                    inited = False
                    init_msg = await init_msg.edit_text(text=message)
                else:
                    init_msg = await init_msg.edit_text(text=init_msg.text + message)
        except Exception as e:
            print(e)
            if chunk.text:
                init_msg = await update.message.reply_text(text=chunk.text, reply_to_message_id=init_msg.message_id)
        await asyncio.sleep(0.1)
        
def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()