import datetime as dt
from django.db.models import Avg
from rest_framework.validators import UniqueValidator
from rest_framework import serializers, status
from reviews.models import Title, Review, Comment, Genre, Category
from users.models import User


class CategoriesSerializer(serializers.ModelSerializer):
    """Серилизатор для категорий."""

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenresSerializer(serializers.ModelSerializer):
    """Серилизатор для жанров произведений."""

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleCreateSerializer(serializers.ModelSerializer):
    """Серилизатор для произведений."""
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        many=True,
        queryset=Genre.objects.all()
    )

    class Meta:
        model = Title
        fields = ('__all__')

    def validate_year(self, value):
        """Валидатор проверяет не является произведение гостем избудущего"""
        today = dt.datetime.today().year
        if not (today >= value):
            raise serializers.ValidationError(
                'Год не может быть выше нынешнего!')
        return value


class TitlesSerializer(serializers.ModelSerializer):
    category = CategoriesSerializer()
    genre = GenresSerializer(many=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )

    def get_rating(self, obj):
        """Получаем средний рейтинг произведения."""
        rating = obj.reviews.all().aggregate(Avg('score')).get('score__avg')
        if not rating:
            return rating
        return round(rating, 1)


class ReviewSerializer(serializers.ModelSerializer):
    """Серилизатор для отзывов."""
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True)
    score = serializers.IntegerField(max_value=10, min_value=1)

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def validate(self, attrs):
        """Валидатор проверяет, что автор не оставит отзыв дважды."""
        if self.instance:
            return attrs
        title_id = self.context['view'].kwargs.get('title_id')
        author = self.context['request'].user
        if Review.objects.filter(author=author, title=title_id).exists():
            raise serializers.ValidationError(
                'Вы уже оставили отзыв об этом произведении.'
            )
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    """Серилизатор для комментариев отзывов."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')

    def validate_comment(self, data):
        """Валидатор на комментарии для отзыва."""
        if self.context['request'].method != 'PATCH':
            return data
        comment_id = self.context['view'].kwargs.get('comment_id')
        comment = Comment.objects.get(id=comment_id)
        author = self.context['request'].user
        if comment.author != author:
            raise serializers.ValidationError(
                'Вы можете редактировать только свои комментарии.')
        return data


class SignUpSerializer(serializers.ModelSerializer):
    """Серилизатор для регистрации новых пользователей."""
    username = serializers.RegexField(
        r'^[\w.@+-]+',
        max_length=150,
        min_length=None,
        allow_blank=False,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    email = serializers.EmailField(
        max_length=254,
        min_length=None,
        allow_blank=False,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = ('username', 'email')

    def validate_email(self, email):
        """Проверка уникальности email."""
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'Такой email уже существует.'
            )
        return email

    def validate_username(self, username):
        """Проверка на создание пользователя ME."""
        if username.lower() == 'me':
            raise serializers.ValidationError(
                'Пользователя с username=me нельзя создавать.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return username


class UserSerializer(SignUpSerializer):
    """Серилизатор для профайла юзера."""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )

    def validate_role(self, role):
        authenticated_user_role = self.context['request'].user.role
        is_superuser = self.context['request'].user.is_superuser
        if (authenticated_user_role in [User.USER, User.MODERATOR]
                and not is_superuser):
            return authenticated_user_role
        return role


class TokenSerializer(serializers.ModelSerializer):
    """Серилизатор для передачи токена."""
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')
        read_only_fields = ('username', 'confirmation_code')
