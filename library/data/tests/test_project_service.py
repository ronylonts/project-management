from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from ..services import ProjectService
from ..exceptions import ProjectNotFoundException, UnauthorizedAccessException

User = get_user_model()

class ProjectServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='password',
            role='MANAGER'
        )
        
        self.member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='password',
            role='MEMBER'
        )
        
        self.service = ProjectService()
    
    def test_create_project(self):
        start_date = date.today()
        end_date = start_date + timedelta(days=30)
        
        project = self.service.create_project(
            name='Projet Test',
            description='Description du projet test',
            start_date=start_date,
            end_date=end_date,
            budget=10000,
            manager_id=self.user.id
        )
        
        self.assertEqual(project.name, 'Projet Test')
        self.assertEqual(project.manager.id, self.user.id)
    
    def test_get_project(self):
        start_date = date.today()
        end_date = start_date + timedelta(days=30)
        
        project = self.service.create_project(
            name='Projet Test',
            description='Description du projet test',
            start_date=start_date,
            end_date=end_date,
            budget=10000,
            manager_id=self.user.id
        )
        
        # Test que le manager peut accéder au projet
        retrieved = self.service.get_project(project.id, self.user.id)
        self.assertEqual(retrieved.id, project.id)
        
        # Test qu'un membre non associé ne peut pas accéder
        with self.assertRaises(UnauthorizedAccessException):
            self.service.get_project(project.id, self.member.id)
    
    def test_get_nonexistent_project(self):
        with self.assertRaises(ProjectNotFoundException):
            self.service.get_project(999, self.user.id)