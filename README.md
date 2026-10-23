# Цифровой некрополь — мобильное приложение

Kivy-клиент + REST API на FastAPI + SQLAlchemy ORM + SQLite.

```
necropolis/
├── Necropolis.exe        — готовое приложение для Windows (сервер встроен), Python не нужен
├── Necropolis.apk        — приложение для Android 7.0+ (подключается к серверу на компьютере)
├── necropolis.db         — база данных (общая для .exe и запуска из исходников)
├── run_from_source.bat   — запуск приложения из исходников (нужен Python 3.12)
├── run_server.bat        — отдельный запуск сервера API (Swagger, телефон)
├── backend/              — сервер API (FastAPI)
├── client/               — приложение (Kivy); buildozer.spec — сборка APK
└── packaging/            — сборка .exe (build_exe.bat, necropolis.spec)
```

## Запуск

### Проще всего: Necropolis.exe

Двойной клик по `Necropolis.exe`. Ничего устанавливать не нужно: приложение само поднимает
сервер API внутри себя и работает с `necropolis.db`, лежащей рядом. Если базы нет, она
создаётся с тестовыми данными. Первый запуск занимает 5–10 секунд (распаковка).

Windows может спросить разрешение для сети (брандмауэр): разрешите для частных сетей —
это нужно, чтобы к серверу мог подключиться телефон. Если сервер уже запущен отдельно
(`run_server.bat`), приложение использует его, а не встроенный.

Логи пишутся в `necropolis.log` рядом с .exe — пригодятся, если что-то пошло не так.

### Из исходников (для разработки)

Нужен **Python 3.12** с python.org (Kivy пока не работает на 3.13/3.14).
Двойной клик по `run_from_source.bat`: при первом запуске он сам создаст окружение `.venv`
и поставит зависимости (несколько минут), потом откроет приложение со встроенным сервером.

`run_server.bat` — только сервер, без приложения: Swagger на http://127.0.0.1:8000.
Вручную то же самое:

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r client/requirements.txt -r backend/requirements.txt
python client/main.py                                   # приложение (сервер встроен)
cd backend && uvicorn app.main:app --host 0.0.0.0       # или отдельно сервер
```

### Телефон в той же Wi-Fi сети

1. Скопировать `Necropolis.apk` на телефон и установить (Android попросит разрешить
   установку из этого источника — это нормально для APK не из Google Play).
2. На компьютере запустить `Necropolis.exe` (или `run_server.bat`). На экране входа .exe
   пишет адрес для телефона, например `http://192.168.1.5:8000`.
3. В приложении на телефоне нажать «Сменить адрес сервера» внизу экрана входа и ввести
   этот адрес. Телефон и компьютер должны быть в одной Wi-Fi сети.

### Пересобрать .exe

`packaging\build_exe.bat` (нужен Python 3.12) — новый `Necropolis.exe` появится в корне.

### Собрать .apk

APK для Kivy собирается Buildozer'ом, а он работает только в Linux. Настройки уже готовы:
`client/buildozer.spec` (разрешён http-трафик в локальной сети, нужен для связи с сервером).

**Вариант 1 — Google Colab** (ничего не ставить на компьютер). Заархивировать папку `client`
в `client.zip`, открыть https://colab.research.google.com, создать блокнот и выполнить ячейки:

```
!pip install buildozer cython==0.29.36
!sudo apt-get update -qq && sudo apt-get install -y -qq openjdk-17-jdk autoconf automake libtool libltdl-dev libffi-dev libssl-dev zip unzip pkg-config cmake
```
```
from google.colab import files
files.upload()                      # выбрать client.zip
!unzip -q -o client.zip -d app
```
```
%cd app/client
!yes | buildozer -v android debug   # 20–40 минут при первой сборке
```
```
import glob; files.download(glob.glob("bin/*.apk")[0])
```

Если в архиве папка лежит не как `client/`, поправьте путь в `%cd`.

**Вариант 2 — WSL/Linux:** `pip install --user buildozer cython==0.29.36` (именно `--user`,
не в venv — иначе Buildozer падает), поставить те же пакеты через apt, затем в папке
`client`: `buildozer -v android debug`. APK появится в `client/bin/`.

**Известные проблемы python-for-android (ветка master, на момент сборки `Necropolis.apk`).**
Buildozer скачивает python-for-android в `client/.buildozer/android/platform/python-for-android`.
При сборке `Necropolis.apk` в его файле `pythonforandroid/build.py` пришлось поправить две ошибки:

1. Функция `process_python_modules`: подставляет Android-wheel (например `charset_normalizer`),
   который pip потом отвергает (`... is not a supported wheel on this platform`). Исправлено
   заменой `not is_wheel_compatible(filename, arch, ctx)` на `not is_wheel_platform_independent(filename)`.
