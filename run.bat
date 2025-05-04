@echo off

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Run the application
echo Starting the FastAPI application...
uvicorn main:app --reload --host 0.0.0.0 --port 8000