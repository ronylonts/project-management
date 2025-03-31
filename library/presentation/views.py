from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from library.data.models import Project, Task
from library.business.services import ProjectService, TaskService
from library.data.repositories import ProjectRepository, TaskRepository
from .forms import ProjectForm, TaskForm

class ProjectDashboardView(LoginRequiredMixin, ListView):
    template_name = 'projects/dashboard.html'
    model = Project
    context_object_name = 'projects'
    
    def get_queryset(self):
        return Project.objects.filter(members=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_service = ProjectService(ProjectRepository())
        task_service = TaskService(TaskRepository())
        
        context['recent_projects'] = self.get_queryset().order_by('-created_at')[:5]
        context['recent_tasks'] = Task.objects.filter(
            project__members=self.request.user
        ).order_by('-created_at')[:5]
        
        context['stats'] = {
            'active_projects': self.get_queryset().filter(status='active').count(),
            'completed_tasks': Task.objects.filter(
                status='completed',
                project__members=self.request.user
            ).count(),
            'in_progress_tasks': Task.objects.filter(
                status='in_progress',
                project__members=self.request.user
            ).count(),
            'overdue_tasks': Task.objects.filter(
                due_date__lt=timezone.now(),
                status__in=['todo', 'in_progress'],
                project__members=self.request.user
            ).count(),
        }
        
        return context

class ProjectListView(LoginRequiredMixin, ListView):
    template_name = 'projects/list.html'
    model = Project
    context_object_name = 'projects'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Project.objects.filter(members=self.request.user)
        
        # Filtrage
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        sort = self.request.GET.get('sort', '-created_at')
        
        if status:
            queryset = queryset.filter(status=status)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by(sort)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Project.Status.choices
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    template_name = 'projects/create.html'
    form_class = ProjectForm
    success_url = reverse_lazy('project_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Ajouter le créateur comme membre du projet
        self.object.members.add(self.request.user)
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_projects'] = Project.objects.filter(members=self.request.user)
        return context

class ProjectDetailView(LoginRequiredMixin, DetailView):
    template_name = 'projects/detail.html'
    model = Project
    context_object_name = 'project'
    
    def get_queryset(self):
        return Project.objects.filter(members=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_activities'] = self.object.activities.all().order_by('-created_at')[:5]
        context['available_users'] = User.objects.exclude(
            id__in=self.object.members.values_list('id', flat=True)
        )
        return context