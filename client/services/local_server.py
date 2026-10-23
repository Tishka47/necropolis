"""Встроенный сервер API для Windows-версии (Necropolis.exe).
Если адрес API указывает на этот компьютер и там никто не отвечает, поднимаем FastAPI-сервер
из папки backend прямо внутри приложения, в фоновом потоке. Так .exe работает «из коробки»:
не нужно ставить Python и отдельно запускать uvicorn.
Сервер слушает 0.0.0.0, поэтому к нему может подключиться и телефон из той же Wi-Fi сети."""
import logging
import os
import socket
import sys
import threading
import time
from urllib.parse import urlparse

LOCAL_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0"}


def is_local(api_url: str) -> bool:
    return (urlparse(api_url).hostname or "") in LOCAL_HOSTS


def port_of(api_url: str) -> int:
    return urlparse(api_url).port or 8000


def is_port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _lan_rank(ip: str) -> int:
    """Чем меньше, тем вероятнее это адрес домашней Wi-Fi/Ethernet сети.
    VPN и виртуальные адаптеры (WSL, Hyper-V) обычно сидят в 172.16–31.x — их в конец."""
    if ip.startswith("192.168."):
        return 0
    if ip.startswith("10."):
        return 1
    parts = ip.split(".")
    if parts[0] == "172" and 16 <= int(parts[1]) <= 31:
        return 2
    return 3


def lan_ip() -> str | None:
    """IP этого компьютера в локальной сети (его вводят в приложении на телефоне)."""
    candidates = set()
    try:
        candidates.update(info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
    except OSError:
        pass
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("8.8.8.8", 80))  # пакеты не отправляются, ОС просто выбирает сетевой интерфейс
            candidates.add(sock.getsockname()[0])
        except OSError:
            pass
    candidates = [ip for ip in candidates if not ip.startswith(("127.", "169.254."))]
    return min(candidates, key=_lan_rank) if candidates else None


def _backend_dir() -> str | None:
    """Папка backend при запуске из исходников; None в .exe (пакет app вшит в сборку)."""
    if getattr(sys, "frozen", False):
        return None
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend")


def start_if_needed(api_url: str) -> bool:
    """True, если запустили встроенный сервер. Если сервер уже работает или адрес не локальный — False."""
    if not is_local(api_url):
        return False
    port = port_of(api_url)
    if is_port_busy(port):
        return False  # сервер уже запущен (например, uvicorn из исходников)

    backend_dir = _backend_dir()
    if backend_dir is None:
        # .exe: база лежит рядом с программой (из исходников путь задаёт backend/app/core/config.py)
        db_path = os.path.join(os.path.dirname(sys.executable), "necropolis.db")
        os.environ.setdefault("DATABASE_URL", "sqlite:///" + db_path.replace("\\", "/"))
    elif os.path.isdir(backend_dir):
        sys.path.insert(0, backend_dir)
    else:
        return False

    try:
        import uvicorn
        from app.main import app as api_app
    except ImportError:
        return False  # в этом окружении нет зависимостей сервера — работаем с внешним сервером

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).setLevel(logging.WARNING)  # без этого лог пишет каждый запрос

    config = uvicorn.Config(
        api_app, host="0.0.0.0", port=port, log_config=None, access_log=False,
        http="h11", loop="asyncio", lifespan="on",
    )
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, name="api-server", daemon=True).start()

    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if server.started:
            return True
        time.sleep(0.1)
    return False
