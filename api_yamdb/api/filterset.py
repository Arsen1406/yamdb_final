from django_filters import rest_framework
from reviews.models import Title


class TitleFilter(rest_framework.FilterSet):
    """Фильтрация проектов."""
    name = rest_framework.CharFilter(field_name='name', lookup_expr='contains')
    genre = rest_framework.CharFilter(field_name='genre__slug')
    category = rest_framework.CharFilter(field_name='category__slug')

    class Meta:
        model = Title
        fields = ('category', 'genre', 'year', 'name')
