from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count

from .models import (
    User, Category, Tag, Article, Comment, Course, CourseSection, Lesson,
    CourseProgress, CourseMaterial, CourseReview, Discussion, Reply,
    Achievement, UserAchievement, UserActivity
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'get_avatar', 'role', 'date_joined', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'role', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'join_date')
    fieldsets = (
        (_('Аутентификация'), {'fields': ('email', 'username', 'password')}),
        (_('Личная информация'), {'fields': ('first_name', 'last_name', 'avatar', 'bio', 'role')}),
        (_('Права доступа'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Важные даты'), {'fields': ('last_login', 'date_joined', 'join_date')}),
    )
    
    def get_avatar(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%" />', obj.avatar.url)
        return format_html('<span style="color: #999">Нет фото</span>')
    get_avatar.short_description = _('Аватар')


class TagInline(admin.TabularInline):
    model = Tag.articles.through
    extra = 1
    verbose_name = _('Тег')
    verbose_name_plural = _('Теги')


class CommentInline(admin.StackedInline):
    model = Comment
    extra = 0
    readonly_fields = ('date',)
    fieldsets = (
        (None, {'fields': ('user', 'date', 'content', 'likes')}),
    )
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'count', 'get_articles_count', 'get_courses_count', 'get_discussions_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_articles_count(self, obj):
        return obj.articles.count()
    get_articles_count.short_description = _('Статьи')
    
    def get_courses_count(self, obj):
        return obj.courses.count()
    get_courses_count.short_description = _('Курсы')
    
    def get_discussions_count(self, obj):
        return obj.discussions.count()
    get_discussions_count.short_description = _('Обсуждения')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'count', 'get_articles_count', 'get_courses_count', 'get_discussions_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_articles_count(self, obj):
        return obj.articles.count()
    get_articles_count.short_description = _('Статьи')
    
    def get_courses_count(self, obj):
        return obj.courses.count()
    get_courses_count.short_description = _('Курсы')
    
    def get_discussions_count(self, obj):
        return obj.discussions.count()
    get_discussions_count.short_description = _('Обсуждения')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'date', 'views', 'likes', 'featured')
    list_filter = ('category', 'featured', 'date')
    search_fields = ('title', 'description', 'content')
    date_hierarchy = 'date'
    autocomplete_fields = ('author', 'category')
    filter_horizontal = ('tags',)
    readonly_fields = ('views', 'likes', 'get_image_preview')
    fieldsets = (
        (_('Основная информация'), {'fields': ('title', 'description', 'content')}),
        (_('Медиа'), {'fields': ('image', 'get_image_preview')}),
        (_('Классификация'), {'fields': ('category', 'tags')}),
        (_('Мета-информация'), {'fields': ('author', 'date', 'read_time', 'views', 'likes', 'featured')}),
    )
    inlines = [TagInline, CommentInline]
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="300" />', obj.image)
        return format_html('<span style="color: #999">Нет изображения</span>')
    get_image_preview.short_description = _('Предпросмотр')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'parent', 'date', 'likes')
    list_filter = ('date',)
    search_fields = ('content', 'user__username', 'article__title')
    date_hierarchy = 'date'
    autocomplete_fields = ('user', 'article', 'parent')
    readonly_fields = ('date', 'likes')
    fieldsets = (
        (None, {'fields': ('user', 'article', 'parent')}),
        (_('Контент'), {'fields': ('content',)}),
        (_('Мета-информация'), {'fields': ('date', 'likes')}),
    )


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'type', 'duration', 'order')


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'get_lessons_count')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    autocomplete_fields = ('course',)
    fieldsets = (
        (None, {'fields': ('course', 'title')}),
        (_('Порядок'), {'fields': ('order',)}),
    )
    inlines = [LessonInline]
    
    def get_lessons_count(self, obj):
        return obj.lessons.count()
    get_lessons_count.short_description = _('Кол-во уроков')


class CourseSectionInline(admin.TabularInline):
    model = CourseSection
    extra = 1
    fields = ('title', 'order')
    show_change_link = True


class CourseMaterialInline(admin.TabularInline):
    model = CourseMaterial
    extra = 1
    fields = ('title', 'file', 'type', 'size')


class CourseReviewInline(admin.StackedInline):
    model = CourseReview
    extra = 0
    readonly_fields = ('date',)
    fields = ('user', 'rating', 'date', 'comment')
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'level', 'instructor', 'students', 'rating', 'featured')
    list_filter = ('category', 'level', 'featured', 'certificate')
    search_fields = ('title', 'description', 'instructor__username')
    filter_horizontal = ('tags',)
    autocomplete_fields = ('instructor', 'category')
    readonly_fields = ('students', 'rating', 'get_image_preview')
    fieldsets = (
        (_('Основная информация'), {'fields': ('title', 'description', 'long_description')}),
        (_('Медиа'), {'fields': ('image', 'get_image_preview')}),
        (_('Классификация'), {'fields': ('category', 'tags', 'level')}),
        (_('Информация о курсе'), {'fields': ('instructor', 'duration', 'price', 'language', 
                                            'last_updated', 'certificate', 'prerequisites')}),
        (_('Цели обучения'), {'fields': ('objectives',)}),
        (_('Статистика'), {'fields': ('students', 'rating', 'featured')}),
    )
    inlines = [CourseSectionInline, CourseMaterialInline, CourseReviewInline]
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="300" />', obj.image)
        return format_html('<span style="color: #999">Нет изображения</span>')
    get_image_preview.short_description = _('Предпросмотр')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'get_course', 'type', 'duration', 'order')
    list_filter = ('type', 'section__course')
    search_fields = ('title', 'section__title', 'section__course__title')
    autocomplete_fields = ('section',)
    fieldsets = (
        (None, {'fields': ('section', 'title', 'type')}),
        (_('Дополнительно'), {'fields': ('duration', 'order')}),
    )
    
    def get_course(self, obj):
        return obj.section.course
    get_course.short_description = _('Курс')
    get_course.admin_order_field = 'section__course__title'


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_lesson_title', 'get_course', 'completed', 'date_completed')
    list_filter = ('completed', 'date_completed', 'lesson__section__course')
    search_fields = ('user__username', 'lesson__title', 'lesson__section__course__title')
    autocomplete_fields = ('user', 'lesson')
    readonly_fields = ('date_completed',)
    fieldsets = (
        (None, {'fields': ('user', 'lesson', 'completed', 'date_completed')}),
    )
    
    def get_lesson_title(self, obj):
        return obj.lesson.title
    get_lesson_title.short_description = _('Урок')
    get_lesson_title.admin_order_field = 'lesson__title'
    
    def get_course(self, obj):
        return obj.lesson.section.course
    get_course.short_description = _('Курс')
    get_course.admin_order_field = 'lesson__section__course__title'


