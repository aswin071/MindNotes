from django.db import models
from django.utils import timezone


class ActiveManager(models.Manager):
    def active(self):
        return super().get_queryset().filter(is_active=True, deleted=False)

class Model(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At', help_text='Date and time at which the row was created')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At', help_text='Date and time at which the row was last updated')
    deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def delete(self):
        self.is_active = False
        self.deleted = True
        self.save()
    
    def restore(self):
        self.is_active = True
        self.deleted = False
        self.save()

    def hard_delete(self):
        super().delete()