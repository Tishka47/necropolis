"""Ролевая модель: роль -> набор разрешений (many-to-many в БД).
Код проверяет не роль ("admin?"), а конкретное разрешение ("memorial:moderate?").
Новую роль можно собрать из разрешений, не трогая код эндпоинтов."""


class Perm:
    MEMORIAL_CREATE = "memorial:create"
    MEMORIAL_EDIT_OWN = "memorial:edit_own"
    MEMORIAL_EDIT_ANY = "memorial:edit_any"
    MEMORIAL_DELETE_OWN = "memorial:delete_own"
    MEMORIAL_DELETE_ANY = "memorial:delete_any"
    MEMORIAL_MODERATE = "memorial:moderate"
    MEMORIAL_VIEW_UNPUBLISHED = "memorial:view_unpublished"
    MATERIAL_ADD = "material:add"
    MATERIAL_DELETE_ANY = "material:delete_any"
    COMMENT_CREATE = "comment:create"
    COMMENT_DELETE_ANY = "comment:delete_any"
    LOCATION_MANAGE = "location:manage"
    USER_MANAGE = "user:manage"


PERMISSION_DESCRIPTIONS: dict[str, str] = {
    Perm.MEMORIAL_CREATE: "Создание мемориальных страниц",
    Perm.MEMORIAL_EDIT_OWN: "Редактирование своих страниц",
    Perm.MEMORIAL_EDIT_ANY: "Редактирование любых страниц",
    Perm.MEMORIAL_DELETE_OWN: "Удаление своих страниц",
    Perm.MEMORIAL_DELETE_ANY: "Удаление любых страниц",
    Perm.MEMORIAL_MODERATE: "Модерация страниц",
    Perm.MEMORIAL_VIEW_UNPUBLISHED: "Просмотр неопубликованных страниц",
    Perm.MATERIAL_ADD: "Добавление материалов",
    Perm.MATERIAL_DELETE_ANY: "Удаление любых материалов",
    Perm.COMMENT_CREATE: "Добавление воспоминаний",
    Perm.COMMENT_DELETE_ANY: "Удаление любых воспоминаний",
    Perm.LOCATION_MANAGE: "Управление местами памяти",
    Perm.USER_MANAGE: "Управление пользователями и ролями",
}

_USER = [
    Perm.MEMORIAL_CREATE, Perm.MEMORIAL_EDIT_OWN, Perm.MEMORIAL_DELETE_OWN,
    Perm.MATERIAL_ADD, Perm.COMMENT_CREATE,
]
_MODERATOR = _USER + [
    Perm.MEMORIAL_EDIT_ANY, Perm.MEMORIAL_MODERATE, Perm.MEMORIAL_VIEW_UNPUBLISHED,
    Perm.MATERIAL_DELETE_ANY, Perm.COMMENT_DELETE_ANY, Perm.LOCATION_MANAGE,
]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "user": _USER,
    "moderator": _MODERATOR,
    "admin": list(PERMISSION_DESCRIPTIONS),
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    "user": "Зарегистрированный пользователь",
    "moderator": "Модератор",
    "admin": "Администратор",
}

DEFAULT_ROLE = "user"
