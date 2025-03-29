from typing import List, Optional
from datetime import date
from django.contrib.auth import get_user_model
from ..data import models
from ..data.repositories import ProjectRepository, TaskRepository, TimeEntryRepository, NotificationRepository
from . import dtos
from . import exceptions

User = get_user_model()

class ProjectService:
    """Service pour la gestion des projets"""
    
    def __init__(self):
        self.project_repo = ProjectRepository()
        self.task_repo = TaskRepository()
        self.notification_repo = NotificationRepository()
    
    def create_project(self, name: str, description: str, start_date: date, end_date: date, budget: float, manager_id: int) -> dtos.ProjectDTO:
        """Crée un nouveau projet"""
        if end_date < start_date:
            raise exceptions.BusinessException("La date de fin doit être après la date de début")
        
        if budget <= 0:
            raise exceptions.BusinessException("Le budget doit être positif")
        
        try:
            manager = User.objects.get(pk=manager_id)
        except User.DoesNotExist:
            raise exceptions.UserNotFoundException(f"Utilisateur avec ID {manager_id} non trouvé")
        
        project = self.project_repo.create_project(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            manager_id=manager_id
        )
        
        return self._convert_project_to_dto(project)
    
    def get_project(self, project_id: int, user_id: int) -> dtos.ProjectDTO:
        """Récupère un projet par son ID"""
        project = self.project_repo.get_project_by_id(project_id)
        
        if not project:
            raise exceptions.ProjectNotFoundException(f"Projet avec ID {project_id} non trouvé")
        
        # Vérification des permissions
        if project.manager_id != user_id and not project.members.filter(id=user_id).exists():
            raise exceptions.UnauthorizedAccessException("Vous n'avez pas accès à ce projet")
        
        return self._convert_project_to_dto(project)
    
    def get_user_projects(self, user_id: int) -> List[dtos.ProjectDTO]:
        """Récupère tous les projets d'un utilisateur"""
        projects = self.project_repo.get_user_projects(user_id)
        return [self._convert_project_to_dto(p) for p in projects]
    
    def get_project_progress(self, project_id: int, user_id: int) -> dtos.ProjectProgressDTO:
        """Récupère la progression d'un projet"""
        project = self.project_repo.get_project_by_id(project_id)
        
        if not project:
            raise exceptions.ProjectNotFoundException(f"Projet avec ID {project_id} non trouvé")
        
        # Vérification des permissions
        if project.manager_id != user_id and not project.members.filter(id=user_id).exists():
            raise exceptions.UnauthorizedAccessException("Vous n'avez pas accès à ce projet")
        
        progress_data = self.project_repo.get_project_progress(project_id)
        return dtos.ProjectProgressDTO(**progress_data)
    
    def _convert_project_to_dto(self, project: models.Project) -> dtos.ProjectDTO:
        """Convertit un modèle Project en ProjectDTO"""
        manager_dto = dtos.UserDTO(
            id=project.manager.id,
            username=project.manager.username,
            email=project.manager.email,
            first_name=project.manager.first_name,
            last_name=project.manager.last_name,
            role=project.manager.role,
            department=project.manager.department,
            phone=project.manager.phone
        )
        
        members_dto = [
            dtos.UserDTO(
                id=member.id,
                username=member.username,
                email=member.email,
                first_name=member.first_name,
                last_name=member.last_name,
                role=member.role,
                department=member.department,
                phone=member.phone
            ) for member in project.members.all()
        ]
        
        return dtos.ProjectDTO(
            id=project.id,
            name=project.name,
            description=project.description,
            start_date=project.start_date,
            end_date=project.end_date,
            status=project.status,
            budget=project.budget,
            manager=manager_dto,
            members=members_dto,
            created_at=project.created_at,
            updated_at=project.updated_at
        )

