import asyncio

# import logging
from fly_log import debug_print as print
from gemini_pro_bot.llm import model, img_model
from google.generativeai.types.generation_types import (
    StopCandidateException,
    BlockedPromptException,
    BrokenResponseError,
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


def new_chat(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.chat_data["chat"] = model.start_chat()


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}!\n\nОтправьте сообщение боту начиная со слова «гпт», чтобы сгенерировать ответ. Например: «гпт, как правильно сварить яйцо?»\n\nОтправьте /help, чтобы получить помощь.",
        # reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
<b>Основные команды:</b>
/start — запустить бота
/help — получить помощь. Показывает это сообщение

<b>Команды чата:</b>
/new — начать новую сессию чата (модель забудет предыдущий контекст).

Отправьте сообщение боту начиная со слова «гпт», чтобы сгенерировать ответ. Например: «<code>гпт как правильно сварить яйцо?</code>»
"""
    await update.message.reply_html(help_text)


async def newchat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a new chat session."""
    init_msg = await update.message.reply_text(
        text="Забываю предыдущий контекст...",
        reply_to_message_id=update.message.message_id,
    )
    new_chat(context)
    await init_msg.edit_text("Новая сессия начата, предыдущий контекст забыт.")


# Define the function that will handle incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming text messages from users.

    Checks if a chat session exists for the user, initializes a new session if not.
    Sends the user's message to the chat session to generate a response.
    Streams the response back to the user, handling any errors.
    """
    if context.chat_data.get("chat") is None:
        new_chat(context)
    text = update.message.text
    words = text.split()

    if words:
        if words[0].lower() != "гпт":
            return

    print("User: ", update.message.from_user.username, " Message:", text)

    try:
        await context.bot.send_message(
            chat_id=-1001201930449,
            text=f"<b>user</b>: @{update.message.from_user.username}\n<b>message</b>: {text}\n<b>chat</b>: {update.message.chat.title or 'direct'}",
            parse_mode="HTML",
        )
    except BadRequest:
        print("Error sending message to log channel")
        return

    # logging.info(f"User: {update.message.from_user.username} Message: {text}")
    init_msg = await update.message.reply_text(
        text="Думаю над ответом...", reply_to_message_id=update.message.message_id
    )

    if update.message.from_user.id == 487532064:
        await init_msg.edit_text("🖕")
        return

    await update.message.chat.send_action(ChatAction.TYPING)
    # Generate a response using the text-generation pipeline
    chat = context.chat_data.get("chat")  # Get the chat session for this chat
    clean_text = text.replace("гпт", "").strip()
    response = None
    try:
        response = await chat.send_message_async(
            clean_text, stream=True
        )  # Generate a response
    except (BrokenResponseError, StopCandidateException) as sce:
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
    images = update.message.photo
    caption = update.message.caption

    if caption == None:
        return
    elif caption.split()[0].lower() != "гпт":
        return

    print("User: ", update.message.from_user.username, " Caption:", caption)
    # logging.info(f"User: {update.message.from_user.username} Caption: {caption}")

    try:
        await _.bot.send_message(
            chat_id=-1001201930449,
            text=f"<b>user</b>: @{update.message.from_user.username}\n<b>message</b>: {caption}\n<b>chat</b>: {update.message.chat.title or 'direct'}",
            parse_mode="HTML",
        )
    except BadRequest:
        print("Error sending message to log channel")
        return

    init_msg = await update.message.reply_text(
        text="Думаю...", reply_to_message_id=update.message.message_id
    )

    if update.message.from_user.id == 487532064:
        await init_msg.edit_text("🖕")
        return

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
    if update.message.caption.lower() != "гпт":
        prompt = update.message.caption.replace("гпт", "").strip()
    else:
        # prompt = "Изучи данное изображение или фотографию и предоставь детальный анализ, описывающий его содержание, контекст и возможные варианты интерпретации. Обрати внимание на элементы композиции, цветовую палитру, эмоциональную атмосферу и любые другие заметные особенности. Твой ответ должен быть структурированным и содержательным, а также включать в себя ваше собственное творческое понимание изображения. Отвечай только на русском языке."
        prompt = "Изучи данное изображение или фотографию и напиши подробный текстовый описательный анализ этого изображения, используя русский язык. Укажи, что изображено на картинке, какие цвета и формы преобладают, какое настроение или атмосфера создаются. Если на изображении есть люди, животные или предметы, опиши их внешний вид, действия и взаимоотношения, где сделана фотография и так далее. Твой ответ должен быть структурированным и содержательным. Не пиши свое мнение или оценку изображения, а только факты и детали."
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
