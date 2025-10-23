from django.dispatch import receiver
from django.db.models.signals import post_migrate
from django.apps import apps

from .models import Category
from .category_seed import ALL_CATEGORIES


@receiver(post_migrate)
def seed_categories_on_migrate(sender, **kwargs):
	if sender.name != 'store':
		return
	if Category.objects.count() == 0:
		for name in ALL_CATEGORIES:
			Category.objects.get_or_create(name=name, defaults={'description': f'{name} category'}) 