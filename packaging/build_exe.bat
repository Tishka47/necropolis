@echo off
rem Пересборка Necropolis.exe (нужен Python 3.12). Результат: Necropolis.exe в корне проекта.
call "%~dp0ensure_venv.bat" || goto :error
cd /d "%~dp0.."

".venv\Scripts\python.exe" -m pip install -q pyinstaller || goto :error
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --distpath . --workpath .build-temp packaging\necropolis.spec || goto :error
rmdir /s /q .build-temp 2>nul
echo.
echo Готово: Necropolis.exe
pause
exit /b 0

:error
echo.
echo Сборка не удалась. Текст ошибки - выше.
pause
exit /b 1
