call ..\.venv\Scripts\activate.bat
python -m uvicorn meal.api.api_run:app --reload --host 0.0.0.0 --port 8000
pause
