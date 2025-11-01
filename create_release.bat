@echo off
echo =====================================
echo Creating Release Package
echo =====================================
echo.

REM Create release directory structure
if exist "release" rmdir /s /q release
mkdir release
mkdir release\PngToIco-v1.0.0

echo Copying files to release package...
REM Copy executable and essential files only
copy dist\PngToIco.exe release\PngToIco-v1.0.0\
copy icon.ico release\PngToIco-v1.0.0\
copy README.txt release\PngToIco-v1.0.0\
copy LICENSE release\PngToIco-v1.0.0\

echo.
echo Creating ZIP archive...
cd release
powershell -Command "Compress-Archive -Path 'PngToIco-v1.0.0' -DestinationPath 'PngToIco-v1.0.0-Windows.zip' -Force"
cd ..

echo.
echo =====================================
echo SUCCESS! Release package created!
echo =====================================
echo.
echo Location: release\PngToIco-v1.0.0-Windows.zip
echo.
echo Package Contents:
echo   ✓ PngToIco.exe     - Standalone application
echo   ✓ icon.ico         - Application icon
echo   ✓ README.txt       - User instructions
echo   ✓ LICENSE          - MIT License
echo.
echo Package is ready to upload to GitHub Releases!
echo Users can extract and run PngToIco.exe directly.
echo.
pause
