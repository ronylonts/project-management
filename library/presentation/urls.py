from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.ProjectDashboardView.as_view(), name='project_dashboard'),
    
    # Projects
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('projects/<int:project_id>/add-member/', views.ProjectAddMemberView.as_view(), name='project_add_member'),
    path('projects/<int:project_id>/upload-file/', views.ProjectUploadFileView.as_view(), name='project_upload_file'),
    
    # Tasks
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('projects/<int:project_id>/tasks/create/', views.TaskCreateView.as_view(), name='task_create_for_project'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/update/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:pk>/complete/', views.TaskCompleteView.as_view(), name='task_complete'),
    path('tasks/<int:pk>/add-comment/', views.TaskAddCommentView.as_view(), name='task_add_comment'),
]