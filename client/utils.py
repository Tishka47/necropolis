"""Форматирование дат и подписи для интерфейса."""
from datetime import date, datetime

STATUS_LABELS = {"approved": "Опубликовано", "pending": "На модерации", "rejected": "Отклонено"}
ROLE_LABELS = {"guest": "Гость", "user": "Пользователь", "moderator": "Модератор", "admin": "Администратор"}
MATERIAL_TYPES = {"photo": "Фотография", "document": "Документ", "text": "Текст", "link": "Ссылка"}


def parse_date(text: str) -> str | None:
    """'14.05.1931' или '1931-05-14' -> '1931-05-14'. Пусто -> None. Ошибка -> ValueError."""
    text = text.strip()
    if not text:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, fmt).date()
        except ValueError:
            continue
        if parsed > date.today():
            raise ValueError(f"Дата {text} в будущем")
        return parsed.isoformat()
    raise ValueError(f"Не понимаю дату «{text}». Формат: ДД.ММ.ГГГГ")


def fmt_date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.strptime(iso[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return iso


def life_dates(birth: str | None, death: str | None) -> str:
    return f"{fmt_date(birth) or '?'} — {fmt_date(death) or '?'}"


def life_years(birth: str | None, death: str | None) -> str:
    return f"{(birth or '?')[:4]} — {(death or '?')[:4]}"
