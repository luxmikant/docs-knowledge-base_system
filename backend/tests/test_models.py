"""
Unit tests for Role, User, and Document models
"""
from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone
from app.models import Role, User, Document


pytestmark = pytest.mark.django_db


class TestRoleModel:
    """Test Role model functionality"""
    
    def test_create_role(self):
        """Test creating a role"""
        role = Role.objects.create(role_name='test_admin')
        assert role.id is not None
        assert role.role_name == 'test_admin'
        assert role.created_at is not None
    
    def test_role_name_unique(self):
        """Test that role_name must be unique"""
        Role.objects.create(role_name='unique_role')
        with pytest.raises(IntegrityError):
            Role.objects.create(role_name='unique_role')
    
    def test_role_str_representation(self):
        """Test role string representation"""
        role = Role.objects.create(role_name='test_user')
        assert str(role) == 'test_user'


class TestUserModel:
    """Test User model functionality"""
    
    def test_create_user_with_manager(self):
        """Test creating a user using UserManager"""
        role, _ = Role.objects.get_or_create(role_name='user')
        user = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123',
            role=role
        )
        assert user.id is not None
        assert user.username == 'testuser1'
        assert user.email == 'test1@example.com'
        assert user.role == role
        assert user.check_password('testpass123')
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            username='admin_test',
            email='admin_test@example.com',
            password='adminpass123'
        )
        assert user.id is not None
        assert user.username == 'admin_test'
        assert user.role.role_name == 'admin'
        assert user.check_password('adminpass123')
    
    def test_username_unique(self):
        """Test that username must be unique"""
        role, _ = Role.objects.get_or_create(role_name='user')
        User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='pass123',
            role=role
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='testuser2',
                email='test3@example.com',
                password='pass123',
                role=role
            )
    
    def test_email_unique(self):
        """Test that email must be unique"""
        role, _ = Role.objects.get_or_create(role_name='user')
        User.objects.create_user(
            username='user3',
            email='test4@example.com',
            password='pass123',
            role=role
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='user4',
                email='test4@example.com',
                password='pass123',
                role=role
            )
    
    def test_user_role_foreign_key(self):
        """Test user-role foreign key relationship"""
        role, _ = Role.objects.get_or_create(role_name='user')
        user = User.objects.create_user(
            username='testuser5',
            email='test5@example.com',
            password='pass123',
            role=role
        )
        assert user.role.id == role.id
        assert user.role.role_name == 'user'
    
    def test_user_str_representation(self):
        """Test user string representation"""
        role, _ = Role.objects.get_or_create(role_name='user')
        user = User.objects.create_user(
            username='testuser6',
            email='test6@example.com',
            password='pass123',
            role=role
        )
        assert str(user) == 'testuser6'
    
    def test_user_timestamps(self):
        """Test that created_at and updated_at are set"""
        role, _ = Role.objects.get_or_create(role_name='user')
        user = User.objects.create_user(
            username='testuser7',
            email='test7@example.com',
            password='pass123',
            role=role
        )
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_username_field_configuration(self):
        """Test that USERNAME_FIELD is set correctly"""
        assert User.USERNAME_FIELD == 'username'
        assert 'email' in User.REQUIRED_FIELDS



