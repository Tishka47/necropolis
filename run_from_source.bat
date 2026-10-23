@echo off
rem Запуск приложения из исходников (нужен Python 3.12). Сервер API поднимается внутри приложения сам.
rem Если нужен просто запуск без Python - откройте Necropolis.exe.
cd /d "%~dp0"
call packaging\ensure_venv.bat || goto :error
cd /d "%~dp0"
".venv\Scripts\python.exe" client\main.py || goto :error
exit /b 0

:error
echo.
echo Не удалось запустить. Текст ошибки - выше.
pause
exit /b 1
