@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")

echo.
echo   scraperpro by loredans
echo   ----------
echo    1  Princeton Tec
echo    2  Crispi
echo    3  Oakley SI
echo    4  Princeton Tec + Crispi
echo.
set "BRANDS="
set /p "CHOICE=  Pick a site [1-4]: "
if "%CHOICE%"=="1" set "BRANDS=princetontec"
if "%CHOICE%"=="2" set "BRANDS=crispi"
if "%CHOICE%"=="3" set "BRANDS=oakleysi"
if "%CHOICE%"=="4" set "BRANDS=princetontec crispi"
if not defined BRANDS goto :bad

echo.
echo    m  Matrixify layout   (default - matches the sample)
echo    s  Native Shopify CSV (built-in importer)
echo    b  Both
echo.
set "FMTS=matrixify"
set /p "FMT=  Format [m]: "
if /i "%FMT%"=="s" set "FMTS=shopify"
if /i "%FMT%"=="b" set "FMTS=matrixify shopify"

echo.
set "LIM="
set /p "LIM=  Limit - how many products (blank = all): "
if "%BRANDS%"=="oakleysi" if "!LIM!"=="" set "LIM=10"

set "EXTRA="
if not "!LIM!"=="" set "EXTRA=--limit !LIM!"

set "DLIMG=n"
if "%BRANDS%"=="oakleysi" (
    set /p "FAST=  Fast mode? 1 request/product, ~3x more before Akamai blocks [y/N]: "
    if /i "!FAST!"=="y" set "EXTRA=!EXTRA! --fast"
    set /p "DLIMG=  Download images too? [y/N]: "
    if /i "!DLIMG!"=="y" set "EXTRA=!EXTRA! --images"
)

for %%F in (!FMTS!) do (
    echo.
    echo   ^>^> %PY% run.py %BRANDS% --format %%F !EXTRA!
    %PY% run.py %BRANDS% --format %%F !EXTRA!
)

if not "%BRANDS%"=="oakleysi" goto :done
if /i not "!DLIMG!"=="y" goto :done
echo.
set /p "REHOST=  Re-host images to R2 and rewrite the CSV now? [y/N]: "
if /i not "!REHOST!"=="y" goto :done
for %%F in (!FMTS!) do (
    if /i "%%F"=="matrixify" ( set "CSV=output\oakleysi_shopify.csv" ) else ( set "CSV=output\oakleysi_shopify-native.csv" )
    echo   ^>^> %PY% tools\rehost_images.py !CSV! --prefix oakley
    %PY% tools\rehost_images.py !CSV! --prefix oakley
)
goto :validate

:bad
echo   invalid choice
goto :end

:validate
echo.
set /p "QA=  Run the validator on the output? [Y/n]: "
if /i "!QA!"=="n" goto :done
for %%B in (%BRANDS%) do (
    for %%F in (!FMTS!) do (
        if /i "%%F"=="matrixify" ( set "SFX=shopify" ) else ( set "SFX=shopify-native" )
        set "CSV=output\%%B_!SFX!.csv"
        if exist "output\%%B_!SFX!.r2.csv" set "CSV=output\%%B_!SFX!.r2.csv"
        if exist "!CSV!" (
            echo.
            echo   ^>^> %PY% tools\validate.py !CSV!
            %PY% tools\validate.py !CSV!
        )
    )
)

:done
echo.
echo   ============================================
echo     SCRAPING COMPLETE  -  files in output\
echo   ============================================

:end
echo.
pause
