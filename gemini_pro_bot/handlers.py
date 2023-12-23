import asyncio
from gemini_pro_bot.llm import model, img_model
import google.generativeai as genai
from google.generativeai.types.generation_types import (
    StopCandidateException,
    BlockedPromptException,
)
from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from telegram.error import NetworkError, BadRequest
from telegram.constants import ChatAction, ParseMode
from gemini_pro_bot.html_format import format_message
import PIL.Image as load_image
from io import BytesIO

chats: dict[int, genai.ChatSession] = {}

def new_chat(chat_id: int) -> None:
    chats[chat_id] = model.start_chat()


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}!\n\nStart sending messages with me to generate a response.\n\nSend /new to start a new chat session.",
        # reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
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
    init_msg = await update.message.reply_text(
        text="Starting new chat session...",
        reply_to_message_id=update.message.message_id,
    )
    new_chat(update.message.chat.id)
    await init_msg.edit_text("New chat session started.")


# Define the function that will handle incoming messages
async def handle_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming text messages from users.

    Checks if a chat session exists for the user, initializes a new session if not.
    Sends the user's message to the chat session to generate a response.
    Streams the response back to the user, handling any errors.
    """
    if update.message.chat.id not in chats:
        new_chat(update.message.chat.id)
    text = update.message.text
    init_msg = await update.message.reply_text(
        text="Generating...", reply_to_message_id=update.message.message_id
    )
    await update.message.chat.send_action(ChatAction.TYPING)
    # Generate a response using the text-generation pipeline
    chat = chats[update.message.chat.id]  # Get the chat session for this chat
    response = None
    try:
        response = await chat.send_message_async(
            text, stream=True
        )  # Generate a response
    except StopCandidateException as sce:
        print("Prompt: ", text, " was stopped. User: ", update.message.from_user)
        print(sce)
        await init_msg.edit_text("The model unexpectedly stopped generating.")
        chat.rewind()  # Rewind the chat session to prevent the bot from getting stuck
        return
    except BlockedPromptException as bpe:
        print("Prompt: ", text, " was blocked. User: ", update.message.from_user)
        print(bpe)
        await init_msg.edit_text("Blocked due to safety concerns.")
        if response:
            # Resolve the response to prevent the chat session from getting stuck
            await response.resolve()
        return
    full_plain_message = ""
    # Stream the responses
    async for chunk in response:
        try:
            if chunk.text:
                full_plain_message += chunk.text
                message = format_message(full_plain_message)
                init_msg = await init_msg.edit_text(
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
        except StopCandidateException as sce:
            await init_msg.edit_text("The model unexpectedly stopped generating.")
            chat.rewind()  # Rewind the chat session to prevent the bot from getting stuck
            continue
        except BadRequest:
            await response.resolve()  # Resolve the response to prevent the chat session from getting stuck
            continue
        except NetworkError:
            raise NetworkError(
                "Looks like you're network is down. Please try again later."
            )
        except IndexError:
            await init_msg.reply_text(
                "Some index error occurred. This response is not supported."
            )
            await response.resolve()
            continue
        except Exception as e:
            print(e)
            if chunk.text:
                full_plain_message = chunk.text
                message = format_message(full_plain_message)
                init_msg = await update.message.reply_text(
                    text=message,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=init_msg.message_id,
                    disable_web_page_preview=True,
                )
        # Sleep for a bit to prevent the bot from getting rate-limited
        await asyncio.sleep(0.1)
        
        
async def handle_image(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming images with captions and generate a response."""
    init_msg = await update.message.reply_text(
        text="Generating...", reply_to_message_id=update.message.message_id
    )
    images = update.message.photo
    unique_images: dict = {}
    for img in images:
        file_id = img.file_id[:-7]
        if file_id not in unique_images:
            unique_images[file_id] = img
        elif img.file_size > unique_images[file_id].file_size:
            unique_images[file_id] = img
    file_list = list(unique_images.values())
    file = await file_list[0].get_file()
    a_img = load_image.open(BytesIO(await file.download_as_bytearray()))
    prompt = None
    if update.message.caption:
        prompt = update.message.caption
    else:
        prompt = "Analyse this image and generate response"
    response = await img_model.generate_content_async([prompt, a_img], stream=True)
    full_plain_message = ""
    async for chunk in response:
        try:
            if chunk.text:
                full_plain_message += chunk.text
                message = format_message(full_plain_message)
                init_msg = await init_msg.edit_text(
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
        except StopCandidateException:
            await init_msg.edit_text("The model unexpectedly stopped generating.")
        except BadRequest:
            await response.resolve()
            continue
        except NetworkError:
            raise NetworkError(
                "Looks like you're network is down. Please try again later."
            )
        except IndexError:
            await init_msg.reply_text(
                "Some index error occurred. This response is not supported."
            )
            await response.resolve()
            continue
        except Exception as e:
            print(e)
            if chunk.text:
                full_plain_message = chunk.text
                message = format_message(full_plain_message)
                init_msg = await update.message.reply_text(
                    text=message,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=init_msg.message_id,
                    disable_web_page_preview=True,
                )
        await asyncio.sleep(0.1)
