from django.shortcuts import render
from django.core.paginator import Paginator
from core.utils.star import Star

def index(request):
    projects_table = Star.get_projects()
    paginator = Paginator(projects_table, 112)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}

    return render(request, 'core/index.html', context)

def view(request, project_name):
    pass