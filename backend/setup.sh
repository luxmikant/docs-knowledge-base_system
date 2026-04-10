#!/bin/bash

set -e

VENV_DIR=".venv"

echo "Setting up AI Task & Knowledge Management System Backend..."

if [ ! -d "$VENV_DIR" ]; then
	echo "Creating virtual environment..."
	python -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# Install dependencies
echo "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Seed roles
echo "Seeding initial roles..."
python manage.py seed_roles

# Create superuser prompt
echo ""
echo "Setup complete!"
echo ""
echo "Virtual environment: $VENV_DIR"
echo "Activate manually with:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To create an admin user, run:"
echo "  python manage.py createsuperuser"
echo ""
echo "To start the development server, run:"
echo "  python manage.py runserver"
