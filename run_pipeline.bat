@echo off
echo ================================================================================
echo UAE Legal Documents ETL Pipeline
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Step 1: Checking dependencies...
python -c "import pdfplumber, fitz, google.generativeai, dotenv" >nul 2>&1
if errorlevel 1 (
    echo Dependencies not installed. Installing now...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
) else (
    echo Dependencies already installed.
)

echo.
echo Step 2: Verifying setup...
python test_setup.py
if errorlevel 1 (
    echo.
    echo Setup verification failed. Please fix the issues above.
    pause
    exit /b 1
)

echo.
echo Step 3: Running ETL pipeline...
echo This may take 5-15 minutes...
echo.
python main.py
if errorlevel 1 (
    echo.
    echo Pipeline execution failed. Check the logs above.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo Pipeline completed successfully!
echo Output file: extracted_data.json
echo ================================================================================
echo.
echo Run 'python analyze_output.py' to analyze the results.
echo.
pause
