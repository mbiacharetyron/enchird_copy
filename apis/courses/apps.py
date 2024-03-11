from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apis.courses'
    
    def ready(self):
        from jobs import updater
        updater.start()
