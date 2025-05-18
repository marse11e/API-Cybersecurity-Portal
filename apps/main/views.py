from datetime import timezone


from django.shortcuts import render
from django.db.models import Count, Q, Avg, F
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import viewsets, generics, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import (
    CustomTokenObtainPairSerializer, UserSerializer, UserProfileSerializer,
    CategorySerializer, TagSerializer, ArticleListSerializer, ArticleDetailSerializer,
    CommentSerializer, CourseListSerializer, CourseDetailSerializer,
    CourseSectionSerializer, LessonSerializer, CourseProgressSerializer,
    CourseMaterialSerializer, CourseReviewSerializer, DiscussionListSerializer,
    DiscussionDetailSerializer, ReplySerializer, AchievementSerializer,
    UserAchievementSerializer, UserActivitySerializer, TestListSerializer,
    TestDetailSerializer, TestQuestionSerializer, TestAttemptSerializer,
    TestResultSerializer, SendEmailCodeSerializer, VerifyEmailCodeSerializer,
    ResetPasswordByCodeSerializer, FavoriteCourseSerializer
)
from .models import (
    User, Category, Tag, Article, Comment, Course, CourseSection, Lesson,
    CourseProgress, CourseMaterial, CourseReview, Discussion, Reply,
    Achievement, UserAchievement, UserActivity, Test, TestQuestion, TestAttempt,
    TestResult, EmailVerificationCode, FavoriteCourse
)
from .utils import send_email_code
import random

