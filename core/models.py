from django.db import models
from django.db.models.functions import Lower

class Category(models.Model):
    title = models.CharField(max_length=250, verbose_name="Category's name")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = [Lower("title")]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.title

class Team(models.Model):
    name = models.CharField(max_length=100, verbose_name="Team's name")
    categories = models.ManyToManyField(Category, limit_choices_to={'is_active': True})

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Teams"
