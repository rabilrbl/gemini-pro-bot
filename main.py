import asyncio
import os
import google.generativeai as genai
from google.generativeai.types.generation_types import StopCandidateException
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, Application
from telegram.error import NetworkError, BadRequest
from telegram.constants import ChatAction, ParseMode
from html_format import format_message
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
    await update.message.chat.send_action(ChatAction.TYPING)
    # Generate a response using the text-generation pipeline
    chat = chats[update.message.chat.id] # Get the chat session for this chat
    response = None
    try:
        response = await chat.send_message_async(text, stream=True) # Generate a response
    except StopCandidateException as sce:
        await init_msg.edit_text("The model unexpectedly stopped generating.")
        chat.rewind() # Rewind the chat session to prevent the bot from getting stuck
        return
    full_plain_message = ""
    # Stream the responses
    async for chunk in response:
        try:
            if chunk.text:
                full_plain_message += (chunk.text)
                message = format_message(full_plain_message)
                init_msg = await init_msg.edit_text(text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        except StopCandidateException as sce:
            await init_msg.edit_text("The model unexpectedly stopped generating.")
            chat.rewind() # Rewind the chat session to prevent the bot from getting stuck
            continue
        except BadRequest:
            await response.resolve() # Resolve the response to prevent the chat session from getting stuck
            continue
        except NetworkError:
            raise NetworkError("Looks like you're network is down. Please try again later.")
        except IndexError:
            await init_msg.reply_text("The bot could not generate a response. Please start a new chat with /new")
            await response.resolve() # Resolve the response to prevent the chat session from getting stuck
            continue
        except Exception as e:
            print(e)
            if chunk.text:
                full_plain_message = chunk.text
                message = format_message(full_plain_message)
                init_msg = await update.message.reply_text(text=message, parse_mode=ParseMode.HTML,reply_to_message_id=init_msg.message_id, disable_web_page_preview=True)
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