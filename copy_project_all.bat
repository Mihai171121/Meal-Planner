@echo off
REM -------------------------------------------------------------
REM Script: copy_project_all.bat
REM Scop: Copiază TOT conținutul proiectului (mirror) într-un director nou,
REM       dar exclude .git pentru a nu prelua istoricul repo.
REM       /MIR sincronizează (atenție: poate șterge din destinație ce nu mai există în sursă).
REM -------------------------------------------------------------
setlocal
set "SRC_PATH=%~dp0"
set "DEST_PATH=D:\Curs Python\Meal-Planner-Pantry-OFFLINE"

ECHO ================= COPIERE COMPLETA (MIRROR FARA .git) =================
ECHO Sursa:      %SRC_PATH%
ECHO Destinatia: %DEST_PATH%
ECHO ======================================================================

IF /I "%SRC_PATH%"=="%DEST_PATH%\" (
  ECHO [EROARE] Destinatia identică cu sursa. Modifica DEST_PATH.
  EXIT /B 1
)

IF NOT EXIST "%DEST_PATH%" mkdir "%DEST_PATH%" >nul 2>&1

ECHO [INFO] Pornesc mirror (robocopy /MIR) excluzând .git și medii virtuale.
robocopy "%SRC_PATH%" "%DEST_PATH%" /MIR /R:1 /W:1 /FFT /Z /XO /XD .git .venv venv env ENV .idea .vscode dist build *.egg-info
SET RC=%ERRORLEVEL%

IF %RC% GEQ 8 (
  ECHO [EROARE] Copiere eșuată (cod=%RC%).
  EXIT /B %RC%
) ELSE (
  ECHO [OK] Copiere finalizată (cod robocopy=%RC%).
)

IF EXIST "%DEST_PATH%\.git" (
  ECHO [INFO] Șterg .git din destinație pentru a decupla de repository.
  rmdir /S /Q "%DEST_PATH%\.git" >nul 2>&1
)

ECHO.
IF EXIST "%DEST_PATH%\meal\main.py" echo   - meal/main.py OK
IF EXIST "%DEST_PATH%\README.md" echo   - README.md OK

ECHO (Opțional) Initializare git nou:
ECHO   cd /d "%DEST_PATH%" && git init && git add . && git commit -m "Initial offline copy"
ECHO ======================================================================
ECHO Gata. Copia completă (mirror) este în: %DEST_PATH%
ECHO ======================================================================
endlocal
EXIT /B 0
