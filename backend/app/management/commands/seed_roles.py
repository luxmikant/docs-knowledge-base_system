"""
Management command to seed initial roles
"""
from django.core.management.base import BaseCommand
from app.models import Role


class Command(BaseCommand):
    help = 'Seed initial roles (admin and user)'

    def handle(self, *args, **kwargs):
        roles = ['admin', 'user']
        
        for role_name in roles:
            role, created = Role.objects.get_or_create(role_name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created role: {role_name}'))
            else:
                self.stdout.write(f'Role already exists: {role_name}')
        
        self.stdout.write(self.style.SUCCESS('Roles seeded successfully'))
