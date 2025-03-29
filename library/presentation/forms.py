from django import forms
from django.core.exceptions import ValidationError
from ..data import models

class ProjectForm(forms.ModelForm):
    """Formulaire pour la création et modification de projets"""
    class Meta:
        model = models.Project
        fields = ['name', 'description', 'start_date', 'end_date', 'budget', 'members']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError("La date de fin doit être après la date de début")
        
        return cleaned_data

class TaskForm(forms.ModelForm):
    """Formulaire pour la création et modification de tâches"""
    class Meta:
        model = models.Task
        fields = ['title', 'description', 'due_date', 'priority', 'assigned_to', 'depends_on']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'depends_on': forms.SelectMultiple(attrs={'class': 'select2'}),
        }
    
    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id', None)
        super().__init__(*args, **kwargs)
        
        if project_id:
            # Filtrer les tâches dépendantes pour n'inclure que celles du même projet
            self.fields['depends_on'].queryset = models.Task.objects.filter(project_id=project_id).exclude(pk=self.instance.pk)
            
            # Filtrer les utilisateurs assignables pour n'inclure que les membres du projet
            self.fields['assigned_to'].queryset = models.User.objects.filter(
                Q(managed_projects__id=project_id) | Q(projects__id=project_id)
            ).distinct()
    
    def clean(self):
        cleaned_data = super().clean()
        due_date = cleaned_data.get('due_date')
        
        if due_date and due_date < date.today():
            raise ValidationError("La date d'échéance ne peut pas être dans le passé")
        
        return cleaned_data

class TimeEntryForm(forms.ModelForm):
    """Formulaire pour l'enregistrement du temps"""
    class Meta:
        model = models.TimeEntry
        fields = ['task', 'date', 'hours', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filtrer les tâches pour n'inclure que celles assignées à l'utilisateur
            self.fields['task'].queryset = models.Task.objects.filter(
                Q(assigned_to=user) | Q(project__manager=user)
            ).distinct()
    
    def clean_hours(self):
        hours = self.cleaned_data.get('hours')
        if hours <= 0:
            raise ValidationError("Les heures doivent être supérieures à 0")
        return hours