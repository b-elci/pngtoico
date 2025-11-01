@echo off
echo Creating release package...

REM Create release directory
if not exist "release" mkdir release
cd release
if exist "pngtoico" rmdir /s /q pngtoico
mkdir pngtoico

REM Copy necessary files (executable and docs only)
copy ..\dist\PngToIco.exe pngtoico\
copy ..\README.md pngtoico\
copy ..\LICENSE pngtoico\
copy ..\sreenshot.png pngtoico\

REM Create ZIP file using PowerShell
powershell -Command "Compress-Archive -Path 'pngtoico' -DestinationPath 'pngtoico-v1.0.0-windows.zip' -Force"

echo.
echo Release package created: release\pngtoico-v1.0.0-windows.zip
echo.
echo Contents:
echo - PngToIco.exe (Standalone executable)
echo - README.md
echo - LICENSE
echo - sreenshot.png
echo.
pause
