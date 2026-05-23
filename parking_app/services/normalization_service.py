import re

LATIN_TO_CYR = str.maketrans({
    "A": "А", "B": "В", "E": "Е", "K": "К", "M": "М", "H": "Н",
    "O": "О", "P": "Р", "C": "С", "T": "Т", "Y": "У", "X": "Х",
})


def normalize_phone(raw: str | None) -> str:
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    return digits


def normalize_state_number(raw: str | None) -> str:
    if not raw:
        return ""
    cleaned = re.sub(r"[\s\-]+", "", raw).upper()
    return cleaned.translate(LATIN_TO_CYR)
