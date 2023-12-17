import re


def escape_html(text: str) -> str:
    """Escape HTML characters."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def apply_hand_points(text: str) -> str:
    """Replace markdown bullet points with hand emojis."""
    pattern = r"(?<=\n)\*\s(?!\*)|^\*\s(?!\*)"

    replaced_text = re.sub(pattern, "👉 ", text)

    return replaced_text


def apply_bold(text: str) -> str:
    """Replace markdown bold ** with HTML bold tags."""
    pattern = r"\*\*(.*?)\*\*"
    replaced_text = re.sub(pattern, r"<b>\1</b>", text)
    return replaced_text


def apply_italic(text: str) -> str:
    """Replace markdown italic * with HTML italic tags."""
    pattern = r"(?<!\*)\*(?!\*)(?!\*\*)(.*?)(?<!\*)\*(?!\*)"
    replaced_text = re.sub(pattern, r"<i>\1</i>", text)
    return replaced_text


def apply_code(text: str) -> str:
    """Replace markdown code ``` with HTML code tags."""
    pattern = r"```[\w]*\n((?:.|[\n])*?)\n```"
    replaced_text = re.sub(pattern, r"<pre>\1</pre>", text)
    return replaced_text


def apply_monospace(text: str) -> str:
    """Replace markdown monospace ` with HTML code tags."""
    pattern = r"(?<!`)`(?!`)(.*?)(?<!`)`(?!`)"
    replaced_text = re.sub(pattern, r"<code>\1</code>", text)
    return replaced_text


def apply_link(text: str) -> str:
    """Replace markdown link [text](url) with HTML anchor tags."""
    pattern = r"\[(.*?)\]\((.*?)\)"
    replaced_text = re.sub(pattern, r'<a href="\2">\1</a>', text)
    return replaced_text


def apply_underline(text: str) -> str:
    """Replace markdown underline __ with HTML underline tags."""
    pattern = r"__(.*?)__"
    replaced_text = re.sub(pattern, r"<u>\1</u>", text)
    return replaced_text


def apply_strikethrough(text: str) -> str:
    """Replace markdown strikethrough ~~ with HTML strikethrough tags."""
    pattern = r"~~(.*?)~~"
    replaced_text = re.sub(pattern, r"<s>\1</s>", text)
    return replaced_text


def apply_header(text: str) -> str:
    """Replace markdown header # with HTML header tags."""
    pattern = r"#{2,6} (.*)"
    replaced_text = re.sub(pattern, r"<b><u>\1</u></b>", text)
    return replaced_text


def format_message(message: str) -> str:
    """Format the message to HTML."""
    message = escape_html(message)
    message = apply_link(message)
    message = apply_header(message)
    message = apply_code(message)
    message = apply_bold(message)
    message = apply_italic(message)
    message = apply_underline(message)
    message = apply_strikethrough(message)
    message = apply_monospace(message)
    message = apply_hand_points(message)
    return message