class TaskService:
    """Service pour la gestion des tâches"""
    
    def __init__(self):
        self.task_repo = TaskRepository()
        self.project_repo = ProjectRepository()
        self.notification_repo = NotificationRepository()
    
    def create_task(self, title: str, description: str, project_id: int, due_date: date, priority: str = 'MEDIUM', creator_id: int) -> dtos.TaskDTO:
        """Crée une nouvelle tâche"""
        project = self.project_repo.get_project_by_id(project_id)
        
        if not project:
            raise exceptions.ProjectNotFoundException(f"Projet avec ID {project_id} non trouvé")
        
        # Vérification des permissions
        if project.manager_id != creator_id:
            raise exceptions.UnauthorizedAccessException("Seul le gestionnaire du projet peut créer des tâches")
        
        if due_date < date.today():
            raise exceptions.BusinessException("La date d'échéance ne peut pas être dans le passé")
        
        task = self.task_repo.create_task(
            title=title,
            description=description,
            project_id=project_id,
            due_date=due_date,
            priority=priority
        )
        
        return self._convert_task_to_dto(task)
    
    def assign_task(self, task_id: int, user_id: int, assigner_id: int) -> dtos.TaskDTO:
        """Assign une tâche à un utilisateur"""
        task = self.task_repo.get_task_by_id(task_id)
        
        if not task:
            raise exceptions.TaskNotFoundException(f"Tâche avec ID {task_id} non trouvée")
        
        # Vérification des permissions
        if task.project.manager_id != assigner_id:
            raise exceptions.UnauthorizedAccessException("Seul le gestionnaire du projet peut assigner des tâches")
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise exceptions.UserNotFoundException(f"Utilisateur avec ID {user_id} non trouvé")
        
        # Vérifier que l'utilisateur est membre du projet
        if not task.project.members.filter(id=user_id).exists():
            raise exceptions.BusinessException("L'utilisateur doit être membre du projet pour être assigné à une tâche")
        
        self.task_repo.assign_task(task_id, user_id)
        
        # Créer une notification
        self.notification_repo.create_notification(
            user_id=user_id,
            message=f"Vous avez été assigné à la tâche '{task.title}'",
            notification_type='ASSIGNMENT',
            related_id=task_id
        )
        
        # Récupérer la tâche mise à jour
        updated_task = self.task_repo.get_task_by_id(task_id)
        return self._convert_task_to_dto(updated_task)
    
    def update_task_progress(self, task_id: int, progress: int, user_id: int) -> dtos.TaskDTO:
        """Met à jour la progression d'une tâche"""
        task = self.task_repo.get_task_by_id(task_id)
        
        if not task:
            raise exceptions.TaskNotFoundException(f"Tâche avec ID {task_id} non trouvée")
        
        # Vérification des permissions
        if task.assigned_to_id != user_id and task.project.manager_id != user_id:
            raise exceptions.UnauthorizedAccessException("Vous n'êtes pas autorisé à modifier cette tâche")
        
        if progress < 0 or progress > 100:
            raise exceptions.InvalidProgressValueException("La progression doit être entre 0 et 100")
        
        self.task_repo.update_task_progress(task_id, progress)
        
        # Si la tâche est complétée, notifier le gestionnaire
        if progress == 100 and task.project.manager_id != user_id:
            self.notification_repo.create_notification(
                user_id=task.project.manager_id,
                message=f"La tâche '{task.title}' a été marquée comme terminée",
                notification_type='UPDATE',
                related_id=task_id
            )
        
        # Récupérer la tâche mise à jour
        updated_task = self.task_repo.get_task_by_id(task_id)
        return self._convert_task_to_dto(updated_task)
    
    def _convert_task_to_dto(self, task: models.Task) -> dtos.TaskDTO:
        """Convertit un modèle Task en TaskDTO"""
        assigned_to_dto = None
        if task.assigned_to:
            assigned_to_dto = dtos.UserDTO(
                id=task.assigned_to.id,
                username=task.assigned_to.username,
                email=task.assigned_to.email,
                first_name=task.assigned_to.first_name,
                last_name=task.assigned_to.last_name,
                role=task.assigned_to.role,
                department=task.assigned_to.department,
                phone=task.assigned_to.phone
            )
        
        depends_on_ids = [dep.id for dep in task.depends_on.all()]
        
        return dtos.TaskDTO(
            id=task.id,
            title=task.title,
            description=task.description,
            project_id=task.project_id,
            assigned_to=assigned_to_dto,
            due_date=task.due_date,
            priority=task.priority,
            status=task.status,
            progress=task.progress,
            depends_on=depends_on_ids,
            created_at=task.created_at,
            updated_at=task.updated_at
        )

