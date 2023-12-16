import asyncio
import os
import google.generativeai as genai

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, Application
from telegram.constants import ChatAction
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


model = genai.GenerativeModel('gemini-pro')

chats: dict[int, genai.ChatSession] = {}


async def new_chat(chat_id: int):
    chats[chat_id] = model.start_chat()

async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        # reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text ="""
Basic commands:
/start - Start the bot
/help - Get help. Shows this message

Chat commands:
/new - Start a new chat session (model will forget previously generated messages)

Send a message to the bot to generate a response.
"""
    await update.message.reply_text(help_text)
    

async def newchat_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a new chat session."""
    init_msg = await update.message.reply_text(text="Starting new chat session...", reply_to_message_id=update.message.message_id)
    await new_chat(update.message.chat.id)
    await init_msg.edit_text("New chat session started.")
    

# Define the function that will handle incoming messages
async def handle_message(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id not in chats:
        await new_chat(update.message.chat.id)
    text = update.message.text
    init_msg = await update.message.reply_text(text="Generating...", reply_to_message_id=update.message.message_id)
    inited = True
    await update.message.chat.send_action(ChatAction.TYPING)
    # Generate a response using the text-generation pipeline
    chat = chats[update.message.chat.id] # Get the chat session for this chat
    response = await chat.send_message_async(text, stream=True) # Generate a response

    # Stream the responses
    async for chunk in response:
        try:
            if chunk.text:
                message = chunk.text
                if inited:
                    inited = False
                    init_msg = await init_msg.edit_text(text=message)
                else:
                    init_msg = await init_msg.edit_text(text=init_msg.text + message)
        except IndexError:
            if inited:
                await init_msg.edit_text("The bot could not generate a response. Please start a new chat with /new")
            else:
                await init_msg.reply_text("The bot could not generate a response. Please start a new chat with /new")
            continue
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
    application.add_handler(CommandHandler("new", newchat_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()