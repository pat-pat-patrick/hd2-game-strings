@echo off
rem HD2 Game Strings: export the game's text in all languages, and in English + Chinese.
cd /d "%~dp0"
where python >nul 2>nul || (echo Python was not found. Install it from https://www.python.org/ and tick "Add python.exe to PATH". & pause & exit /b 1)
python -c "import lz4" 2>nul || python -m pip install lz4
python hd2_game_strings.py export
python hd2_game_strings.py export --langs us,cn,tc
echo.
echo The files are in the output folder.
pause
