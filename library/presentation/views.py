from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from ..business.services import ProjectService, TaskService, TimeTrackingService, NotificationService
from ..business import exceptions
from . import forms
import json

@login_required
def dashboard(request):
    """Vue pour le tableau de bord"""
    project_service = ProjectService()
    task_service = TaskService()
    notification_service = NotificationService()
    
    try:
        projects = project_service.get_user_projects(request.user.id)
        notifications = notification_service.get_user_notifications(request.user.id, unread_only=True)
        
        # Tâches assignées à l'utilisateur
        assigned_tasks = []
        for project in projects:
            tasks = task_service.get_project_tasks(project.id)
            assigned_tasks.extend([t for t in tasks if t.assigned_to and t.assigned_to.id == request.user.id and t.status != 'DONE'])
        
        # Trier par date d'échéance
        assigned_tasks.sort(key=lambda t: t.due_date)
        
        context = {
            'projects': projects,
            'assigned_tasks': assigned_tasks[:5],  # Limiter à 5 tâches
            'notifications': notifications[:5],     # Limiter à 5 notifications
        }
        
        return render(request, 'presentation/dashboard.html', context)
    
    except exceptions.BusinessException as e:
        messages.error(request, str(e))
        return render(request, 'presentation/dashboard.html')

@login_required
def project_list(request):
    """Vue pour la liste des projets"""
    project_service = ProjectService()
    
    try:
        projects = project_service.get_user_projects(request.user.id)
        return render(request, 'presentation/projects/list.html', {'projects': projects})
    
    except exceptions.BusinessException as e:
        messages.error(request, str(e))
        return render(request, 'presentation/projects/list.html', {'projects': []})

@login_required
def project_detail(request, project_id):
    """Vue pour les détails d'un projet"""
    project_service = ProjectService()
    task_service = TaskService()
    
    try:
        project = project_service.get_project(project_id, request.user.id)
        tasks = task_service.get_project_tasks(project.id)
        progress = project_service.get_project_progress(project.id, request.user.id)
        
        context = {
            'project': project,
            'tasks': tasks,
            'progress': progress,
        }
        
        return render(request, 'presentation/projects/detail.html', context)
    
    except exceptions.BusinessException as e:
        messages.error(request, str(e))
        return redirect('project_list')

@login_required
def create_project(request):
    """Vue pour la création d'un projet"""
    if request.method == 'POST':
        form = forms.ProjectForm(request.POST)
        
        if form.is_valid():
            project_service = ProjectService()
            
            try:
                project = project_service.create_project(
                    name=form.cleaned_data['name'],
                    description=form.cleaned_data['description'],
                    start_date=form.cleaned_data['start_date'],
                    end_date=form.cleaned_data['end_date'],
                    budget=form.cleaned_data['budget'],
                    manager_id=request.user.id
                )
                
                # Ajouter les membres
                for member in form.cleaned_data['members']:
                    project.members.add(member)
                
                messages.success(request, "Projet créé avec succès")
                return redirect('project_detail', project_id=project.id)
            
            except exceptions.BusinessException as e:
                messages.error(request, str(e))
    else:
        form = forms.ProjectForm()
    
    return render(request, 'presentation/projects/create.html', {'form': form})

@login_required
def create_task(request, project_id):
    """Vue pour la création d'une tâche"""
    project_service = ProjectService()
    
    try:
        project = project_service.get_project(project_id, request.user.id)
        
        # Vérifier que l'utilisateur est le gestionnaire du projet
        if project.manager.id != request.user.id:
            messages.error(request, "Seul le gestionnaire du projet peut créer des tâches")
            return redirect('project_detail', project_id=project_id)
        
        if request.method == 'POST':
            form = forms.TaskForm(request.POST, project_id=project_id)
            
            if form.is_valid():
                task_service = TaskService()
                
                task = task_service.create_task(
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description'],
                    project_id=project_id,
                    due_date=form.cleaned_data['due_date'],
                    priority=form.cleaned_data['priority'],
                    creator_id=request.user.id
                )
                
                # Ajouter les dépendances
                for dependency in form.cleaned_data['depends_on']:
                    task.depends_on.add(dependency)
                
                messages.success(request, "Tâche créée avec succès")
                return redirect('project_detail', project_id=project_id)
        else:
            form = forms.TaskForm(project_id=project_id)
        
        return render(request, 'presentation/tasks/create.html', {'form': form, 'project': project})
    
    except exceptions.BusinessException as e:
        messages.error(request, str(e))
        return redirect('project_list')

@login_required
def update_task_progress(request, task_id):
    """Vue pour mettre à jour la progression d'une tâche (AJAX)"""
    if request.method == 'POST' and request.is_ajax():
        try:
            data = json.loads(request.body)
            progress = int(data.get('progress'))
            
            task_service = TaskService()
            task = task_service.update_task_progress(task_id, progress, request.user.id)
            
            return JsonResponse({
                'success': True,
                'task': {
                    'id': task.id,
                    'progress': task.progress,
                    'status': task.status
                }
            })
        
        except exceptions.BusinessException as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Requête invalide'}, status=400)

@login_required
def log_time(request):
    """Vue pour enregistrer du temps"""
    time_service = TimeTrackingService()
    
    if request.method == 'POST':
        form = forms.TimeEntryForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                time_entry = time_service.log_time(
                    user_id=request.user.id,
                    task_id=form.cleaned_data['task'].id,
                    date=form.cleaned_data['date'],
                    hours=form.cleaned_data['hours'],
                    description=form.cleaned_data['description']
                )
                
                messages.success(request, "Temps enregistré avec succès")
                return redirect('dashboard')
            
            except exceptions.BusinessException as e:
                messages.error(request, str(e))
    else:
        form = forms.TimeEntryForm(user=request.user)
    
    return render(request, 'presentation/time/log.html', {'form': form})

@login_required
def mark_notification_as_read(request, notification_id):
    """Vue pour marquer une notification comme lue (AJAX)"""
    if request.method == 'POST' and request.is_ajax():
        notification_service = NotificationService()
        
        try:
            notification_service.mark_as_read(notification_id, request.user.id)
            return JsonResponse({'success': True})
        
        except exceptions.BusinessException as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Requête invalide'}, status=400)