from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        from django.db.models.signals import post_migrate
        from .signals import seed_categories_on_migrate
        post_migrate.connect(seed_categories_on_migrate, sender=self)
