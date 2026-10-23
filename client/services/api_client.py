"""Слой работы с API. Экраны не знают про HTTP: они вызывают методы этого класса.
Здесь же автоматическое обновление access-токена через refresh-токен."""
import threading

import requests


class ApiError(Exception):
    def __init__(self, status: int, detail: str, code: str | None = None) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail
        self.code = code


class ApiClient:
    NO_REFRESH_PATHS = {
        "/api/auth/login", "/api/auth/register", "/api/auth/refresh", "/api/auth/logout",
    }

    def __init__(self, base_url: str, on_refresh_token_changed=None) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self._on_refresh_token_changed = on_refresh_token_changed
        self._http = requests.Session()
        self._refresh_lock = threading.Lock()

    # ---------- токены ----------

    def set_tokens(self, access: str | None, refresh: str | None) -> None:
        self.access_token = access
        self.refresh_token = refresh
        if self._on_refresh_token_changed:
            self._on_refresh_token_changed(refresh)

    def clear_tokens(self) -> None:
        self.set_tokens(None, None)

    def _refresh_tokens(self) -> bool:
        with self._refresh_lock:
            token = self.refresh_token
            if not token:
                return False
            try:
                response = self._http.post(
                    self.base_url + "/api/auth/refresh", json={"refresh_token": token}, timeout=10
                )
                data = self._parse(response)
            except (ApiError, requests.exceptions.RequestException):
                self.clear_tokens()
                return False
            self.set_tokens(data["access_token"], data["refresh_token"])
            return True

    # ---------- транспорт ----------

    def _send(self, method: str, path: str, json=None, params=None) -> requests.Response:
        headers = {"Accept": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        try:
            return self._http.request(
                method, self.base_url + path, json=json, params=params, headers=headers, timeout=10
            )
        except requests.exceptions.Timeout as exc:
            raise ApiError(0, "Сервер не ответил вовремя. Если он в облаке, он мог спать — "
                              "подождите минуту и попробуйте ещё раз.") from exc
        except requests.exceptions.RequestException as exc:
            raise ApiError(0, "Нет связи с сервером. Проверьте, что API запущен.") from exc

    @staticmethod
    def _parse(response: requests.Response):
        if response.status_code >= 400:
            try:
                data = response.json()
            except ValueError:
                data = {}
            if not isinstance(data, dict):
                data = {}
            detail = data.get("detail")
            if isinstance(detail, list):
                detail = "; ".join(str(d.get("msg", d)) if isinstance(d, dict) else str(d) for d in detail)
            raise ApiError(
                response.status_code,
                detail or f"Ошибка сервера ({response.status_code})",
                data.get("code"),
            )
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def request(self, method: str, path: str, *, json=None, params=None):
        response = self._send(method, path, json, params)
        if response.status_code == 401 and self.refresh_token and path not in self.NO_REFRESH_PATHS:
            if self._refresh_tokens():
                response = self._send(method, path, json, params)
        return self._parse(response)

    def wake(self) -> None:
        """Разбудить сервер (бесплатный Render засыпает): один запрос с долгим ожиданием."""
        try:
            self._http.get(self.base_url + "/api/health", timeout=90)
        except requests.exceptions.RequestException as exc:
            raise ApiError(0, "Нет связи с сервером. Проверьте интернет и адрес сервера.") from exc

    # ---------- авторизация ----------

    def register(self, username: str, email: str, password: str) -> dict:
        return self.request("POST", "/api/auth/register",
                            json={"username": username, "email": email, "password": password})

    def login(self, login: str, password: str) -> dict:
        data = self.request("POST", "/api/auth/login", json={"login": login, "password": password})
        self.set_tokens(data["access_token"], data["refresh_token"])
        return data

    def restore_session(self) -> dict:
        if not self._refresh_tokens():
            raise ApiError(401, "Сессия истекла, войдите снова", "SESSION_EXPIRED")
        return self.me()

    def logout(self) -> None:
        token = self.refresh_token
        try:
            if token:
                self.request("POST", "/api/auth/logout", json={"refresh_token": token})
        finally:
            self.clear_tokens()

    # ---------- профиль ----------

    def me(self) -> dict:
        return self.request("GET", "/api/users/me")

    def update_me(self, payload: dict) -> dict:
        return self.request("PATCH", "/api/users/me", json=payload)

    # ---------- мемориальные страницы ----------

    def list_memorials(self, params: dict | None = None) -> list:
        return self.request("GET", "/api/memorials", params=params or {})

    def get_memorial(self, memorial_id: int) -> dict:
        return self.request("GET", f"/api/memorials/{memorial_id}")

    def create_memorial(self, payload: dict) -> dict:
        return self.request("POST", "/api/memorials", json=payload)

    def update_memorial(self, memorial_id: int, payload: dict) -> dict:
        return self.request("PATCH", f"/api/memorials/{memorial_id}", json=payload)

    def delete_memorial(self, memorial_id: int) -> None:
        self.request("DELETE", f"/api/memorials/{memorial_id}")

    def set_memorial_status(self, memorial_id: int, status: str) -> dict:
        return self.request("PATCH", f"/api/memorials/{memorial_id}/status", json={"status": status})

    # ---------- материалы, воспоминания, места ----------

    def list_materials(self, memorial_id: int) -> list:
        return self.request("GET", f"/api/memorials/{memorial_id}/materials")

    def add_material(self, memorial_id: int, payload: dict) -> dict:
        return self.request("POST", f"/api/memorials/{memorial_id}/materials", json=payload)

    def delete_material(self, material_id: int) -> None:
        self.request("DELETE", f"/api/materials/{material_id}")

    def list_comments(self, memorial_id: int) -> list:
        return self.request("GET", f"/api/memorials/{memorial_id}/comments")

    def add_comment(self, memorial_id: int, text: str) -> dict:
        return self.request("POST", f"/api/memorials/{memorial_id}/comments", json={"text": text})

    def delete_comment(self, comment_id: int) -> None:
        self.request("DELETE", f"/api/comments/{comment_id}")

    def list_locations(self) -> list:
        return self.request("GET", "/api/locations")

    def create_location(self, payload: dict) -> dict:
        return self.request("POST", "/api/locations", json=payload)

    # ---------- администрирование ----------

    def list_users(self) -> list:
        return self.request("GET", "/api/users", params={"limit": 200})

    def change_role(self, user_id: int, role: str) -> dict:
        return self.request("PATCH", f"/api/users/{user_id}/role", json={"role": role})

    def set_user_active(self, user_id: int, is_active: bool) -> dict:
        return self.request("PATCH", f"/api/users/{user_id}/active", json={"is_active": is_active})