class TestDocumentModel:
    """Test Document model functionality"""
    
    def test_create_document(self, admin_user):
        """Test creating a document with all required fields"""
        document = Document.objects.create(
            filename='test_document.txt',
            file_path='/media/documents/test_document.txt',
            file_size=1024,
            uploaded_by=admin_user,
            content_text='This is test content'
        )
        assert document.id is not None
        assert document.filename == 'test_document.txt'
        assert document.file_path == '/media/documents/test_document.txt'
        assert document.file_size == 1024
        assert document.uploaded_by == admin_user
        assert document.content_text == 'This is test content'
        assert document.upload_date is not None
    
    def test_document_filename_field(self, admin_user):
        """Test document filename field"""
        document = Document.objects.create(
            filename='my_file.txt',
            file_path='/path/to/file.txt',
            file_size=500,
            uploaded_by=admin_user
        )
        assert document.filename == 'my_file.txt'
        assert len(document.filename) <= 255  # Max length check
    
    def test_document_file_path_field(self, admin_user):
        """Test document file_path field"""
        long_path = '/media/documents/' + 'a' * 450 + '.txt'
        document = Document.objects.create(
            filename='test.txt',
            file_path=long_path,
            file_size=100,
            uploaded_by=admin_user
        )
        assert document.file_path == long_path
        assert len(document.file_path) <= 500  # Max length check
    
    def test_document_file_size_field(self, admin_user):
        """Test document file_size field stores integer bytes"""
        document = Document.objects.create(
            filename='large_file.txt',
            file_path='/media/documents/large_file.txt',
            file_size=10485760,  # 10MB in bytes
            uploaded_by=admin_user
        )
        assert document.file_size == 10485760
        assert isinstance(document.file_size, int)
    
    def test_document_uploaded_by_foreign_key(self, admin_user, regular_user):
        """Test document uploaded_by foreign key relationship"""
        doc1 = Document.objects.create(
            filename='admin_doc.txt',
            file_path='/media/documents/admin_doc.txt',
            file_size=100,
            uploaded_by=admin_user
        )
        doc2 = Document.objects.create(
            filename='user_doc.txt',
            file_path='/media/documents/user_doc.txt',
            file_size=200,
            uploaded_by=regular_user
        )
        
        assert doc1.uploaded_by.id == admin_user.id
        assert doc1.uploaded_by.username == 'admin'
        assert doc2.uploaded_by.id == regular_user.id
        assert doc2.uploaded_by.username == 'user1'
    
    def test_document_upload_date_auto_set(self, admin_user):
        """Test that upload_date is automatically set on creation"""
        before_creation = timezone.now()
        document = Document.objects.create(
            filename='test.txt',
            file_path='/media/documents/test.txt',
            file_size=100,
            uploaded_by=admin_user
        )
        after_creation = timezone.now()
        
        assert document.upload_date is not None
        assert before_creation <= document.upload_date <= after_creation
    
    def test_document_content_text_optional(self, admin_user):
        """Test that content_text field is optional (can be null/blank)"""
        document = Document.objects.create(
            filename='empty_content.txt',
            file_path='/media/documents/empty_content.txt',
            file_size=0,
            uploaded_by=admin_user,
            content_text=None
        )
        assert document.content_text is None
        
        # Test with blank string
        document2 = Document.objects.create(
            filename='blank_content.txt',
            file_path='/media/documents/blank_content.txt',
            file_size=0,
            uploaded_by=admin_user,
            content_text=''
        )
        assert document2.content_text == ''
    
    def test_document_content_text_stores_large_text(self, admin_user):
        """Test that content_text can store large text content"""
        large_content = 'Lorem ipsum ' * 10000  # Large text
        document = Document.objects.create(
            filename='large_content.txt',
            file_path='/media/documents/large_content.txt',
            file_size=len(large_content),
            uploaded_by=admin_user,
            content_text=large_content
        )
        assert document.content_text == large_content
        assert len(document.content_text) > 100000
    
    def test_document_cascade_delete_on_user_deletion(self, admin_user):
        """Test that documents are deleted when user is deleted (CASCADE)"""
        document = Document.objects.create(
            filename='test.txt',
            file_path='/media/documents/test.txt',
            file_size=100,
            uploaded_by=admin_user
        )
        document_id = document.id
        
        # Delete the user
        admin_user.delete()
        
        # Document should be deleted due to CASCADE
        assert not Document.objects.filter(id=document_id).exists()
    
    def test_document_str_representation(self, admin_user):
        """Test document string representation"""
        document = Document.objects.create(
            filename='my_document.txt',
            file_path='/media/documents/my_document.txt',
            file_size=100,
            uploaded_by=admin_user
        )
        assert str(document) == 'my_document.txt'
    
    def test_document_db_table_name(self):
        """Test that Document model uses correct database table name"""
        assert Document._meta.db_table == 'documents'
    
    def test_document_uploaded_by_index_exists(self):
        """Test that index exists on uploaded_by field"""
        indexes = [index.fields for index in Document._meta.indexes]
        assert ['uploaded_by'] in indexes
    
    def test_document_upload_date_index_exists(self):
        """Test that index exists on upload_date field"""
        indexes = [index.fields for index in Document._meta.indexes]
        assert ['upload_date'] in indexes
    
    def test_multiple_documents_same_user(self, admin_user):
        """Test that a user can upload multiple documents"""
        doc1 = Document.objects.create(
            filename='doc1.txt',
            file_path='/media/documents/doc1.txt',
            file_size=100,
            uploaded_by=admin_user
        )
        doc2 = Document.objects.create(
            filename='doc2.txt',
            file_path='/media/documents/doc2.txt',
            file_size=200,
            uploaded_by=admin_user
        )
        doc3 = Document.objects.create(
            filename='doc3.txt',
            file_path='/media/documents/doc3.txt',
            file_size=300,
            uploaded_by=admin_user
        )
        
        user_documents = Document.objects.filter(uploaded_by=admin_user)
        assert user_documents.count() == 3
        assert doc1 in user_documents
        assert doc2 in user_documents
        assert doc3 in user_documents
    
    def test_document_query_by_uploaded_by(self, admin_user, regular_user):
        """Test querying documents by uploaded_by (tests index usage)"""
        # Create documents for different users
        for i in range(5):
            Document.objects.create(
                filename=f'admin_doc_{i}.txt',
                file_path=f'/media/documents/admin_doc_{i}.txt',
                file_size=100 * i,
                uploaded_by=admin_user
            )
        
        for i in range(3):
            Document.objects.create(
                filename=f'user_doc_{i}.txt',
                file_path=f'/media/documents/user_doc_{i}.txt',
                file_size=50 * i,
                uploaded_by=regular_user
            )
        
        admin_docs = Document.objects.filter(uploaded_by=admin_user)
        user_docs = Document.objects.filter(uploaded_by=regular_user)
        
        assert admin_docs.count() == 5
        assert user_docs.count() == 3
    
    def test_document_query_by_upload_date(self, admin_user):
        """Test querying documents by upload_date (tests index usage)"""
        doc1 = Document.objects.create(
            filename='doc1.txt',
            file_path='/media/documents/doc1.txt',
            file_size=100,
            uploaded_by=admin_user
        )

        # Make this deterministic across databases with coarse timestamp precision.
        doc1.upload_date = timezone.now() - timedelta(minutes=1)
        doc1.save(update_fields=['upload_date'])
        
        # Query documents uploaded after a certain time
        cutoff_time = timezone.now()
        
        doc2 = Document.objects.create(
            filename='doc2.txt',
            file_path='/media/documents/doc2.txt',
            file_size=200,
            uploaded_by=admin_user
        )
        
        recent_docs = Document.objects.filter(upload_date__gte=cutoff_time)
        assert doc2 in recent_docs
        assert doc1 not in recent_docs
    
    def test_document_ordering_by_upload_date(self, admin_user):
        """Test ordering documents by upload_date"""
        doc1 = Document.objects.create(
            filename='first.txt',
            file_path='/media/documents/first.txt',
            file_size=100,
            uploaded_by=admin_user
        )
        doc2 = Document.objects.create(
            filename='second.txt',
            file_path='/media/documents/second.txt',
            file_size=200,
            uploaded_by=admin_user
        )
        doc3 = Document.objects.create(
            filename='third.txt',
            file_path='/media/documents/third.txt',
            file_size=300,
            uploaded_by=admin_user
        )
        
        # Order by upload_date descending (newest first)
        docs = Document.objects.order_by('-upload_date')
        docs_list = list(docs)
        
        assert docs_list[0] == doc3
        assert docs_list[1] == doc2
        assert docs_list[2] == doc1
    
    def test_document_special_characters_in_filename(self, admin_user):
        """Test document with special characters in filename"""
        special_filename = 'test-file_v2.0 (final).txt'
        document = Document.objects.create(
            filename=special_filename,
            file_path='/media/documents/test-file_v2.0_(final).txt',
            file_size=100,
            uploaded_by=admin_user
        )
        assert document.filename == special_filename
    
    def test_document_unicode_content(self, admin_user):
        """Test document with unicode content"""
        unicode_content = 'Hello 世界 🌍 Привет مرحبا'
        document = Document.objects.create(
            filename='unicode_test.txt',
            file_path='/media/documents/unicode_test.txt',
            file_size=len(unicode_content.encode('utf-8')),
            uploaded_by=admin_user,
            content_text=unicode_content
        )
        assert document.content_text == unicode_content
    
    def test_document_zero_file_size(self, admin_user):
        """Test document with zero file size (empty file)"""
        document = Document.objects.create(
            filename='empty.txt',
            file_path='/media/documents/empty.txt',
            file_size=0,
            uploaded_by=admin_user,
            content_text=''
        )
        assert document.file_size == 0
        assert document.content_text == ''
