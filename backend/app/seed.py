"""Начальные данные: роли, разрешения, тестовые пользователи, примеры страниц.
Идемпотентно: при повторном запуске ничего не дублирует."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.permissions import PERMISSION_DESCRIPTIONS, ROLE_DESCRIPTIONS, ROLE_PERMISSIONS
from app.core.security import hash_password
from app.models import Location, Memorial, MemorialStatus, Permission, Role, User

DEMO_USERS = [
    ("admin", "admin@necropolis.local", settings.ADMIN_PASSWORD, "admin"),
    ("moder", "moder@necropolis.local", "Moder123!", "moderator"),
    ("demo", "demo@necropolis.local", "Demo123!", "user"),
]


def _seed_roles(db: Session) -> dict[str, Role]:
    permissions = {p.code: p for p in db.scalars(select(Permission))}
    for code, description in PERMISSION_DESCRIPTIONS.items():
        if code not in permissions:
            permissions[code] = Permission(code=code, description=description)
            db.add(permissions[code])

    roles: dict[str, Role] = {}
    for name, codes in ROLE_PERMISSIONS.items():
        role = db.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(name=name, description=ROLE_DESCRIPTIONS[name])
            db.add(role)
        role.permissions = [permissions[c] for c in codes]
        roles[name] = role
    db.flush()
    return roles


def _seed_users(db: Session, roles: dict[str, Role]) -> dict[str, User]:
    users = {}
    for username, email, password, role_name in DEMO_USERS:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            user = User(username=username, email=email,
                        password_hash=hash_password(password), role=roles[role_name])
            db.add(user)
        users[username] = user
    db.flush()
    return users


def _seed_content(db: Session, users: dict[str, User]) -> None:
    if db.scalar(select(Location.id).limit(1)) is not None:
        return
    novodevichye = Location(name="Новодевичье кладбище", address="Москва, Лужнецкий проезд, 2")
    svyatogorsky = Location(name="Святогорский монастырь",
                            address="Псковская обл., пос. Пушкинские Горы")
    vagankovo = Location(name="Ваганьковское кладбище", address="Москва, ул. Сергея Макеева, 15")
    db.add_all([novodevichye, svyatogorsky, vagankovo])

    examples = [
        ("Чехов Антон Павлович", date(1860, 1, 29), date(1904, 7, 15),
         "Русский писатель и драматург, врач по образованию. Автор пьес «Чайка», "
         "«Три сестры», «Вишнёвый сад» и сотен рассказов.",
         MemorialStatus.APPROVED, users["moder"], [novodevichye]),
        ("Пушкин Александр Сергеевич", date(1799, 6, 6), date(1837, 2, 10),
         "Поэт, драматург и прозаик, основоположник современного русского литературного языка.",
         MemorialStatus.APPROVED, users["moder"], [svyatogorsky]),
        ("Иванов Пётр Сергеевич", date(1931, 5, 14), date(2010, 11, 2),
         "Инженер-строитель, ветеран труда. Страница добавлена для примера модерации.",
         MemorialStatus.PENDING, users["demo"], [vagankovo]),
    ]
    for full_name, born, died, bio, status, creator, locations in examples:
        db.add(Memorial(
            full_name=full_name, search_name=Memorial.normalize_name(full_name),
            birth_date=born, death_date=died, biography=bio,
            status=status.value, creator=creator, locations=locations,
        ))


def seed(db: Session) -> None:
    try:
        roles = _seed_roles(db)
        users = _seed_users(db, roles)
        _seed_content(db, users)
        db.commit()
    except Exception:
        db.rollback()
        raise
