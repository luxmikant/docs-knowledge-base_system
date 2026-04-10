#!/usr/bin/env python
"""
Verification script for Task 1: Backend Project Structure Setup
This script verifies that all components of Task 1 are properly configured.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.conf import settings
from django.core.management import call_command
from app.models import Role, User


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\n=== Checking Dependencies ===")
    required_packages = [
        ('django', 'Django'),
        ('rest_framework', 'Django REST Framework'),
        ('jwt', 'PyJWT'),
        ('numpy', 'numpy'),
        ('hypothesis', 'hypothesis'),
        ('pytest', 'pytest'),
        ('dotenv', 'python-dotenv'),
    ]
    optional_packages = [
        ('sentence_transformers', 'sentence-transformers (optional AI acceleration)'),
        ('faiss', 'faiss-cpu (optional AI acceleration)'),
    ]
    
    missing = []
    for module, package in required_packages:
        try:
            __import__(module)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} NOT installed")
            missing.append(package)
    
    for module, package in optional_packages:
        try:
            __import__(module)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"! {package} not installed (fallback embedding mode will be used)")

    return len(missing) == 0, missing


def check_environment():
    """Check environment configuration"""
    print("\n=== Checking Environment Configuration ===")
    
    # Check .env file exists
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        print("✓ .env file exists")
    else:
        print("✗ .env file NOT found")
        return False
    
    # Check critical settings
    checks = [
        ('SECRET_KEY', settings.SECRET_KEY),
        ('JWT_SECRET', settings.JWT_SECRET),
        ('JWT_EXPIRATION_HOURS', settings.JWT_EXPIRATION_HOURS),
        ('MEDIA_ROOT', settings.MEDIA_ROOT),
        ('FAISS_INDEX_PATH', settings.FAISS_INDEX_PATH),
    ]
    
    all_ok = True
    for name, value in checks:
        if value:
            print(f"✓ {name} configured")
        else:
            print(f"✗ {name} NOT configured")
            all_ok = False
    
    return all_ok


def check_database():
    """Check database configuration and migrations"""
    print("\n=== Checking Database ===")
    
    try:
        # Check if migrations exist
        from django.db.migrations.loader import MigrationLoader
        loader = MigrationLoader(None, ignore_no_migrations=True)
        
        if 'app' in loader.migrated_apps:
            print("✓ Migrations exist for app")
        else:
            print("✗ No migrations found for app")
            return False
        
        # Try to query database
        Role.objects.count()
        print("✓ Database connection successful")
        
        # Check if roles are seeded
        admin_role = Role.objects.filter(role_name='admin').exists()
        user_role = Role.objects.filter(role_name='user').exists()
        
        if admin_role and user_role:
            print("✓ Roles seeded (admin, user)")
        else:
            print("✗ Roles NOT seeded")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False


def check_directories():
    """Check required directories exist"""
    print("\n=== Checking Directory Structure ===")
    
    required_dirs = [
        ('app', 'Main application directory'),
        ('app/services', 'Services directory'),
        ('app/management/commands', 'Management commands directory'),
        ('config', 'Configuration directory'),
        ('tests', 'Tests directory'),
    ]
    
    all_ok = True
    for dir_path, description in required_dirs:
        full_path = os.path.join(os.path.dirname(__file__), dir_path)
        if os.path.exists(full_path):
            print(f"✓ {description}: {dir_path}")
        else:
            print(f"✗ {description} NOT found: {dir_path}")
            all_ok = False
    
    # Check FAISS data directory
    faiss_path = settings.FAISS_INDEX_PATH
    if os.path.exists(faiss_path):
        print(f"✓ FAISS index directory: {faiss_path}")
    else:
        print(f"! FAISS index directory will be created: {faiss_path}")
        os.makedirs(faiss_path, exist_ok=True)
        print(f"✓ Created FAISS index directory")
    
    # Check media directory
    media_path = settings.MEDIA_ROOT
    if os.path.exists(media_path):
        print(f"✓ Media directory: {media_path}")
    else:
        print(f"! Media directory will be created: {media_path}")
        os.makedirs(media_path, exist_ok=True)
        print(f"✓ Created media directory")
    
    return all_ok


def check_models():
    """Check if all models are properly defined"""
    print("\n=== Checking Models ===")
    
    models = [
        ('Role', Role),
        ('User', User),
    ]
    
    all_ok = True
    for name, model in models:
        try:
            # Check if model has required fields
            model._meta.get_fields()
            print(f"✓ {name} model defined")
        except Exception as e:
            print(f"✗ {name} model error: {e}")
            all_ok = False
    
    return all_ok


def check_services():
    """Check if services are properly configured"""
    print("\n=== Checking Services ===")
    
    try:
        from app.services.embedding_service import EmbeddingService
        service = EmbeddingService()
        print("✓ EmbeddingService initialized")
        print(f"  - Model: all-MiniLM-L6-v2")
        print(f"  - Dimension: {service.dimension}")
        return True
    except Exception as e:
        print(f"✗ EmbeddingService error: {e}")
        return False


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Backend Project Structure Verification")
    print("Task 1: Set up backend project structure and core configuration")
    print("=" * 60)
    
    results = {
        'Dependencies': check_dependencies(),
        'Environment': check_environment(),
        'Directories': check_directories(),
        'Models': check_models(),
        'Database': check_database(),
        'Services': check_services(),
    }
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check, (passed, *extra) in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check:20s}: {status}")
        if not passed:
            all_passed = False
            if extra and extra[0]:  # Missing packages
                print(f"  Missing: {', '.join(extra[0])}")
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! Backend setup is complete.")
        print("\nNext steps:")
        print("1. Run: python manage.py runserver")
        print("2. Test API at: http://localhost:8000/api/")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the errors above.")
        print("\nTo fix issues:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Run migrations: python manage.py migrate")
        print("3. Seed roles: python manage.py seed_roles")
        return 1


if __name__ == '__main__':
    sys.exit(main())
