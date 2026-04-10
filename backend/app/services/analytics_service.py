"""Analytics service for system metrics and insights."""

from typing import Dict, Any
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q, Sum
from app.models import Task, Document, ActivityLog, Chunk, User


class AnalyticsService:
    """Service for generating system analytics and insights."""
    
    def get_task_analytics(self) -> Dict[str, Any]:
        """Get task-related metrics."""
        tasks = Task.objects.all()
        total_tasks = tasks.count()
        pending_tasks = tasks.filter(status='pending').count()
        completed_tasks = tasks.filter(status='completed').count()
        
        # Task assignment distribution
        task_assignments = tasks.values('assigned_to__username').annotate(
            count=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            completed=Count('id', filter=Q(status='completed')),
        )
        
        return {
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
            'task_assignments': list(task_assignments),
        }
    
    def get_document_analytics(self) -> Dict[str, Any]:
        """Get document-related metrics."""
        documents = Document.objects.all()
        total_documents = documents.count()
        total_size_bytes = sum(doc.file_size for doc in documents)
        
        # Document upload distribution by user
        uploads_by_user = documents.values('uploaded_by__username').annotate(
            count=Count('id'),
            total_size=Sum('file_size'),
        )
        
        # Chunking statistics
        chunks = Chunk.objects.all()
        total_chunks = chunks.count()
        total_tokens = chunks.aggregate(total=Sum('token_count'))['total'] or 0
        
        return {
            'total_documents': total_documents,
            'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
            'avg_doc_size_kb': round(
                total_size_bytes / total_documents / 1024, 2
            ) if total_documents > 0 else 0,
            'total_chunks': total_chunks,
            'total_tokens': total_tokens,
            'avg_chunks_per_doc': round(
                total_chunks / total_documents, 2
            ) if total_documents > 0 else 0,
            'uploads_by_user': list(uploads_by_user),
        }
    
    def get_search_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get search-related metrics."""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Count search activities
        search_logs = ActivityLog.objects.filter(
            action_type='search',
            timestamp__gte=cutoff_date,
        )
        
        total_searches = search_logs.count()
        unique_searchers = search_logs.values('user').distinct().count()
        
        # Top queries (by activity log details)
        top_queries = search_logs.values('details').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Search by user
        searches_by_user = search_logs.values('user__username').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Search result statistics
        total_results = 0
        max_results = 0
        min_results = float('inf')
        
        for log in search_logs:
            if log.details:
                import json
                try:
                    details = json.loads(log.details) if isinstance(log.details, str) else log.details
                    result_count = details.get('result_count', 0)
                    total_results += result_count
                    max_results = max(max_results, result_count)
                    min_results = min(min_results, result_count)
                except:
                    pass
        
        avg_results = round(total_results / total_searches, 2) if total_searches > 0 else 0
        
        return {
            'total_searches': total_searches,
            'unique_searchers': unique_searchers,
            'avg_results_per_search': avg_results,
            'max_results_in_search': max_results if max_results != 0 else None,
            'min_results_in_search': min_results if min_results != float('inf') else None,
            'searches_by_user': list(searches_by_user),
            'period_days': days,
        }
    
    def get_user_analytics(self) -> Dict[str, Any]:
        """Get user and role-related metrics."""
        users = User.objects.all()
        total_users = users.count()
        
        # Users by role
        users_by_role = users.values('role__role_name').annotate(count=Count('id'))
        
        # User activity
        active_users = ActivityLog.objects.values('user').distinct().count()
        
        # Activity by type
        activity_by_type = ActivityLog.objects.values('action_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'users_by_role': list(users_by_role),
            'activity_by_type': list(activity_by_type),
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        from app.services.search_service import search_service
        
        # Index health
        index_size = search_service.embedding_service.index.ntotal
        chunk_map_size = len(search_service.chunk_to_index_map)
        chunk_count = Chunk.objects.count()
        
        # Check for inconsistencies
        issues = []
        if chunk_count != chunk_map_size:
            issues.append(
                f"Chunk count ({chunk_count}) does not match index map size ({chunk_map_size})"
            )
        
        return {
            'indexed_chunks': index_size,
            'database_chunks': chunk_count,
            'chunk_map_entries': chunk_map_size,
            'index_consistent': len(issues) == 0,
            'issues': issues if issues else None,
        }
    
    def get_comprehensive_analytics(self, search_days: int = 7) -> Dict[str, Any]:
        """Get all analytics in one response."""
        return {
            'timestamp': timezone.now().isoformat(),
            'tasks': self.get_task_analytics(),
            'documents': self.get_document_analytics(),
            'search': self.get_search_analytics(days=search_days),
            'users': self.get_user_analytics(),
            'system_health': self.get_system_health(),
        }


# Global instance
analytics_service = AnalyticsService()
