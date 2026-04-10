"""
Verification script for Role and User models
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import Role, User

print("=" * 60)
print("VERIFICATION: Role and User Models")
print("=" * 60)

# Check Role model
print("\n1. Role Model:")
print(f"   - Table name: {Role._meta.db_table}")
print(f"   - Fields: {[f.name for f in Role._meta.get_fields()]}")
print(f"   - Indexes: {[idx.name for idx in Role._meta.indexes]}")

# Check User model
print("\n2. User Model:")
print(f"   - Table name: {User._meta.db_table}")
print(f"   - Fields: {[f.name for f in User._meta.get_fields()]}")
print(f"   - Indexes: {[idx.name for idx in User._meta.indexes]}")
print(f"   - USERNAME_FIELD: {User.USERNAME_FIELD}")
print(f"   - REQUIRED_FIELDS: {User.REQUIRED_FIELDS}")

# Check foreign key relationship
print("\n3. Foreign Key Relationships:")
role_field = User._meta.get_field('role')
print(f"   - User.role -> {role_field.related_model.__name__}")
print(f"   - On delete: {role_field.remote_field.on_delete.__name__}")

# Test creating instances
print("\n4. Testing Model Creation:")
try:
    # Clean up any existing test data
    Role.objects.filter(role_name='test_role').delete()
    User.objects.filter(username='test_user').delete()
    
    # Create test role
    test_role = Role.objects.create(role_name='test_role')
    print(f"   ✓ Created Role: {test_role}")
    
    # Create test user
    test_user = User.objects.create_user(
        username='test_user',
        email='test@example.com',
        password='testpass123',
        role=test_role
    )
    print(f"   ✓ Created User: {test_user}")
    print(f"   ✓ User role: {test_user.role.role_name}")
    print(f"   ✓ Password check: {test_user.check_password('testpass123')}")
    
    # Clean up
    test_user.delete()
    test_role.delete()
    print("   ✓ Cleanup successful")
    
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
