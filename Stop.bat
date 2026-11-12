@echo off
chcp 65001 >nul
title إيقاف سجل المدرسين

echo ======================================================
echo          🛑 جاري إيقاف السيرفر ونفق Cloudflare...
echo ======================================================
echo.

:: إيقاف نفق Cloudflare
taskkill /f /im cloudflared.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [✔] تم إيقاف نفق Cloudflare بنجاح.
) else (
    echo [-] نفق Cloudflare لم يكن قيد التشغيل.
)

:: إيقاف سيرفر بايثون المخصص للمشروع
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*python_embed\python.exe app.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1

echo [✔] تم إيقاف السيرفر المحلي بأمان.
echo.
echo ======================================================
echo              تم إيقاف البرنامج بالكامل!
echo ======================================================
timeout /t 3 >nul
