from django.contrib import admin
from django.urls import path
from library.presentation import views
from django.urls import path, include, re_path
from library.presentation.api import schema_view

urlpatterns = [
    # ... vos autres URLs ...
    
    # Documentation API
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/update-progress/', views.update_task_progress, name='update_task_progress'),
    path('time/log/', views.log_time, name='log_time'),
    path('notifications/<int:notification_id>/mark-as-read/', views.mark_notification_as_read, name='mark_notification_as_read'),
]