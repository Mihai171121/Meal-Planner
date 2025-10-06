@echo off
REM -------------------------------------------------------------
REM Script: copy_project_clean.bat
REM Scop: Creează o copie a proiectului într-un director separat
REM       fără a o conecta la Git (exclude .git și medii virtuale / fișiere IDE).
REM       Include fallback la PowerShell dacă robocopy eșuează.
REM -------------------------------------------------------------
setlocal EnableDelayedExpansion

REM CONFIG
set "DEST_PATH=D:\Curs Python\Meal-Planner"

pushd "%~dp0" >nul
set "SRC_PATH=%CD%"

ECHO -------------------------------------------------------------
ECHO Sursa:      %SRC_PATH%\
ECHO Destinatia: %DEST_PATH%
ECHO -------------------------------------------------------------

IF /I "%SRC_PATH%\"=="%DEST_PATH%\" (
  ECHO [EROARE] Destinatia este identica cu sursa. Modifica DEST_PATH.
  popd >nul
  EXIT /B 1
)

IF NOT EXIST "%DEST_PATH%" (
  ECHO [INFO] Creez destinatia...
  mkdir "%DEST_PATH%" >nul 2>&1
)

ECHO.
ECHO [PAS 1] Copiere cu ROBOCOPY...
robocopy "%SRC_PATH%" "%DEST_PATH%" /E /R:1 /W:1 /XO /XD .git .venv venv env ENV .idea .vscode dist build *.egg-info >nul
SET RC=%ERRORLEVEL%

IF %RC% GEQ 8 (
  ECHO [AVERTISMENT] Robocopy a esuat (cod=%RC%). Incerc fallback PowerShell...
  powershell -NoLogo -Command "Copy-Item -Path '%SRC_PATH%\*' -Destination '%DEST_PATH%' -Recurse -Force -ErrorAction Stop" 2>nul
  IF ERRORLEVEL 1 (
    ECHO [EROARE] Fallback PowerShell a esuat. Oprire.
    GOTO :END
  ) ELSE (
    ECHO [OK] Fallback PowerShell a reusit.
  )
) ELSE (
  ECHO [OK] Robocopy finalizat (cod=%RC%).
)

ECHO.
ECHO [PAS 2] Verificare fișiere cheie...
IF EXIST "%DEST_PATH%\README.md" (ECHO   - README.md OK) ELSE (ECHO   - README.md LIPSESTE)
IF EXIST "%DEST_PATH%\meal\main.py" (ECHO   - meal/main.py OK) ELSE (ECHO   - meal/main.py LIPSESTE)
IF EXIST "%DEST_PATH%\requirements.txt" (ECHO   - requirements.txt OK) ELSE (ECHO   - requirements.txt LIPSESTE)

ECHO.
ECHO Primele 15 elemente din destinație:
set /a COUNT=0
for /f "delims=" %%F in ('dir /b "%DEST_PATH%"') do (
  set /a COUNT+=1
  echo   * %%F
  if !COUNT! GEQ 15 goto short_list_done
)
:short_list_done

ECHO.
ECHO (Optional) Pentru a initializa un nou repository Git:
ECHO   cd /d "%DEST_PATH%" && git init && git add . && git commit -m "Initial offline copy"

:END
ECHO -------------------------------------------------------------
ECHO [FINAL] Copia offline este în: %DEST_PATH%
ECHO Deschide in Explorer: explorer "%DEST_PATH%"
ECHO -------------------------------------------------------------

popd >nul
endlocal
EXIT /B 0
