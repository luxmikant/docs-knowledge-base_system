from django.contrib import admin
from .models import Role, User, Document, Task, ActivityLog

admin.site.register(Role)
admin.site.register(User)
admin.site.register(Document)
admin.site.register(Task)
admin.site.register(ActivityLog)
