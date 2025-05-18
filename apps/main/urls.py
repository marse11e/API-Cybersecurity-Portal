from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Создаем роутер для API
router = DefaultRouter()

# Базовые маршруты
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'categories', views.CategoryViewSet, basename='categories')
router.register(r'tags', views.TagViewSet, basename='tags')

# Контент-маршруты
router.register(r'articles', views.ArticleViewSet, basename='articles')
router.register(r'comments', views.CommentViewSet, basename='comments')
router.register(r'courses', views.CourseViewSet, basename='courses')
router.register(r'course-sections', views.CourseSectionViewSet, basename='course-sections')
router.register(r'lessons', views.LessonViewSet, basename='lessons')
router.register(r'course-progress', views.CourseProgressViewSet, basename='course-progress')
router.register(r'course-materials', views.CourseMaterialViewSet, basename='course-materials')
router.register(r'course-reviews', views.CourseReviewViewSet, basename='course-reviews')

# Форум-маршруты
router.register(r'discussions', views.DiscussionViewSet, basename='discussions')
router.register(r'replies', views.ReplyViewSet, basename='replies')

# Тесты-маршруты
router.register(r'tests', views.TestViewSet, basename='tests')
router.register(r'test-questions', views.TestQuestionViewSet, basename='test-questions')
router.register(r'test-attempts', views.TestAttemptViewSet, basename='test-attempts')
router.register(r'test-results', views.TestResultViewSet, basename='test-results')

# Достижения и активности
router.register(r'achievements', views.AchievementViewSet, basename='achievements')
router.register(r'user-achievements', views.UserAchievementViewSet, basename='user-achievements')
router.register(r'user-activities', views.UserActivityViewSet, basename='user-activities')

# Добавляем новый маршрут для избранных курсов
router.register(r'favorite-courses', views.FavoriteCourseViewSet, basename='favorite-courses')

# API маршруты версии 1
api_v1_patterns = [
    # Аутентификация
    path('auth/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', views.UserViewSet.as_view({'post': 'register'}), name='register'),
    # Email подтверждение и восстановление пароля
    path('auth/send-code/', views.SendEmailCodeAPIView.as_view(), name='send_email_code'),
    path('auth/verify-code/', views.VerifyEmailCodeAPIView.as_view(), name='verify_email_code'),
    path('auth/reset-password/', views.ResetPasswordByCodeAPIView.as_view(), name='reset_password_by_code'),
    # Специальные маршруты
    path('search/', views.SearchAPIView.as_view(), name='search'),
    path('dashboard/', views.UserDashboardView.as_view(), name='dashboard'),
    
    # REST API из роутера
    path('', include(router.urls)),
]

# Корневые URL-маршруты приложения
urlpatterns = [
    # API версии 1
    path('api/v1/', include(api_v1_patterns)),
]