2. Функция `run_pymodules_install`: на второй архитектуре venv создаётся поверх старого, и pip
   ломается (`cannot import name 'BuildDependencyInstallError'`). Исправлено удалением папки
   `venv` перед `shprint(host_python, '-m', 'venv', 'venv')`.

Если при пересборке появятся эти ошибки — первый запуск `buildozer` скачает python-for-android,
затем нужно внести правки и запустить `buildozer android debug` ещё раз. Возможно, в новых
версиях python-for-android их уже исправили.

### Облако (бесплатно): Render + Supabase

```
APK / .exe ──https──► Render (FastAPI) ──► Supabase (PostgreSQL)
```

Приложение по умолчанию ходит на сервер в облаке (`CLOUD_URL` в `client/config.py`), поэтому
работает через любой интернет — Wi-Fi или мобильный, компьютер включать не нужно.

1. **Supabase** → New project (отдельный, не общий с другими проектами — таблицы `users` и т. п.
   пересекутся) → Connect → **Session pooler** → скопировать строку
   `postgresql://postgres.XXXX:[YOUR-PASSWORD]@aws-...pooler.supabase.com:5432/postgres` и подставить
   пароль от БД. Префикс `postgresql://` сервер сам превратит в `postgresql+psycopg2://`.
2. **Render** → New → **Blueprint** → выбрать репозиторий с этим проектом: Render прочитает
   `render.yaml` из корня. При создании спросит `DATABASE_URL` (строка из п. 1) и `ADMIN_PASSWORD`
   (пароль админа в облаке; `moder` и `demo` получат пароли из «Тестовых аккаунтов»).
3. Таблицы, роли, места памяти и тестовые страницы создаются сами при старте сервера.
4. Проверка: `https://<адрес от Render>/docs`. Если адрес не `https://necropolis.onrender.com` —
   поменять `CLOUD_URL` в `client/config.py` и пересобрать .exe и .apk.

Свой компьютер вместо облака: «Сменить адрес сервера» на экране входа → `http://127.0.0.1:8000`
(Necropolis.exe поднимет встроенный сервер). Пустой адрес — вернуться к облаку.

Ограничения бесплатных тарифов:
- Render засыпает после 15 минут без запросов, первый запрос будит его примерно минуту —
  приложение в это время пишет «Сервер … просыпается». 750 часов работы в месяц.
- Supabase ставит проект на паузу после недели без активности — включается кнопкой Restore
  в дашборде, данные сохраняются. 500 МБ на базу.

### Тестовые аккаунты

| Логин | Пароль | Роль |
|---|---|---|
| admin | Admin123! | Администратор |
| moder | Moder123! | Модератор |
| demo | Demo123! | Пользователь |

Сбросить базу: закрыть приложение/сервер и удалить `necropolis.db` в корне — при следующем
запуске создастся новая с тестовыми данными.

## Архитектура

Сервер разделён на слои, каждый отвечает за одно:

```
HTTP-запрос
   ↓
api/           Роутеры: принимают запрос, валидируют через схемы, вызывают сервис.
   ↓           Не содержат бизнес-логики и SQL.
services/      Бизнес-логика: права доступа, правила (модерация, ротация токенов),
   ↓           commit()/rollback(). Не знают про HTTP.
repositories/  Доступ к данным: все запросы select() живут только здесь.
   ↓
models/        ORM-модели SQLAlchemy = таблицы БД.
```

Сбоку: `schemas/` (Pydantic: что приходит и уходит в JSON), `core/` (настройки,
безопасность, обработка ошибок, подключение к БД).

Клиент:

```
screens/ + kv/   Экраны: Python-логика отдельно, разметка KV отдельно.
services/        ApiClient — единственное место, где есть HTTP. Экраны вызывают его методы.
                 local_server.py — встроенный сервер: на компьютере, если API не отвечает,
                 поднимает FastAPI из backend/ в фоновом потоке (так работает Necropolis.exe).
widgets/         Общие диалоги. theme.py — палитра (светлая и тёмная тема) и подключение шрифтов.
                 Цвета — свойства объекта theme.P, KV привязан к ним, поэтому смена темы
                 (пункт в главном меню) перекрашивает всё сразу; выбор запоминается.
fonts/           PT Sans (основной) и PT Serif (заголовки), лицензия OFL (fonts/OFL.txt).
```

## База данных (10 таблиц)

| Таблица | Назначение |
|---|---|
| roles | Роли |
| permissions | Разрешения |
| role_permissions | Роль ↔ разрешение (многие-ко-многим) |
| users | Пользователи |
| refresh_tokens | Сессии (refresh-токены) |
| memorials | Мемориальные страницы |
| materials | Фото, документы, тексты, ссылки |
| comments | Воспоминания |
| locations | Места памяти |
| memorial_locations | Страница ↔ место (многие-ко-многим) |

Связи: roles→users, users→memorials, users→materials, users→comments, users→refresh_tokens,
memorials→materials, memorials→comments, memorials↔locations, roles↔permissions.
