from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    User, Category, Tag, Article, Comment, Course, CourseSection, Lesson,
    CourseProgress, CourseMaterial, CourseReview, Discussion, Reply,
    Achievement, UserAchievement, UserActivity, Test, TestQuestion, TestAttempt, 
    TestResult
)

# Пользовательский TokenObtainPairSerializer с дополнительными данными
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # Добавляем пользовательские данные
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'bio': self.user.bio,
            'avatar': self.user.avatar.url if self.user.avatar else None,
        }
        return data

# Базовые сериализаторы
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'count']
        read_only_fields = ['count']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'count']
        read_only_fields = ['count']

# Сериализаторы пользователя
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 
                 'confirm_password', 'avatar', 'bio', 'role', 'join_date', 'date_joined']
        read_only_fields = ['id', 'join_date', 'date_joined']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }
        
    def validate(self, attrs):
        # Валидация при создании пользователя
        if 'password' in attrs:
            if 'confirm_password' not in attrs:
                raise serializers.ValidationError(
                    {"confirm_password": "Необходимо подтвердить пароль."}
                )
            if attrs['password'] != attrs['confirm_password']:
                raise serializers.ValidationError(
                    {"password": "Пароли не совпадают."}
                )
            validate_password(attrs['password'])
        return attrs
        
    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
        
    def update(self, instance, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        
        if password:
            instance.set_password(password)
        
        return super().update(instance, validated_data)

class UserProfileSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для отображения информации о пользователе"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar', 'role', 'join_date']

# Сериализаторы для комментариев
class RecursiveCommentSerializer(serializers.Serializer):
    """Рекурсивный сериализатор для вложенных комментариев"""
    def to_representation(self, instance):
        serializer = CommentSerializer(instance, context=self.context)
        return serializer.data

class CommentSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    replies = RecursiveCommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'article', 'user', 'date', 'content', 'likes', 'parent', 'replies']
        read_only_fields = ['id', 'date', 'likes', 'user']
        
    def create(self, validated_data):
        user = self.context['request'].user
        comment = Comment.objects.create(user=user, **validated_data)
        return comment

# Сериализаторы для статей
class ArticleListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка статей с базовой информацией"""
    author = UserProfileSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'description', 'image', 'category', 'date', 
                  'author', 'read_time', 'tags', 'views', 'likes', 'featured', 
                  'comments_count']
        
    def get_comments_count(self, obj):
        return obj.comments.count()

class ArticleDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор для полной информации о статье"""
    author = UserProfileSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        write_only=True, 
        source='category'
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), 
        write_only=True, 
        many=True, 
        required=False,
        source='tags'
    )
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'description', 'content', 'image', 'category', 
                  'category_id', 'date', 'author', 'read_time', 'tags', 'tag_ids',
                  'views', 'likes', 'featured', 'comments', 'comments_count']
        read_only_fields = ['id', 'date', 'views', 'likes', 'author']
        
    def get_comments_count(self, obj):
        return obj.comments.count()
        
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        user = self.context['request'].user
        article = Article.objects.create(author=user, **validated_data)
        
        if tags:
            article.tags.set(tags)
        
        return article
        
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        
        if tags is not None:
            instance.tags.set(tags)
            
        return super().update(instance, validated_data)

# Сериализаторы для курсов
class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'section', 'title', 'duration', 'type', 'order']
        read_only_fields = ['id']

class CourseSectionSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    
    class Meta:
        model = CourseSection
        fields = ['id', 'course', 'title', 'order', 'lessons']
        read_only_fields = ['id']

class CourseMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMaterial
        fields = ['id', 'course', 'title', 'file', 'type', 'size']
        read_only_fields = ['id']

class CourseReviewSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = CourseReview
        fields = ['id', 'course', 'user', 'rating', 'date', 'comment']
        read_only_fields = ['id', 'date', 'user']
        
    def create(self, validated_data):
        user = self.context['request'].user
        review = CourseReview.objects.create(user=user, **validated_data)
        return review

class CourseListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка курсов с базовой информацией"""
    instructor = UserProfileSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'image', 'category', 'level',
                 'duration', 'instructor', 'rating', 'students', 'price',
                 'featured', 'tags', 'language', 'certificate', 'last_updated']
        read_only_fields = ['id', 'rating', 'students']

class CourseDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор для полной информации о курсе"""
    instructor = UserProfileSerializer(read_only=True)
    instructor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        write_only=True, 
        source='instructor'
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        write_only=True, 
        source='category'
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), 
        write_only=True, 
        many=True, 
        required=False,
        source='tags'
    )
    sections = CourseSectionSerializer(many=True, read_only=True, source='sections.all')
    materials = CourseMaterialSerializer(many=True, read_only=True, source='materials.all')
    reviews = CourseReviewSerializer(many=True, read_only=True, source='reviews.all')
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'long_description', 'image', 
                 'category', 'category_id', 'level', 'duration', 'instructor', 
                 'instructor_id', 'rating', 'students', 'price', 'featured',
                 'tags', 'tag_ids', 'last_updated', 'language', 'certificate',
                 'prerequisites', 'objectives', 'sections', 'materials', 'reviews']
        read_only_fields = ['id', 'rating', 'students']
        
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        course = Course.objects.create(**validated_data)
        
        if tags:
            course.tags.set(tags)
        
        return course
        
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        
        if tags is not None:
            instance.tags.set(tags)
            
        return super().update(instance, validated_data)

class CourseProgressSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    lesson = LessonSerializer(read_only=True)
    lesson_id = serializers.PrimaryKeyRelatedField(
        queryset=Lesson.objects.all(), 
        write_only=True, 
        source='lesson'
    )
    
    class Meta:
        model = CourseProgress
        fields = ['id', 'user', 'lesson', 'lesson_id', 'completed', 'date_completed']
        read_only_fields = ['id', 'date_completed', 'user']
        
    def create(self, validated_data):
        user = self.context['request'].user
        progress = CourseProgress.objects.create(user=user, **validated_data)
        return progress

# Сериализаторы для форумных обсуждений
class ReplySerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Reply
        fields = ['id', 'discussion', 'user', 'content', 'date', 'likes']
        read_only_fields = ['id', 'date', 'likes', 'user']
        
    def create(self, validated_data):
        user = self.context['request'].user
        reply = Reply.objects.create(user=user, **validated_data)
        return reply

class DiscussionListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка обсуждений с базовой информацией"""
    author = UserProfileSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Discussion
        fields = ['id', 'title', 'description', 'category', 'author', 'date',
                 'replies', 'views', 'likes', 'tags', 'pinned', 'solved']
        read_only_fields = ['id', 'date', 'replies', 'views', 'likes', 'author']

class DiscussionDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор для полной информации о обсуждении"""
    author = UserProfileSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        write_only=True, 
        source='category'
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), 
        write_only=True, 
        many=True, 
        required=False,
        source='tags'
    )
    discussion_replies = ReplySerializer(many=True, read_only=True)
    
    class Meta:
        model = Discussion
        fields = ['id', 'title', 'description', 'category', 'category_id', 
                 'author', 'date', 'replies', 'views', 'likes', 'tags', 
                 'tag_ids', 'pinned', 'solved', 'discussion_replies']
        read_only_fields = ['id', 'date', 'replies', 'views', 'likes', 'author']
        
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        user = self.context['request'].user
        discussion = Discussion.objects.create(author=user, **validated_data)
        
        if tags:
            discussion.tags.set(tags)
        
        return discussion
        
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        
        if tags is not None:
            instance.tags.set(tags)
            
        return super().update(instance, validated_data)
# Сериализаторы для тестов
class TestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = ['id', 'test', 'topic', 'question_text', 'question_type', 'options', 
                 'correct_answer', 'explanation', 'difficulty', 'points', 'order']
        read_only_fields = ['id']

class TestListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка тестов с базовой информацией"""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Test
        fields = ['id', 'title', 'description', 'image', 'category', 'level',
                 'duration', 'questions_count', 'participants', 'rating',
                 'featured', 'tags', 'passing_score', 'max_attempts', 'created_at']
        read_only_fields = ['id', 'participants', 'rating', 'created_at']

class TestDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор для полной информации о тесте"""
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        write_only=True, 
        source='category'
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), 
        write_only=True, 
        many=True, 
        required=False,
        source='tags'
    )
    questions = TestQuestionSerializer(many=True, read_only=True, source='questions.all')
    
    class Meta:
        model = Test
        fields = ['id', 'title', 'description', 'long_description', 'image', 
                 'category', 'category_id', 'level', 'duration', 'questions_count',
                 'participants', 'rating', 'passing_score', 'max_attempts',
                 'featured', 'tags', 'tag_ids', 'questions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'participants', 'rating', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        test = Test.objects.create(**validated_data)
        
        if tags:
            test.tags.set(tags)
        
        return test
        
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        
        if tags is not None:
            instance.tags.set(tags)
            
        return super().update(instance, validated_data)

class TestAttemptSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = TestAttempt
        fields = ['id', 'user', 'test', 'start_time', 'end_time', 'status', 
                 'score', 'answers', 'attempt_number']
        read_only_fields = ['id', 'start_time', 'user', 'attempt_number']
        
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Определение номера попытки
        attempt_count = TestAttempt.objects.filter(
            user=user, 
            test=validated_data['test']
        ).count()
        
        attempt = TestAttempt.objects.create(
            user=user, 
            attempt_number=attempt_count + 1,
            **validated_data
        )
        return attempt

class TestResultSerializer(serializers.ModelSerializer):
    attempt = TestAttemptSerializer(read_only=True)
    
    class Meta:
        model = TestResult
        fields = ['id', 'attempt', 'total_questions', 'correct_answers', 
                 'score_percent', 'time_spent', 'passed', 'feedback', 
                 'detailed_results', 'created_at']
        read_only_fields = ['id', 'created_at']

# Сериализаторы для достижений
class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'title', 'description', 'icon']
        read_only_fields = ['id']

class UserAchievementSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    achievement = AchievementSerializer(read_only=True)
    achievement_id = serializers.PrimaryKeyRelatedField(
        queryset=Achievement.objects.all(), 
        write_only=True,
        source='achievement'
    )
    
    class Meta:
        model = UserAchievement
        fields = ['id', 'user', 'achievement', 'achievement_id', 'date_earned']
        read_only_fields = ['id', 'date_earned', 'user']
        
    def create(self, validated_data):
        user = self.context['request'].user
        user_achievement = UserAchievement.objects.create(user=user, **validated_data)
        return user_achievement

# Сериализатор для активностей пользователя
class UserActivitySerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'activity_type', 'title', 'date', 'progress', 'score']
        read_only_fields = ['id', 'date', 'user']
        
    def create(self, validated_data):
        user = self.context['request'].user
        activity = UserActivity.objects.create(user=user, **validated_data)
        return activity