@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'type', 'size', 'get_file_link')
    list_filter = ('type', 'course')
    search_fields = ('title', 'course__title')
    autocomplete_fields = ('course',)
    fieldsets = (
        (None, {'fields': ('course', 'title', 'file')}),
        (_('Дополнительно'), {'fields': ('type', 'size')}),
    )
    
    def get_file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Скачать</a>', obj.file.url)
        return format_html('<span style="color: #999">Нет файла</span>')
    get_file_link.short_description = _('Файл')


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'rating', 'date')
    list_filter = ('rating', 'date', 'course')
    search_fields = ('comment', 'user__username', 'course__title')
    autocomplete_fields = ('user', 'course')
    readonly_fields = ('date',)
    fieldsets = (
        (None, {'fields': ('user', 'course')}),
        (_('Отзыв'), {'fields': ('rating', 'comment')}),
        (_('Мета-информация'), {'fields': ('date',)}),
    )


class ReplyInline(admin.StackedInline):
    model = Reply
    extra = 0
    readonly_fields = ('date',)
    fieldsets = (
        (None, {'fields': ('user', 'date', 'content', 'likes')}),
    )
    show_change_link = True


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'date', 'replies', 'views', 'likes', 'pinned', 'solved')
    list_filter = ('category', 'pinned', 'solved', 'date')
    search_fields = ('title', 'description', 'author__username')
    date_hierarchy = 'date'
    autocomplete_fields = ('author', 'category')
    filter_horizontal = ('tags',)
    readonly_fields = ('replies', 'views', 'likes', 'date')
    fieldsets = (
        (_('Основная информация'), {'fields': ('title', 'description')}),
        (_('Классификация'), {'fields': ('category', 'tags')}),
        (_('Мета-информация'), {'fields': ('author', 'date', 'replies', 'views', 'likes')}),
        (_('Статус'), {'fields': ('pinned', 'solved')}),
    )
    inlines = [ReplyInline]
    
    actions = ['mark_as_solved', 'mark_as_unsolved', 'pin_discussions', 'unpin_discussions']
    
    def mark_as_solved(self, request, queryset):
        queryset.update(solved=True)
    mark_as_solved.short_description = _('Отметить как решенные')
    
    def mark_as_unsolved(self, request, queryset):
        queryset.update(solved=False)
    mark_as_unsolved.short_description = _('Отметить как нерешенные')
    
    def pin_discussions(self, request, queryset):
        queryset.update(pinned=True)
    pin_discussions.short_description = _('Закрепить обсуждения')
    
    def unpin_discussions(self, request, queryset):
        queryset.update(pinned=False)
    unpin_discussions.short_description = _('Открепить обсуждения')


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_discussion_title', 'date', 'likes')
    list_filter = ('date', 'likes')
    search_fields = ('content', 'user__username', 'discussion__title')
    date_hierarchy = 'date'
    autocomplete_fields = ('user', 'discussion')
    readonly_fields = ('date', 'likes')
    fieldsets = (
        (None, {'fields': ('user', 'discussion')}),
        (_('Контент'), {'fields': ('content',)}),
        (_('Мета-информация'), {'fields': ('date', 'likes')}),
    )
    
    def get_discussion_title(self, obj):
        return obj.discussion.title
    get_discussion_title.short_description = _('Обсуждение')
    get_discussion_title.admin_order_field = 'discussion__title'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'get_users_count')
    search_fields = ('title', 'description')
    fieldsets = (
        (None, {'fields': ('title', 'description', 'icon')}),
    )
    
    def get_users_count(self, obj):
        return UserAchievement.objects.filter(achievement=obj).count()
    get_users_count.short_description = _('Кол-во пользователей')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'date_earned')
    list_filter = ('achievement', 'date_earned')
    search_fields = ('user__username', 'achievement__title')
    autocomplete_fields = ('user', 'achievement')
    readonly_fields = ('date_earned',)
    fieldsets = (
        (None, {'fields': ('user', 'achievement')}),
        (_('Мета-информация'), {'fields': ('date_earned',)}),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'title', 'date', 'progress', 'score')
    list_filter = ('activity_type', 'date')
    search_fields = ('user__username', 'title')
    date_hierarchy = 'date'
    autocomplete_fields = ('user',)
    readonly_fields = ('date',)
    fieldsets = (
        (None, {'fields': ('user', 'activity_type', 'title')}),
        (_('Данные активности'), {'fields': ('progress', 'score')}),
        (_('Мета-информация'), {'fields': ('date',)}),
    )


# Настройка административного сайта
admin.site.site_header = _('Администрирование портала кибербезопасности')
admin.site.site_title = _('Портал кибербезопасности')
admin.site.index_title = _('Панель управления')
