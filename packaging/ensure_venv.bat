@echo off
rem Общее окружение .venv в корне проекта: зависимости клиента и сервера.
rem Если .venv нет или он скопирован с другого компьютера и не работает - создается заново.
cd /d "%~dp0.."

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import kivy, fastapi, uvicorn, sqlalchemy" >nul 2>&1 && exit /b 0
)

where py >nul 2>&1 || (
    echo Не найден Python. Установите Python 3.12 с https://www.python.org/downloads/
    echo и при установке отметьте "Add python.exe to PATH".
    exit /b 1
)

echo Устанавливаю зависимости (только при первом запуске, несколько минут)...
py -3.12 -m venv --clear .venv || (
    echo Нужен именно Python 3.12: Kivy пока не поддерживает 3.13 и 3.14.
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install -q --upgrade pip
".venv\Scripts\python.exe" -m pip install -q -r client\requirements.txt -r backend\requirements.txt || exit /b 1
exit /b 0
