"""Keep technical chat fragments outside dictionaries and translation services."""
import re

_DOMAIN = r"(?:[\w-]+\.)+(?:[^\W\d_]{2,63}|xn--[a-z0-9-]+)"
_IPV4 = r"(?:\d{1,3}\.){3}\d{1,3}"
_IPV6 = r"\[[a-f0-9:.%]+\]|(?<!\w)(?:[a-f0-9]{0,4}:){2,7}[a-f0-9]{0,4}(?!\w)"
_ADDRESS = re.compile(
    rf"(?:[a-z][a-z0-9+.-]*://[^\s<>\"']+|"
    rf"(?:[\w.%+\-]+@)?(?:{_DOMAIN}|{_IPV4}|{_IPV6})"
    rf"(?::\d+)?(?:[/#?][^\s<>\"']*)?)", re.IGNORECASE
)


def technical_fragments(text):
    return tuple(match.group() for match in _ADDRESS.finditer(text))


def translate_prose(text, translate):
    """Invoke translate only for prose and preserve whitespace at boundaries."""
    pieces = []
    end = 0
    def append_prose(value):
        if any(char.isalnum() for char in value):
            core = value.strip()
            start = len(value) - len(value.lstrip())
            pieces.extend((value[:start], translate(core), value[start + len(core):]))
        else:
            pieces.append(value)
    for match in _ADDRESS.finditer(text):
        append_prose(text[end:match.start()])
        pieces.append(match.group())
        end = match.end()
    if end == 0:
        return translate(text)
    append_prose(text[end:])
    return "".join(pieces)
