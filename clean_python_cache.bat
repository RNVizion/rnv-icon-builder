@echo off
echo Cleaning Python cache files...

:: Remove __pycache__ directories
for /d /r %%d in (__pycache__) do (
    if exist "%%d" (
        echo Removing: %%d
        rmdir /s /q "%%d"
    )
)

:: Remove .pyc and .pyo files
for /r %%f in (*.pyc *.pyo) do (
    if exist "%%f" (
        echo Removing: %%f
        del /q "%%f"
    )
)

echo Done.
pause
