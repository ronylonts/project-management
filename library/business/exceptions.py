class BusinessException(Exception):
    """Exception de base pour les erreurs métier"""
    pass

class ProjectNotFoundException(BusinessException):
    """Exception levée quand un projet n'est pas trouvé"""
    pass

class TaskNotFoundException(BusinessException):
    """Exception levée quand une tâche n'est pas trouvée"""
    pass

class UserNotFoundException(BusinessException):
    """Exception levée quand un utilisateur n'est pas trouvé"""
    pass

class UnauthorizedAccessException(BusinessException):
    """Exception levée quand un utilisateur n'a pas les droits nécessaires"""
    pass

class InvalidProgressValueException(BusinessException):
    """Exception levée quand la progression n'est pas valide"""
    pass

class TimeEntryValidationException(BusinessException):
    """Exception levée quand une entrée de temps n'est pas valide"""
    pass

class DependencyCycleException(BusinessException):
    """Exception levée quand une dépendance circulaire est détectée"""
    pass