from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    """Modèle personnalisé d'utilisateur avec des rôles supplémentaires"""
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('MANAGER', 'Gestionnaire'),
        ('MEMBER', 'Membre'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Project(models.Model):
    """Modèle représentant un projet"""
    STATUS_CHOICES = [
        ('PLANNING', 'Planification'),
        ('IN_PROGRESS', 'En cours'),
        ('ON_HOLD', 'En attente'),
        ('COMPLETED', 'Terminé'),
        ('CANCELLED', 'Annulé'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    manager = models.ForeignKey(User, on_delete=models.PROTECT, related_name='managed_projects')
    members = models.ManyToManyField(User, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
    
    def __str__(self):
        return self.name

class Task(models.Model):
    """Modèle représentant une tâche dans un projet"""
    PRIORITY_CHOICES = [
        ('LOW', 'Basse'),
        ('MEDIUM', 'Moyenne'),
        ('HIGH', 'Haute'),
        ('CRITICAL', 'Critique'),
    ]
    
    STATUS_CHOICES = [
        ('TODO', 'À faire'),
        ('IN_PROGRESS', 'En cours'),
        ('REVIEW', 'En revue'),
        ('DONE', 'Terminé'),
        ('BLOCKED', 'Bloqué'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    due_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    progress = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    depends_on = models.ManyToManyField('self', symmetrical=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'due_date']
        verbose_name = "Tâche"
        verbose_name_plural = "Tâches"
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class TimeEntry(models.Model):
    """Modèle pour le suivi du temps passé sur les tâches"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    date = models.DateField()
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Entrée de temps"
        verbose_name_plural = "Entrées de temps"
        unique_together = ['user', 'task', 'date']
    
    def __str__(self):
        return f"{self.user} - {self.task} - {self.hours}h"

class Notification(models.Model):
    """Modèle pour les notifications utilisateur"""
    TYPE_CHOICES = [
        ('ASSIGNMENT', 'Assignation de tâche'),
        ('DEADLINE', 'Échéance proche'),
        ('UPDATE', 'Mise à jour'),
        ('COMMENT', 'Commentaire'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    related_id = models.PositiveIntegerField()  # ID de l'objet lié
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.user}"