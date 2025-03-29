from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

@dataclass
class UserDTO:
    """DTO pour les utilisateurs"""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    department: Optional[str]
    phone: Optional[str]

@dataclass
class ProjectDTO:
    """DTO pour les projets"""
    id: int
    name: str
    description: str
    start_date: date
    end_date: date
    status: str
    budget: float
    manager: UserDTO
    members: List[UserDTO]
    created_at: datetime
    updated_at: datetime
    
    @property
    def days_remaining(self) -> int:
        """Nombre de jours restants avant la fin du projet"""
        return (self.end_date - date.today()).days if self.end_date > date.today() else 0

@dataclass
class TaskDTO:
    """DTO pour les tâches"""
    id: int
    title: str
    description: str
    project_id: int
    assigned_to: Optional[UserDTO]
    due_date: date
    priority: str
    status: str
    progress: int
    depends_on: List[int]  # IDs des tâches dépendantes
    created_at: datetime
    updated_at: datetime
    
    @property
    def is_overdue(self) -> bool:
        """Vérifie si la tâche est en retard"""
        return self.due_date < date.today() and self.status != 'DONE'

@dataclass
class TimeEntryDTO:
    """DTO pour les entrées de temps"""
    id: int
    user: UserDTO
    task_id: int
    task_title: str
    date: date
    hours: float
    description: str
    created_at: datetime

@dataclass
class NotificationDTO:
    """DTO pour les notifications"""
    id: int
    message: str
    notification_type: str
    related_id: int
    is_read: bool
    created_at: datetime

@dataclass
class ProjectProgressDTO:
    """DTO pour la progression d'un projet"""
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    avg_progress: float