# Пользовательские классы разрешений
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение на редактирование только владельцу объекта.
    """
    def has_object_permission(self, request, view, obj):
        # Разрешения на чтение разрешены для любого запроса
        if request.method in permissions.SAFE_METHODS:
            return True

        # Права на запись доступны только владельцу объекта
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        return False

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Разрешение на редактирование только для администраторов, чтение для всех.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

# Пользовательский класс TokenObtainPairView
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Представления для пользователей
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        elif self.action == 'list':
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_object(self):
        # Переопределяем для случая, когда запрашивается собственный профиль по "me"
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "message": "Пользователь успешно зарегистрирован!"
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        # Вычисляем статистику пользователя
        courses_completed = user.course_progresses.filter(completed=True).values('lesson__section__course').distinct().count()
        tests_completed = user.test_attempts.filter(status='completed').count()
        articles_read = user.activities.filter(activity_type='article').count()
        average_score = user.test_attempts.filter(status='completed').aggregate(avg=Avg('score'))['avg'] or 0
        # Добавляем статистику к объекту пользователя (динамически)
        user.courses_completed = courses_completed
        user.tests_completed = tests_completed
        user.articles_read = articles_read
        user.average_score = int(average_score)
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def achievements(self, request, pk=None):
        user = self.get_object()
        achievements = UserAchievement.objects.filter(user=user)
        serializer = UserAchievementSerializer(achievements, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        user = self.get_object()
        activities = UserActivity.objects.filter(user=user).order_by('-date')
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)

# Представления для категорий
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsStaffOrReadOnly()]
        return [AllowAny()]

# Представления для тегов
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsStaffOrReadOnly()]
        return [AllowAny()]

# Представления для статей
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author', 'featured', 'tags']
    search_fields = ['title', 'description', 'content']
    ordering_fields = ['date', 'views', 'likes']
    ordering = ['-date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer
        return ArticleDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Увеличиваем счетчик просмотров
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        article = self.get_object()
        article.likes += 1
        article.save()
        return Response({"status": "success", "likes": article.likes})
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured = Article.objects.filter(featured=True)
        serializer = ArticleListSerializer(featured, many=True)
        return Response(serializer.data)

# Представления для комментариев
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['article', 'user', 'parent']
    ordering_fields = ['date', 'likes']
    ordering = ['-date']
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        comment.likes += 1
        comment.save()
        return Response({"status": "success", "likes": comment.likes})

# Представления для курсов
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'instructor', 'level', 'featured', 'tags', 'certificate']
    search_fields = ['title', 'description', 'long_description']
    ordering_fields = ['rating', 'students', 'last_updated']
    ordering = ['-students']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]
    
    @action(detail=True, methods=['get'])
    def sections(self, request, pk=None):
        course = self.get_object()
        sections = CourseSection.objects.filter(course=course).order_by('order')
        serializer = CourseSectionSerializer(sections, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def materials(self, request, pk=None):
        course = self.get_object()
        materials = CourseMaterial.objects.filter(course=course)
        serializer = CourseMaterialSerializer(materials, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        course = self.get_object()
        reviews = CourseReview.objects.filter(course=course)
        serializer = CourseReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured = Course.objects.filter(featured=True)
        serializer = CourseListSerializer(featured, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        course = self.get_object()
        user = request.user
        # Получаем все уроки курса
        lessons = course.sections.all().values_list('lessons__id', flat=True)
        lessons = [lid for lid in lessons if lid]
        if not lessons:
            return Response({'error': 'В курсе нет уроков'}, status=status.HTTP_400_BAD_REQUEST)
        # Проверяем, есть ли уже прогресс по этим урокам
        existing = CourseProgress.objects.filter(user=user, lesson_id__in=lessons)
        if existing.exists():
            return Response({'detail': 'Вы уже записаны на этот курс.'}, status=200)
        # Создаём прогресс по всем урокам
        progresses = [CourseProgress(user=user, lesson_id=lid, completed=False) for lid in lessons]
        CourseProgress.objects.bulk_create(progresses)
        return Response({'detail': 'Вы успешно записались на курс.'}, status=201)

# Представления для разделов курса
class CourseSectionViewSet(viewsets.ModelViewSet):
    queryset = CourseSection.objects.all()
    serializer_class = CourseSectionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course']
    ordering_fields = ['order']
    ordering = ['order']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsStaffOrReadOnly()]
        return [AllowAny()]

# Представления для уроков
class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['section', 'type']
    ordering_fields = ['order']
    ordering = ['order']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsStaffOrReadOnly()]
        return [AllowAny()]

# Представления для прогресса по курсам
class CourseProgressViewSet(viewsets.ModelViewSet):
    serializer_class = CourseProgressSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'lesson', 'completed']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CourseProgress.objects.all()
        return CourseProgress.objects.filter(user=user)
    
    def get_permissions(self):
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({"error": "Course ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        lessons = Lesson.objects.filter(section__course_id=course_id)
        user_progress = CourseProgress.objects.filter(
            user=request.user, 
            lesson__in=lessons
        )
        
        completed_count = user_progress.filter(completed=True).count()
        total_count = lessons.count()
        
        data = {
            "course_id": course_id,
            "completed_lessons": completed_count,
            "total_lessons": total_count,
            "progress_percentage": (completed_count / total_count * 100) if total_count > 0 else 0
        }
        
        return Response(data)

# Представления для материалов курса
class CourseMaterialViewSet(viewsets.ModelViewSet):
    queryset = CourseMaterial.objects.all()
    serializer_class = CourseMaterialSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['course', 'type']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsStaffOrReadOnly()]
        return [IsAuthenticated()]

# Представления для отзывов о курсе
class CourseReviewViewSet(viewsets.ModelViewSet):
    queryset = CourseReview.objects.all()
    serializer_class = CourseReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'user', 'rating']
    ordering_fields = ['date', 'rating']
    ordering = ['-date']
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]

# Представления для форумных обсуждений
class DiscussionViewSet(viewsets.ModelViewSet):
    queryset = Discussion.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author', 'tags', 'pinned', 'solved']
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'views', 'likes', 'replies']
    ordering = ['-pinned', '-date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DiscussionListSerializer
        return DiscussionDetailSerializer
    
    def get_queryset(self):
        queryset = Discussion.objects.all()
        sort_by = self.request.query_params.get('sort_by', None)
        
        if sort_by:
            if sort_by == 'newest':
                queryset = queryset.order_by('-date')
            elif sort_by == 'popular':
                queryset = queryset.order_by('-likes')
            elif sort_by == 'most_replies':
                queryset = queryset.order_by('-replies')
        
        return queryset
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Увеличиваем счетчик просмотров
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        discussion = self.get_object()
        discussion.likes += 1
        discussion.save()
        return Response({"status": "success", "likes": discussion.likes})
    
    @action(detail=True, methods=['post'])
    def solve(self, request, pk=None):
        discussion = self.get_object()
        if request.user == discussion.author or request.user.is_staff:
            discussion.solved = True
            discussion.save()
            return Response({"status": "success", "solved": discussion.solved})
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        discussion = self.get_object()
        if request.user.is_staff:
            discussion.pinned = True
            discussion.save()
            return Response({"status": "success", "pinned": discussion.pinned})
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

# Представления для ответов в форуме
class ReplyViewSet(viewsets.ModelViewSet):
    queryset = Reply.objects.all()
    serializer_class = ReplySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['discussion', 'user']
    ordering_fields = ['date', 'likes']
    ordering = ['date']
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Увеличиваем счетчик ответов в обсуждении
        discussion = serializer.validated_data['discussion']
        discussion.replies += 1
        discussion.save(update_fields=['replies'])
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        discussion = instance.discussion
        
        self.perform_destroy(instance)
        
        # Уменьшаем счетчик ответов в обсуждении
        if discussion.replies > 0:
            discussion.replies -= 1
            discussion.save(update_fields=['replies'])
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        reply = self.get_object()
        reply.likes += 1
        reply.save()
        return Response({"status": "success", "likes": reply.likes})

# Представления для тестов
class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'level', 'featured', 'tags']
    search_fields = ['title', 'description', 'long_description']
    ordering_fields = ['rating', 'participants']
    ordering = ['-participants']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TestListSerializer
        return TestDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]
    
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        test = self.get_object()
        # Проверяем, начал ли пользователь тест
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Находим или создаем попытку прохождения теста
        attempt, created = TestAttempt.objects.get_or_create(
            test=test,
            user=request.user,
            completed=False,
            defaults={'start_time': timezone.now()}
        )
        
        questions = TestQuestion.objects.filter(test=test).order_by('order')
        serializer = TestQuestionSerializer(questions, many=True)
        
        # Скрываем правильные ответы в ответе
        data = serializer.data
        for question in data:
            question.pop('correct_answer', None)
            question.pop('explanation', None)
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def submit_answers(self, request, pk=None):
        test = self.get_object()
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Получаем ответы пользователя
        answers = request.data.get('answers', [])
        if not answers:
            return Response({"error": "No answers provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Находим незавершенную попытку или создаем новую
        attempt, created = TestAttempt.objects.get_or_create(
            test=test,
            user=request.user,
            completed=False,
            defaults={'start_time': timezone.now()}
        )
        
        # Проверяем ответы
        questions = TestQuestion.objects.filter(test=test)
        question_dict = {q.id: q for q in questions}
        
        correct_count = 0
        total_count = len(answers)
        processed_answers = []
        
        for answer in answers:
            question_id = answer.get('question_id')
            selected_option = answer.get('selected_option')
            
            if question_id in question_dict:
                question = question_dict[question_id]
                is_correct = selected_option == question.correct_answer
                if is_correct:
                    correct_count += 1
                
                processed_answers.append({
                    'question_id': question_id,
                    'selected_option': selected_option,
                    'is_correct': is_correct,
                    'correct_answer': question.correct_answer,
                    'explanation': question.explanation
                })
        
        # Рассчитываем результат
        score = (correct_count / total_count * 100) if total_count > 0 else 0
        passed = score >= test.passing_score
        
        # Обновляем статистику теста
        test.participants += 1
        test.save()
        
        # Отмечаем попытку как завершенную
        attempt.completed = True
        attempt.end_time = timezone.now()
        attempt.score = score
        attempt.answers = processed_answers
        attempt.save()
        
        # Сохраняем результат
        result = TestResult.objects.create(
            test=test,
            user=request.user,
            attempt=attempt,
            total_questions=total_count,
            correct_answers=correct_count,
            score_percent=score,
            passed=passed,
            time_spent=(attempt.end_time - attempt.start_time).total_seconds(),
            detailed_results=processed_answers
        )
        
        # Создаем запись активности пользователя
        UserActivity.objects.create(
            user=request.user,
            activity_type='test',
            title=test.title,
            date=timezone.now(),
            score=score
        )
        
        return Response({
            "id": result.id,
            "score": score,
            "passed": passed,
            "answers": processed_answers
        })
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        test = self.get_object()
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        results = TestResult.objects.filter(test=test, user=request.user).order_by('-created_at')
        serializer = TestResultSerializer(results, many=True)
        return Response(serializer.data)

# Представления для вопросов теста
class TestQuestionViewSet(viewsets.ModelViewSet):
    queryset = TestQuestion.objects.all()
    serializer_class = TestQuestionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['test', 'topic', 'difficulty']
    ordering_fields = ['order']
    ordering = ['order']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsStaffOrReadOnly()]
        return [IsAuthenticated()]

# Представления для попыток прохождения теста
class TestAttemptViewSet(viewsets.ModelViewSet):
    serializer_class = TestAttemptSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['test', 'user', 'status']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return TestAttempt.objects.all()
        return TestAttempt.objects.filter(user=user)
    
    def get_permissions(self):
        return [IsAuthenticated()]

# Представления для результатов тестов
class TestResultViewSet(viewsets.ModelViewSet):
    serializer_class = TestResultSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['test', 'user', 'passed']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return TestResult.objects.all()
        return TestResult.objects.filter(user=user)
    
    def get_permissions(self):
        return [IsAuthenticated()]

# Представления для достижений
class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsStaffOrReadOnly()]
        return [AllowAny()]

# Представления для достижений пользователя
class UserAchievementViewSet(viewsets.ModelViewSet):
    serializer_class = UserAchievementSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'achievement']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserAchievement.objects.all()
        return UserAchievement.objects.filter(user=user)
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsStaffOrReadOnly()]
        return [IsAuthenticated()]

# Представления для активностей пользователя
class UserActivityViewSet(viewsets.ModelViewSet):
    serializer_class = UserActivitySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'activity_type']
    ordering_fields = ['date']
    ordering = ['-date']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserActivity.objects.all()
        return UserActivity.objects.filter(user=user)
    
    def get_permissions(self):
        return [IsAuthenticated()]

# API для поиска по всем типам контента
class SearchAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Search query is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Поиск статей
        articles = Article.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(content__icontains=query)
        )[:5]
        
        # Поиск курсов
        courses = Course.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(long_description__icontains=query)
        )[:5]
        
        # Поиск обсуждений
        discussions = Discussion.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )[:5]
        
        # Поиск тестов
        tests = Test.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(long_description__icontains=query)
        )[:5]
        
        # Подготовка результатов
        results = {
            'articles': ArticleListSerializer(articles, many=True).data,
            'courses': CourseListSerializer(courses, many=True).data,
            'discussions': DiscussionListSerializer(discussions, many=True).data,
            'tests': TestListSerializer(tests, many=True).data,
        }
        
        return Response(results)

# Представление для дашборда пользователя
class UserDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        # Получаем последние активности
        activities = UserActivity.objects.filter(user=user).order_by('-date')[:5]
        # Получаем прогресс по курсам
        course_progress = {}
        enrolled_courses = Course.objects.filter(
            sections__lessons__courseprogress__user=user
        ).distinct()
        for course in enrolled_courses:
            lessons = Lesson.objects.filter(section__course=course)
            total_lessons = lessons.count()
            completed_lessons = CourseProgress.objects.filter(
                user=user, 
                lesson__in=lessons,
                completed=True
            ).count()
            progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
            course_progress[course.id] = {
                'id': course.id,
                'title': course.title,
                'completed_lessons': completed_lessons,
                'total_lessons': total_lessons,
                'progress_percentage': progress_percentage
            }
        # Получаем результаты тестов
        test_results = TestResult.objects.filter(user=user).order_by('-created_at')[:5]
        # Получаем достижения
        achievements = UserAchievement.objects.filter(user=user).order_by('-date_earned')
        # Статистика пользователя
        courses_completed = user.course_progresses.filter(completed=True).values('lesson__section__course').distinct().count()
        tests_completed = user.test_attempts.filter(status='completed').count()
        articles_read = user.activities.filter(activity_type='article').count()
        average_score = user.test_attempts.filter(status='completed').aggregate(avg=Avg('score'))['avg'] or 0
        user.courses_completed = courses_completed
        user.tests_completed = tests_completed
        user.articles_read = articles_read
        user.average_score = int(average_score)
        # Собираем данные дашборда
        dashboard_data = {
            'user': UserProfileSerializer(user).data,
            'activities': UserActivitySerializer(activities, many=True).data,
            'course_progress': list(course_progress.values()),
            'test_results': TestResultSerializer(test_results, many=True).data,
            'achievements': UserAchievementSerializer(achievements, many=True).data,
            'stats': {
                'courses_enrolled': enrolled_courses.count(),
                'courses_completed': courses_completed,
                'tests_taken': user.test_attempts.filter(status='completed').count(),
                'average_test_score': average_score,
                'discussions_created': Discussion.objects.filter(author=user).count(),
                'replies_posted': Reply.objects.filter(user=user).count(),
            }
        }
        return Response(dashboard_data)

class SendEmailCodeAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = SendEmailCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code_type = serializer.validated_data['type']
        # Генерируем 6-значный код
        code = str(random.randint(100000, 999999))
        # Деактивируем старые коды
        EmailVerificationCode.objects.filter(email=email, type=code_type, is_used=False).update(is_used=True)
        # Сохраняем новый код
        EmailVerificationCode.objects.create(email=email, code=code, type=code_type)
        # Отправляем email
        send_email_code(email, code, code_type)
        return Response({'detail': 'Код отправлен на email.'}, status=200)

class VerifyEmailCodeAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = VerifyEmailCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code_obj = serializer.validated_data['code_obj']
        code_obj.is_used = True
        code_obj.save()
        return Response({'detail': 'Код подтвержден.'}, status=200)

class ResetPasswordByCodeAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ResetPasswordByCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code_obj = serializer.validated_data['code_obj']
        user = User.objects.get(email=serializer.validated_data['email'])
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        code_obj.is_used = True
        code_obj.save()
        return Response({'detail': 'Пароль успешно изменён.'}, status=200)

class FavoriteCourseViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteCourseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'course']

    def get_queryset(self):
        user = self.request.user
        return FavoriteCourse.objects.filter(user=user)

    def get_permissions(self):
        return [IsAuthenticated()]