class TimeTrackingService:
    """Service pour le suivi du temps"""
    
    def __init__(self):
        self.time_repo = TimeEntryRepository()
        self.task_repo = TaskRepository()
    
    def log_time(self, user_id: int, task_id: int, date: date, hours: float, description: str = '') -> dtos.TimeEntryDTO:
        """Enregistre du temps passé sur une tâche"""
        if hours <= 0:
            raise exceptions.TimeEntryValidationException("Les heures doivent être supérieures à 0")
        
        task = self.task_repo.get_task_by_id(task_id)
        
        if not task:
            raise exceptions.TaskNotFoundException(f"Tâche avec ID {task_id} non trouvée")
        
        # Vérifier que l'utilisateur est assigné à la tâche ou gestionnaire du projet
        if task.assigned_to_id != user_id and task.project.manager_id != user_id:
            raise exceptions.UnauthorizedAccessException("Vous ne pouvez pas enregistrer du temps pour cette tâche")
        
        time_entry = self.time_repo.log_time(
            user_id=user_id,
            task_id=task_id,
            date=date,
            hours=hours,
            description=description
        )
        
        return dtos.TimeEntryDTO(
            id=time_entry.id,
            user=dtos.UserDTO(
                id=time_entry.user.id,
                username=time_entry.user.username,
                email=time_entry.user.email,
                first_name=time_entry.user.first_name,
                last_name=time_entry.user.last_name,
                role=time_entry.user.role,
                department=time_entry.user.department,
                phone=time_entry.user.phone
            ),
            task_id=time_entry.task_id,
            task_title=time_entry.task.title,
            date=time_entry.date,
            hours=time_entry.hours,
            description=time_entry.description,
            created_at=time_entry.created_at
        )
    
    def get_user_time_entries(self, user_id: int, start_date: date = None, end_date: date = None) -> List[dtos.TimeEntryDTO]:
        """Récupère les entrées de temps d'un utilisateur"""
        time_entries = self.time_repo.get_user_time_entries(user_id, start_date, end_date)
        
        return [
            dtos.TimeEntryDTO(
                id=te.id,
                user=dtos.UserDTO(
                    id=te.user.id,
                    username=te.user.username,
                    email=te.user.email,
                    first_name=te.user.first_name,
                    last_name=te.user.last_name,
                    role=te.user.role,
                    department=te.user.department,
                    phone=te.user.phone
                ),
                task_id=te.task_id,
                task_title=te.task.title,
                date=te.date,
                hours=te.hours,
                description=te.description,
                created_at=te.created_at
            ) for te in time_entries
        ]

class NotificationService:
    """Service pour la gestion des notifications"""
    
    def __init__(self):
        self.notification_repo = NotificationRepository()
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False) -> List[dtos.NotificationDTO]:
        """Récupère les notifications d'un utilisateur"""
        notifications = self.notification_repo.get_user_notifications(user_id, unread_only)
        
        return [
            dtos.NotificationDTO(
                id=n.id,
                message=n.message,
                notification_type=n.notification_type,
                related_id=n.related_id,
                is_read=n.is_read,
                created_at=n.created_at
            ) for n in notifications
        ]
    
    def mark_as_read(self, notification_id: int, user_id: int) -> None:
        """Marque une notification comme lue"""
        updated = self.notification_repo.mark_as_read(notification_id, user_id)
        
        if not updated:
            raise exceptions.BusinessException("Notification non trouvée ou vous n'avez pas la permission")