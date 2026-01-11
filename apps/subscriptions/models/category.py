from  django.db import models

class Category(models.Model):
    """
    Category - категория подписки
    """
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True, db_index=True)
    # Идентификатор иконки для Frontend
    icon = models.CharField(max_length=64, blank=True, null=True)

    sort_order = models.PositiveIntegerField(default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name