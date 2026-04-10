#!/usr/bin/env python
"""
Complete setup script for Task 1: Backend Project Structure Setup
This script performs all necessary setup steps.
"""
import os
import sys
import subprocess


def run_command(command, description, cwd=None):
    """Run a command and report status"""
    print(f"\n→ {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ {description} completed")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def main():
    """Run complete setup"""
    print("=" * 60)
    print("Backend Project Complete Setup")
    print("Task 1: Set up backend project structure and core configuration")
    print("=" * 60)
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    steps = [
        # Step 0: Upgrade pip
        (
            f'"{sys.executable}" -m pip install --upgrade pip',
            'Upgrading pip',
            backend_dir
        ),
        # Step 1: Install dependencies
        (
            f'"{sys.executable}" -m pip install -r requirements.txt',
            "Installing dependencies",
            backend_dir
        ),
        # Step 2: Create migrations
        (
            "python manage.py makemigrations",
            "Creating database migrations",
            backend_dir
        ),
        # Step 3: Apply migrations
        (
            "python manage.py migrate",
            "Applying database migrations",
            backend_dir
        ),
        # Step 4: Seed roles
        (
            "python manage.py seed_roles",
            "Seeding initial roles",
            backend_dir
        ),
    ]
    
    failed_steps = []
    for command, description, cwd in steps:
        if not run_command(command, description, cwd):
            failed_steps.append(description)
    
    # Create required directories
    print("\n→ Creating required directories...")
    dirs_to_create = [
        os.path.join(backend_dir, 'data'),
        os.path.join(backend_dir, 'media'),
        os.path.join(backend_dir, 'media', 'documents'),
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✓ Created: {dir_path}")
    
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    
    if not failed_steps:
        print("\n✓ All setup steps completed successfully!")
        print("\nBackend project structure is ready:")
        print("  ✓ Dependencies installed")
        print("  ✓ Database configured")
        print("  ✓ Migrations applied")
        print("  ✓ Roles seeded")
        print("  ✓ Directories created")
        print("\nNext steps:")
        print("1. Create a superuser: python manage.py createsuperuser")
        print("2. Run the server: python manage.py runserver")
        print("3. Test the API at: http://localhost:8000/api/")
        return 0
    else:
        print("\n✗ Some setup steps failed:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nPlease review the errors above and try again.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
