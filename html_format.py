import re

def apply_hand_points(text: str) -> str:
    # Define the modified pattern to match '\n\*(?!\*)'
    pattern = r'(?<=\n)\*\s(?!\*)|^\*\s(?!\*)'

    replaced_text = re.sub(pattern, '👉 ', text)

    return replaced_text

def apply_bold(text: str) -> str:
    # Pattern to match all markdown bold **
    pattern = r'\*\*(.*?)\*\*'
    replaced_text = re.sub(pattern, r'<b>\1</b>', text)
    return replaced_text


def apply_italic(text: str) -> str:
    # Pattern to match all markdown italic **
    pattern = r'(?<!\*)\*(?!\*)(?!\*\*)(.*?)(?<!\*)\*(?!\*)'
    replaced_text = re.sub(pattern, r'<i>\1</i>', text)
    return replaced_text


def apply_code(text: str) -> str:
    # Pattern to match all markdown code ```<any_text>.*```
    pattern = r'```[\w]*\n((?:.|[\n])*?)\n```'
    replaced_text = re.sub(pattern, r'<pre>\1</pre>', text)
    return replaced_text


def apply_monospace(text: str) -> str:
    # Pattern to match all markdown code `.*` and not ```.*```
    pattern = r'(?<!`)`(?!`)(.*?)(?<!`)`(?!`)'
    replaced_text = re.sub(pattern, r'<code>\1</code>', text)
    return replaced_text


def apply_link(text: str) -> str:
    # Pattern to match all markdown link [.*](.*)
    pattern = r'\[(.*?)\]\((.*?)\)'
    replaced_text = re.sub(pattern, r'<a href="\2">\1</a>', text)
    return replaced_text

# def apply_header(text: str) -> str:
#     # Pattern to match "### <any_text>"
#     pattern = r'### (.*)'
#     replaced_text = re.sub(pattern, r'<b><u>\1</u></b>', text)
#     return replaced_text
    
    
def format_message(message: str) -> str:
    message = apply_bold(message)
    message = apply_italic(message)
    message = apply_hand_points(message)
    message = apply_code(message)
    message = apply_monospace(message)
    message = apply_link(message)
    # message = apply_header(message)
    return message