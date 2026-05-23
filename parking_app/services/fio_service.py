from __future__ import annotations


def build_fio(*, surname: str, name: str, patronymic: str | None = None) -> str:
    parts = [surname.strip(), name.strip()]
    if patronymic and patronymic.strip():
        parts.append(patronymic.strip())
    return " ".join(parts)


def split_fio(fio: str) -> tuple[str, str, str | None]:
    parts = [p for p in fio.strip().split() if p]
    if len(parts) == 0:
        return "", "", None
    if len(parts) == 1:
        return parts[0], "", None
    if len(parts) == 2:
        return parts[0], parts[1], None
    return parts[0], parts[1], " ".join(parts[2:])
