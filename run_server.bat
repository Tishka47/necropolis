@echo off
rem Отдельный запуск сервера API (для Swagger или для телефона без Necropolis.exe). Нужен Python 3.12.
cd /d "%~dp0"
call packaging\ensure_venv.bat || goto :error
cd /d "%~dp0backend"
echo.
echo Сервер: http://127.0.0.1:8000  (Swagger открывается по этому адресу)
echo Для телефона: http://IP-этого-компьютера:8000  (IP смотрите командой ipconfig)
echo Остановить: Ctrl+C или закрыть окно.
echo.
"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 || goto :error
exit /b 0

:error
echo.
echo Не удалось запустить сервер. Текст ошибки - выше.
pause
exit /b 1
