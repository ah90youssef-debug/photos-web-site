@echo off
chcp 65001 >nul
title سـجل المدرسين - تشغيل تلقائي

:: =============================
::  إعداد بيئة التشغيل
:: =============================

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

:: إيقاف أي عمليات سابقة قد تتداخل
taskkill /f /im cloudflared.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im python_embed\python.exe >nul 2>&1

:: =============================
::  1. تشغيل خادم Flask باستخدام نسخة Python المضمنة
:: =============================

echo [1/3] تشغيل خادم Flask على المنفذ 5000 ...
start "Flask Server" /min cmd /c "python_embed\python.exe app.py"

:: الانتظار قليلاً حتى يبدأ الخادم
timeout /t 3 /nobreak >nul

:: اختبار الخادم المحليor /f "delims=" %%A in ('powershell -Command "try { (Invoke-WebRequest -Uri http://127.0.0.1:5000 -UseBasicParsing).StatusCode } catch { $_ }"') do set "SERVER_STATUS=%%A"
if "%SERVER_STATUS%" NEQ "200" (
    echo [✗] فشل تشغيل خادم Flask. حالة الاستجابة: %SERVER_STATUS%
    type server_out.log
    pause
    exit /b 1
) else (
    echo [✔] خادم Flask يعمل على http://localhost:5000
)

:: =============================
::  2. تشغيل نفق Cloudflare لتوفير رابط عام
:: =============================

echo [2/3] بدء نفق Cloudflare ...
if exist "tunnel.log" del /f /q "tunnel.log" >nul 2>&1
start "Cloudflare Tunnel" cmd /k "cloudflared.exe tunnel --url http://127.0.0.1:5000 --logfile tunnel.log"

:: الانتظار لاستخراج الرابط العام
echo.
echo [3/3] انتظار استخراج الرابط العام...
powershell -Command "$timeout = 30; while ($timeout -gt 0) { if (Test-Path 'tunnel.log') { $match = Select-String -Path 'tunnel.log' -Pattern 'https://[a-zA-Z0-9-]+\\.trycloudflare\\.com' | Select-Object -First 1; if ($match) { Write-Host ''; Write-Host '======================================================' -ForegroundColor Green; Write-Host ' ✅ تم تشغيل الموقع بنجاح ورابطك العام هو:' -ForegroundColor Yellow; Write-Host ('   ' + $match.Matches.Value) -ForegroundColor Cyan; Write-Host '======================================================' -ForegroundColor Green; Write-Host 'شارك هذا الرابط مع أي شخص من أي جهاز للمشاهدة والإضافة!'; break; } }; Start-Sleep -Seconds 1; $timeout-- }"

:: فتح المتصفح مع العنوان المحلي
start "" "http://localhost:5000"

echo.
echo اضغط أي زر لإغلاق هذه النافذة (الخادم والنفق سيظلان يعملان في الخلفية).
pause >nul