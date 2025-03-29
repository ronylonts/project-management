from django.apps import AppConfig

class LibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'library'

    def ready(self):
        # Import des signaux ici pour éviter les imports circulaires
        import library.data.signals  # Nous créerons ce fichier plus tard