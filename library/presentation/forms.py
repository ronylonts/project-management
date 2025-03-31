from django import forms
from library.data.models import Project, Task

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date', 'status', 'budget']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("La date de fin doit être postérieure à la date de début")
        
        return cleaned_data

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'status', 'priority', 'due_date', 'assigned_to', 'tags']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['project'].queryset = Project.objects.filter(members=self.user)
            self.fields['assigned_to'].queryset = User.objects.filter(
                projectmembership__project__in=self.user.managed_projects.all()
            ).distinct()
    
    def clean(self):
        cleaned_data = super().clean()
        due_date = cleaned_data.get('due_date')
        project = cleaned_data.get('project')
        
        if due_date and project:
            if due_date < project.start_date:
                raise forms.ValidationError(
                    "La date d'échéance ne peut pas être antérieure au début du projet"
                )
            if due_date > project.end_date:
                raise forms.ValidationError(
                    "La date d'échéance ne peut pas être postérieure à la fin du projet"
                )
        
        return cleaned_data