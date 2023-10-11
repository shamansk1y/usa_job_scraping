from datetime import datetime
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Vacancy

def vacancy_list(request):

    selected_search_source = request.GET.get('search_source')
    date_filter = request.GET.get('date_filter')

    if date_filter:
        try:
            date_filter = datetime.strptime(date_filter, '%Y-%m-%d')
        except ValueError:
            date_filter = None

    vacancies = Vacancy.objects.all()

    if selected_search_source:
        vacancies = vacancies.filter(search_source=selected_search_source)

    if date_filter:
        vacancies = vacancies.filter(timestamp=date_filter)

    count = 20
    paginator = Paginator(vacancies, count)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    queryset = Vacancy.objects.values_list('search_source', flat=True)
    search_source_choices = list(set(queryset))

    context = {
        'search_source_choices': search_source_choices,
        'selected_search_source': selected_search_source,
        'date_filter': date_filter,
        'page_obj': page_obj,
    }

    return render(request, 'vacancy_list.html', context)
