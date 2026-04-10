@echo off
setlocal

set VENV_DIR=.venv

echo Setting up AI Task ^& Knowledge Management System Backend...

REM Create virtual environment if needed
if not exist %VENV_DIR% (
	echo Creating virtual environment...
	python -m venv %VENV_DIR%
)

call %VENV_DIR%\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Run migrations
echo Running database migrations...
python manage.py migrate

REM Seed roles
echo Seeding initial roles...
python manage.py seed_roles

REM Create superuser prompt
echo.
echo Setup complete!
echo.
echo Virtual environment: %VENV_DIR%
echo Activate manually with:
echo   %VENV_DIR%\Scripts\activate
echo.
echo To create an admin user, run:
echo   python manage.py createsuperuser
echo.
echo To start the development server, run:
echo   python manage.py runserver

endlocal
