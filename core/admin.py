from django.contrib import admin
from .models import *


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    filter_horizontal = ('categories',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_editable = ('is_active',)