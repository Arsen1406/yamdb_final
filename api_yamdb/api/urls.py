from django.urls import include, path
from rest_framework import routers
from .views import (
    TitleViewSet,
    ReviewViewSet,
    CommentsViewSet,
    GenresViewSet,
    CategoriesViewSet,
    UsersViewSet,
    SignUpViewSet,
    TokenViewSet,
)

router_v1 = routers.DefaultRouter()
router_v1.register(r'titles', TitleViewSet, basename='titles')
router_v1.register(r'genres', GenresViewSet, basename='genres')
router_v1.register(r'categories', CategoriesViewSet, basename='categories')
router_v1.register(r'^titles/(?P<title_id>\d+)/reviews',
                   ReviewViewSet, basename='reviews')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentsViewSet,
    basename='comments'
)
router_v1.register(r'auth/signup', SignUpViewSet, basename='signup')
router_v1.register(r'auth/token', TokenViewSet, basename='token')
router_v1.register(r'users', UsersViewSet, basename='users')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
]
