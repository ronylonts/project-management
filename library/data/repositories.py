from django.db import transaction
from django.db.models import Q, F, Sum, Count, Case, When, Value, IntegerField
from django.db.models.functions import Coalesce
from . import models
from typing import Optional, List

class ProjectRepository:
    """Repository pour la gestion des opérations CRUD sur les projets"""
    
    @transaction.atomic
    def create_project(self, name: str, description: str, start_date, end_date, budget: float, manager_id: int) -> models.Project:
        """Crée un nouveau projet"""
        project = models.Project.objects.create(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            manager_id=manager_id
        )
        return project
    
    def get_project_by_id(self, project_id: int) -> Optional[models.Project]:
        """Récupère un projet par son ID"""
        try:
            return models.Project.objects.select_related('manager').prefetch_related('members', 'tasks').get(pk=project_id)
        except models.Project.DoesNotExist:
            return None
    
    def get_user_projects(self, user_id: int) -> List[models.Project]:
        """Récupère tous les projets d'un utilisateur"""
        return models.Project.objects.filter(
            Q(manager_id=user_id) | Q(members__id=user_id)
        ).distinct().select_related('manager').prefetch_related('members')
    
    @transaction.atomic
    def update_project_status(self, project_id: int, status: str) -> bool:
        """Met à jour le statut d'un projet"""
        updated = models.Project.objects.filter(pk=project_id).update(status=status)
        return updated > 0
    
    def get_project_progress(self, project_id: int) -> dict:
        """Calcule la progression globale d'un projet"""
        result = models.Task.objects.filter(project_id=project_id).aggregate(
            total_tasks=Count('id'),
            completed_tasks=Count(Case(When(status='DONE', then=1))),
            avg_progress=Coalesce(Avg('progress'), Value(0))
        )
        
        return {
            'total_tasks': result['total_tasks'],
            'completed_tasks': result['completed_tasks'],
            'completion_rate': round((result['completed_tasks'] / result['total_tasks'] * 100) if result['total_tasks'] > 0 else 0, 2),
            'avg_progress': round(result['avg_progress'], 2)
        }

class TaskRepository:
    """Repository pour la gestion des opérations CRUD sur les tâches"""
    
    @transaction.atomic
    def create_task(self, title: str, description: str, project_id: int, due_date, priority='MEDIUM') -> models.Task:
        """Crée une nouvelle tâche"""
        task = models.Task.objects.create(
            title=title,
            description=description,
            project_id=project_id,
            due_date=due_date,
            priority=priority
        )
        return task
    
    def get_task_by_id(self, task_id: int) -> Optional[models.Task]:
        """Récupère une tâche par son ID"""
        try:
            return models.Task.objects.select_related('project', 'assigned_to').get(pk=task_id)
        except models.Task.DoesNotExist:
            return None
    
    def get_project_tasks(self, project_id: int) -> List[models.Task]:
        """Récupère toutes les tâches d'un projet"""
        return models.Task.objects.filter(project_id=project_id).select_related('assigned_to')
    
    @transaction.atomic
    def assign_task(self, task_id: int, user_id: int) -> bool:
        """Assign une tâche à un utilisateur"""
        updated = models.Task.objects.filter(pk=task_id).update(assigned_to_id=user_id)
        return updated > 0
    
    @transaction.atomic
    def update_task_progress(self, task_id: int, progress: int) -> bool:
        """Met à jour la progression d'une tâche"""
        if progress < 0 or progress > 100:
            raise ValueError("La progression doit être entre 0 et 100")
        
        updated = models.Task.objects.filter(pk=task_id).update(progress=progress)
        
        if progress == 100:
            models.Task.objects.filter(pk=task_id).update(status='DONE')
        elif progress > 0:
            models.Task.objects.filter(pk=task_id).exclude(status='DONE').update(status='IN_PROGRESS')
        
        return updated > 0

class TimeEntryRepository:
    """Repository pour la gestion des entrées de temps"""
    
    @transaction.atomic
    def log_time(self, user_id: int, task_id: int, date, hours: float, description: str = '') -> models.TimeEntry:
        """Enregistre une entrée de temps"""
        if hours <= 0:
            raise ValueError("Les heures doivent être supérieures à 0")
        
        time_entry = models.TimeEntry.objects.create(
            user_id=user_id,
            task_id=task_id,
            date=date,
            hours=hours,
            description=description
        )
        return time_entry
    
    def get_user_time_entries(self, user_id: int, start_date=None, end_date=None) -> List[models.TimeEntry]:
        """Récupère les entrées de temps d'un utilisateur"""
        queryset = models.TimeEntry.objects.filter(user_id=user_id).select_related('task', 'task__project')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')

class NotificationRepository:
    """Repository pour la gestion des notifications"""
    
    @transaction.atomic
    def create_notification(self, user_id: int, message: str, notification_type: str, related_id: int) -> models.Notification:
        """Crée une nouvelle notification"""
        notification = models.Notification.objects.create(
            user_id=user_id,
            message=message,
            notification_type=notification_type,
            related_id=related_id
        )
        return notification
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False) -> List[models.Notification]:
        """Récupère les notifications d'un utilisateur"""
        queryset = models.Notification.objects.filter(user_id=user_id)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        return queryset.order_by('-created_at')
    
    @transaction.atomic
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Marque une notification comme lue"""
        updated = models.Notification.objects.filter(pk=notification_id, user_id=user_id).update(is_read=True)
        return updated > 0