from django.shortcuts import render
from django.core.paginator import Paginator
from core.utils.star import Star, Project
from core.models import Category, Team

def index(request):
    projects_table = Star.get_projects()
    paginator = Paginator(projects_table, 112)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}

    return render(request, 'core/index.html', context)

def view(request, device_name):
    all_active_categories = list(Category.objects.filter(is_active=True).values('id', 'title'))
    teams_with_categories = []
    for team in Team.objects.all():
        team_json = {}
        team_json['team_id'] = 'team_' + str(team.id)
        team_json['team_name'] = team.name
        team_json['team_categories'] = list(
            team.categories.values('id', 'title')
        )
        teams_with_categories.append(team_json)

    context = {'categories': all_active_categories,
               'teams': teams_with_categories,
               'title': device_name
               }
  
    categories = []

    if request.method == 'POST':
        filters = {}
        if request.POST.getlist('category'):
            categories = request.POST.getlist('category')
            filters['categories'] = categories

        if request.POST.get('only_blank'):
            filters['only_blank'] = 'on'
            context['only_blank'] = True

        if request.POST.get('tc911'):
            filters['tc911'] = 'on'
            context['tc911'] = True

        if request.POST.get('Priority') != 'Priority':
            priotiry = request.POST.get('Priority')
            filters['Priority'] = priotiry
            context['Priority'] = priotiry

        if request.POST.get('Variant') != 'None':
            variant = request.POST.get('Variant')
            filters['Variant'] = variant
            context['Variant'] = variant

        # project = Project.get_phone_project2(
        #     phone_model=device_name, filter=filter)
        whole_project = Project(device_name, filters)
        
        project = {
            'testcases': whole_project.sorted_list_of_tc_by_category,
            'last_binary_version': whole_project.current_binary_version,
            'previous_binaty_version': whole_project.previous_biniry_version,
            'total_tc': len(whole_project.sorted_list_of_tc_by_category),
            'total_time': whole_project.parse_time
        }
        context['selected_categories'] = list(map(int, categories))
        for item in project:
            context[item] = project[item]
        context['button'] = 'Refresh project'

    else:
        context['button'] = 'Show project'
        if request.COOKIES.get('Categories'):
            selected_categories = request.COOKIES.get('Categories').split('-')
            selected_categories = list(map(int, selected_categories))
            context['selected_categories'] = selected_categories
        if request.COOKIES.get('Only_blank') == 'True':
            context['only_blank'] = True
        if request.COOKIES.get('tc911') == 'True':
            context['tc911'] = True

    response = render(request, 'core/view.html', context)
    # Save coockies
    if request.method == 'POST':
        response.set_cookie('Categories', '-'.join(categories))
        if request.POST.get('only_blank') == 'on':
            response.set_cookie('Only_blank', 'True')
        else:
            response.set_cookie('Only_blank', 'False')

        if request.POST.get('tc911') == 'on':
            response.set_cookie('tc911', 'True')
        else:
            response.set_cookie('tc911', 'False')

        if request.POST.get('Priority') != 'None':
            response.set_cookie('Priority', request.POST.get('Priority'))

        if request.POST.get('Variant') != 'None':
            response.set_cookie('Variant', request.POST.get('Variant'))

    return response