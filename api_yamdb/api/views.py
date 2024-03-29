from rest_framework.decorators import action
from .permissions import (
    AdminOrReadOnly,
    IsAdmin,
    IsSuperuser,
    ReviewPermission
)
from .serializers import (
    CommentSerializer,
    CategoriesSerializer,
    GenresSerializer,
    SignUpSerializer,
    ReviewSerializer,
    TokenSerializer,
    TitlesSerializer,
    TitleCreateSerializer,
    UserSerializer,
)
from django.contrib.auth.tokens import default_token_generator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated
)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import filters, mixins, status, viewsets

from reviews.models import Category, Genre, Review, Title
from users.models import User

from .filterset import TitleFilter
from .send_confirmation_code import send_confirmation_code
from .my_base_view_set import BaseMyViewSet


class TitleViewSet(viewsets.ModelViewSet):
    """Все произведения проекта."""
    permission_classes = (AdminOrReadOnly,)
    queryset = Title.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return TitleCreateSerializer
        return TitlesSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Отзывы о произведениях."""
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, ReviewPermission)
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CommentsViewSet(viewsets.ModelViewSet):
    """Комментарии для отзывов."""
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, ReviewPermission)
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            review=get_object_or_404(Review, id=self.kwargs.get('review_id'))
        )

    def get_queryset(self):
        review = get_object_or_404(Review, pk=self.kwargs.get('review_id'))
        return review.comments.all()


class CategoriesViewSet(BaseMyViewSet):
    """Категории для произведений."""
    serializer_class = CategoriesSerializer
    permission_classes = (AdminOrReadOnly,)
    lookup_field = 'slug'
    queryset = Category.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    pagination_class = LimitOffsetPagination


class GenresViewSet(BaseMyViewSet):
    """Жанры для произведений."""
    serializer_class = GenresSerializer
    queryset = Genre.objects.all()
    lookup_field = 'slug'
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    pagination_class = LimitOffsetPagination


class UsersViewSet(viewsets.ModelViewSet):
    """Профайл для пользователя."""
    lookup_field = 'username'
    serializer_class = UserSerializer
    permission_classes = [IsAdmin | IsSuperuser]
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    queryset = User.objects.all()

    @action(detail=False, methods=['get', 'patch'],
            permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        self.kwargs['username'] = self.request.user
        if self.request.method == 'PATCH':
            return self.update(request, partial=True, *args, **kwargs)
        return self.retrieve(request, *args, **kwargs)


class SignUpViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Регистрация нового пользователя."""
    serializer_class = SignUpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        user = User.objects.get(username=serializer.data['username'])
        send_confirmation_code(user)

        return Response(serializer.data, status=status.HTTP_200_OK,
                        headers=headers)


class TokenViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Получение токена авторизации пользователя."""
    model = User
    lookup_field = 'username'
    serializer_class = TokenSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, username=serializer.data['username'])
        confirmation_code_is_valid = default_token_generator.check_token(
            user,
            serializer.data['confirmation_code']
        )
        if confirmation_code_is_valid:
            user = User.objects.get(username=serializer.data['username'])
            token = str(RefreshToken.for_user(user).access_token)
            return Response(data={'token': token}, status=status.HTTP_200_OK)
        return Response(
            data={'Ошибка': 'Код неправильный.'},
            status=status.HTTP_400_BAD_REQUEST
        )
