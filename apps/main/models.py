from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Расширяет стандартную модель пользователя Django с авторизацией по Email
    """
    email = models.EmailField(
        unique=True,
        verbose_name=_('Email адрес'),
        help_text=_('Email адрес для авторизации')
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, 
                              verbose_name=_('Аватар'), 
                              help_text=_('Изображение профиля пользователя'))
    bio = models.TextField(blank=True, 
                          verbose_name=_('Биография'), 
                          help_text=_('Краткая информация о пользователе'))
    role = models.CharField(max_length=100, blank=True, 
                           verbose_name=_('Роль'), 
                           help_text=_('Роль пользователя в системе (студент, преподаватель и т.д.)'))
    join_date = models.DateField(auto_now_add=True, 
                                verbose_name=_('Дата регистрации'), 
                                help_text=_('Дата создания учетной записи'))
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
    
    def __str__(self):
        return self.email


class Category(models.Model):
    """
    Категория для статей, курсов и обсуждений
    """
    name = models.CharField(max_length=100, 
                           verbose_name=_('Название'), 
                           help_text=_('Название категории'))
    slug = models.SlugField(unique=True, 
                           verbose_name=_('Слаг'), 
                           help_text=_('Уникальный идентификатор для URL'))
    count = models.PositiveIntegerField(default=0, 
                                       verbose_name=_('Количество'), 
                                       help_text=_('Количество элементов в данной категории'))
    
    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    Теги для статей, курсов и обсуждений
    """
    name = models.CharField(max_length=50, 
                           verbose_name=_('Название'), 
                           help_text=_('Название тега'))
    slug = models.SlugField(unique=True, 
                           verbose_name=_('Слаг'), 
                           help_text=_('Уникальный идентификатор для URL'))
    count = models.PositiveIntegerField(default=0, 
                                       verbose_name=_('Количество'), 
                                       help_text=_('Количество элементов с данным тегом'))
    
    class Meta:
        verbose_name = _('Тег')
        verbose_name_plural = _('Теги')
    
    def __str__(self):
        return self.name


class Article(models.Model):
    """
    Модель для хранения статей
    """
    title = models.CharField(max_length=255, 
                            verbose_name=_('Заголовок'), 
                            help_text=_('Заголовок статьи'))
    description = models.TextField(
                                  verbose_name=_('Краткое описание'), 
                                  help_text=_('Краткое описание или аннотация статьи'))
    content = models.TextField(
                              verbose_name=_('Содержание'), 
                              help_text=_('Полный текст статьи'))
    image = models.URLField(
                           verbose_name=_('Изображение'), 
                           help_text=_('URL изображения для статьи'))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles', 
                                verbose_name=_('Категория'), 
                                help_text=_('Категория, к которой относится статья'))
    date = models.DateField(
                           verbose_name=_('Дата публикации'), 
                           help_text=_('Дата публикации статьи'))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles', 
                              verbose_name=_('Автор'), 
                              help_text=_('Автор статьи'))
    read_time = models.PositiveIntegerField(default=0, 
                                           verbose_name=_('Время чтения'), 
                                           help_text=_('Примерное время чтения статьи в минутах'))
    tags = models.ManyToManyField(Tag, related_name='articles', 
                                 verbose_name=_('Теги'), 
                                 help_text=_('Теги, связанные со статьей'))
    views = models.PositiveIntegerField(default=0, 
                                       verbose_name=_('Просмотры'), 
                                       help_text=_('Количество просмотров статьи'))
    likes = models.PositiveIntegerField(default=0, 
                                       verbose_name=_('Лайки'), 
                                       help_text=_('Количество лайков статьи'))
    featured = models.BooleanField(default=False, 
                                  verbose_name=_('Рекомендованная'), 
                                  help_text=_('Отметка о том, что статья является рекомендованной'))
    
    class Meta:
        verbose_name = _('Статья')
        verbose_name_plural = _('Статьи')
        ordering = ['-date']
    
    def __str__(self):
        return self.title


class Comment(models.Model):
    """
    Комментарии к статьям
    """
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', 
                               verbose_name=_('Статья'), 
                               help_text=_('Статья, к которой относится комментарий'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', 
                            verbose_name=_('Пользователь'), 
                            help_text=_('Автор комментария'))
    date = models.DateField(auto_now_add=True, 
                           verbose_name=_('Дата'), 
                           help_text=_('Дата создания комментария'))
    content = models.TextField(
                              verbose_name=_('Содержание'), 
                              help_text=_('Текст комментария'))
    likes = models.PositiveIntegerField(default=0, 
                                       verbose_name=_('Лайки'), 
                                       help_text=_('Количество лайков комментария'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', 
                              verbose_name=_('Родительский комментарий'), 
                              help_text=_('Комментарий, на который дан ответ'))
    
    class Meta:
        verbose_name = _('Комментарий')
        verbose_name_plural = _('Комментарии')
        ordering = ['-date']
    
    def __str__(self):
        return f'Комментарий от {self.user.username} к {self.article.title}'


class Course(models.Model):
    """
    Модель для курсов
    """
    LEVEL_CHOICES = [
        ('Начальный', 'Начальный'),
        ('Средний', 'Средний'),
        ('Продвинутый', 'Продвинутый'),
    ]
    
    title = models.CharField(max_length=255, 
                            verbose_name=_('Название'), 
                            help_text=_('Название курса'))
    description = models.TextField(
                                  verbose_name=_('Краткое описание'), 
                                  help_text=_('Краткое описание курса для превью'))
    long_description = models.TextField(blank=True, 
                                       verbose_name=_('Полное описание'), 
                                       help_text=_('Подробное описание курса'))
    image = models.URLField(
                           verbose_name=_('Изображение'), 
                           help_text=_('URL изображения для курса'))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses', 
                                verbose_name=_('Категория'), 
                                help_text=_('Категория, к которой относится курс'))
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, 
                            verbose_name=_('Уровень сложности'), 
                            help_text=_('Уровень сложности курса'))
    duration = models.CharField(max_length=50, 
                               verbose_name=_('Продолжительность'), 
                               help_text=_('Общая продолжительность курса'))
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses', 
                                  verbose_name=_('Преподаватель'), 
                                  help_text=_('Преподаватель курса'))
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0, 
                                verbose_name=_('Рейтинг'), 
                                help_text=_('Средний рейтинг курса'))
    students = models.PositiveIntegerField(default=0, 
                                          verbose_name=_('Студенты'), 
                                          help_text=_('Количество студентов, записанных на курс'))
    price = models.CharField(max_length=20, blank=True, 
                            verbose_name=_('Цена'), 
                            help_text=_('Стоимость курса'))
    featured = models.BooleanField(default=False, 
                                  verbose_name=_('Рекомендованный'), 
                                  help_text=_('Отметка о том, что курс является рекомендованным'))
    tags = models.ManyToManyField(Tag, related_name='courses', 
                                 verbose_name=_('Теги'), 
                                 help_text=_('Теги, связанные с курсом'))
    last_updated = models.CharField(max_length=50, 
                                   verbose_name=_('Последнее обновление'), 
                                   help_text=_('Дата последнего обновления курса'))
    language = models.CharField(max_length=50, default='Русский', 
                               verbose_name=_('Язык'), 
                               help_text=_('Язык, на котором ведется курс'))
    certificate = models.BooleanField(default=False, 
                                     verbose_name=_('Сертификат'), 
                                     help_text=_('Выдается ли сертификат по окончании курса'))
    prerequisites = models.TextField(blank=True, 
                                    verbose_name=_('Предварительные требования'), 
                                    help_text=_('Необходимые знания для прохождения курса'))
    objectives = models.JSONField(default=list, 
                                 verbose_name=_('Цели обучения'), 
                                 help_text=_('Список целей обучения в формате JSON'))
    
    class Meta:
        verbose_name = _('Курс')
        verbose_name_plural = _('Курсы')
    
    def __str__(self):
        return self.title


class CourseSection(models.Model):
    """
    Разделы курса
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections', 
                              verbose_name=_('Курс'), 
                              help_text=_('Курс, к которому относится раздел'))
    title = models.CharField(max_length=255, 
                            verbose_name=_('Название'), 
                            help_text=_('Название раздела курса'))
    order = models.PositiveIntegerField(default=0, 
                                       verbose_name=_('Порядок'), 
                                       help_text=_('Порядковый номер раздела в курсе'))
    
    class Meta:
        verbose_name = _('Раздел курса')
        verbose_name_plural = _('Разделы курса')
        ordering = ['order']
    
    def __str__(self):
        return f'{self.title} ({self.course.title})'


class Lesson(models.Model):
    """
    Уроки в разделах курса
    """
    LESSON_TYPE_CHOICES = [
        ('video', 'Видео'),
        ('quiz', 'Тест'),
        ('exercise', 'Упражнение'),
        ('exam', 'Экзамен'),
        ('project', 'Проект'),
    ]
    
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='lessons', 
                               verbose_name=_('Раздел'), 
                               help_text=_('Раздел курса, к которому относится урок'))
    title = models.CharField(max_length=255, 
                            verbose_name=_('Название'), 
                            help_text=_('Название урока'))
    duration = models.CharField(max_length=20, 
                               verbose_name=_('Продолжительность'), 
                               help_text=_('Продолжительность урока'))
    type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES, 
                           verbose_name=_('Тип'), 
                           help_text=_('Тип урока (видео, тест и т.д.)'))
    order = models.PositiveIntegerField(default=0, 
                                       verbose_name=_('Порядок'), 
                                       help_text=_('Порядковый номер урока в разделе'))
    
    class Meta:
        verbose_name = _('Урок')
        verbose_name_plural = _('Уроки')
        ordering = ['order']
    
    def __str__(self):
        return f'{self.title} ({self.section.course.title})'


class CourseProgress(models.Model):
    """
    Прогресс пользователя по урокам курса
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_progresses', 
                            verbose_name=_('Пользователь'), 
                            help_text=_('Пользователь, чей прогресс отслеживается'))
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, 
                              verbose_name=_('Урок'), 
                              help_text=_('Урок, по которому отслеживается прогресс'))
    completed = models.BooleanField(default=False, 
                                   verbose_name=_('Завершен'), 
                                   help_text=_('Отметка о завершении урока'))
    date_completed = models.DateTimeField(null=True, blank=True, 
                                         verbose_name=_('Дата завершения'), 
                                         help_text=_('Дата и время завершения урока'))
    
    class Meta:
        verbose_name = _('Прогресс курса')
        verbose_name_plural = _('Прогресс курсов')
        unique_together = ['user', 'lesson']
    
    def __str__(self):
        return f'Прогресс {self.user.username} по {self.lesson.title}'


class CourseMaterial(models.Model):
    """
    Скачиваемые материалы курса
    """
    MATERIAL_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('word', 'Word'),
        ('other', 'Other'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials', 
                              verbose_name=_('Курс'), 
                              help_text=_('Курс, к которому относится материал'))
    title = models.CharField(max_length=255, 
                            verbose_name=_('Название'), 
                            help_text=_('Название материала'))
    file = models.FileField(upload_to='course_materials/', 
                           verbose_name=_('Файл'), 
                           help_text=_('Загружаемый файл материала'))
    type = models.CharField(max_length=10, choices=MATERIAL_TYPE_CHOICES, 
                           verbose_name=_('Тип'), 
                           help_text=_('Тип файла материала'))
    size = models.CharField(max_length=20, 
                           verbose_name=_('Размер'), 
                           help_text=_('Размер файла в удобочитаемом формате'))
    
    class Meta:
        verbose_name = _('Материал курса')
        verbose_name_plural = _('Материалы курса')
    
    def __str__(self):
        return f'{self.title} ({self.course.title})'


class CourseReview(models.Model):
    """
    Отзывы о курсах
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews', 
                              verbose_name=_('Курс'), 
                              help_text=_('Курс, к которому относится отзыв'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_reviews', 
                            verbose_name=_('Пользователь'), 
                            help_text=_('Пользователь, оставивший отзыв'))
    rating = models.PositiveIntegerField(
                                        verbose_name=_('Оценка'), 
                                        help_text=_('Оценка курса от 1 до 5'))
    date = models.DateField(auto_now_add=True, 
                           verbose_name=_('Дата'), 
                           help_text=_('Дата создания отзыва'))
    comment = models.TextField(
                              verbose_name=_('Комментарий'), 
                              help_text=_('Текст отзыва'))
    
    class Meta:
        verbose_name = _('Отзыв о курсе')
        verbose_name_plural = _('Отзывы о курсе')
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f'Отзыв от {self.user.username} о {self.course.title}'


class Discussion(models.Model):
    """
    Обсуждения на форуме
    """
    title = models.CharField(max_length=255, 
                            verbose_name=_('Заголовок'), 
                            help_text=_('Заголовок обсуждения'))
    description = models.TextField(
                                  verbose_name=_('Описание'), 
                                  help_text=_('Текст обсуждения'))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='discussions', 
                                verbose_name=_('Категория'), 
                                help_text=_('Категория, к которой относится обсуждение'))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussions', 
                              verbose_name=_('Автор'), 
                              help_text=_('Пользователь, создавший обсуждение'))
    date = models.DateTimeField(auto_now_add=True, 
                               verbose_name=_('Дата создания'), 
                               help_text=_('Дата и время создания обсуждения'))
    replies = models.PositiveIntegerField(default=0, 
                                         verbose_name=_('Ответы'), 
                                         help_text=_('Количество ответов в обсуждении'))
    views = models.PositiveIntegerField(default=0, 
                                       verbose_name=_('Просмотры'), 
                                       help_text=_('Количество просмотров обсуждения'))
    likes = models.PositiveIntegerField(default=0, 
                                       verbose_name=_('Лайки'), 
                                       help_text=_('Количество лайков обсуждения'))
    tags = models.ManyToManyField(Tag, related_name='discussions', 
                                 verbose_name=_('Теги'), 
                                 help_text=_('Теги, связанные с обсуждением'))
    pinned = models.BooleanField(default=False, 
                                verbose_name=_('Закрепленное'), 
                                help_text=_('Отметка о том, что обсуждение закреплено'))
    solved = models.BooleanField(default=False, 
                                verbose_name=_('Решено'), 
                                help_text=_('Отметка о том, что проблема в обсуждении решена'))
    
    class Meta:
        verbose_name = _('Обсуждение')
        verbose_name_plural = _('Обсуждения')
        ordering = ['-pinned', '-date']
    
    def __str__(self):
        return self.title


class Reply(models.Model):
    """
    Ответы к обсуждениям
    """
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='discussion_replies', 
                                  verbose_name=_('Обсуждение'), 
                                  help_text=_('Обсуждение, к которому относится ответ'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_replies', 
                            verbose_name=_('Пользователь'), 
                            help_text=_('Пользователь, оставивший ответ'))
    content = models.TextField(
                              verbose_name=_('Содержание'), 
                              help_text=_('Текст ответа'))
    date = models.DateTimeField(auto_now_add=True, 
                               verbose_name=_('Дата'), 
                               help_text=_('Дата и время создания ответа'))
    likes = models.PositiveIntegerField(default=0, 
                                       verbose_name=_('Лайки'), 
                                       help_text=_('Количество лайков ответа'))
    
    class Meta:
        verbose_name = _('Ответ')
        verbose_name_plural = _('Ответы')
        ordering = ['date']
    
    def __str__(self):
        return f'Ответ от {self.user.username} в {self.discussion.title}'


class Achievement(models.Model):
    """
    Достижения пользователей
    """
    title = models.CharField(max_length=100, 
                            verbose_name=_('Название'), 
                            help_text=_('Название достижения'))
    description = models.TextField(
                                  verbose_name=_('Описание'), 
                                  help_text=_('Описание условий получения достижения'))
    icon = models.CharField(max_length=50, 
                           verbose_name=_('Иконка'), 
                           help_text=_('Название иконки для отображения достижения'))
    
    class Meta:
        verbose_name = _('Достижение')
        verbose_name_plural = _('Достижения')
    
    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    """
    Связь между пользователем и достижениями
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements', 
                            verbose_name=_('Пользователь'), 
                            help_text=_('Пользователь, получивший достижение'))
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, 
                                   verbose_name=_('Достижение'), 
                                   help_text=_('Полученное достижение'))
    date_earned = models.DateTimeField(auto_now_add=True, 
                                      verbose_name=_('Дата получения'), 
                                      help_text=_('Дата и время получения достижения'))
    
    class Meta:
        verbose_name = _('Достижение пользователя')
        verbose_name_plural = _('Достижения пользователя')
        unique_together = ['user', 'achievement']
    
    def __str__(self):
        return f'{self.user.username} - {self.achievement.title}'


class UserActivity(models.Model):
    """
    Активность пользователя
    """
    ACTIVITY_TYPE_CHOICES = [
        ('course', 'Курс'),
        ('test', 'Тест'),
        ('article', 'Статья'),
        ('discussion', 'Обсуждение'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', 
                            verbose_name=_('Пользователь'), 
                            help_text=_('Пользователь, совершивший действие'))
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, 
                                    verbose_name=_('Тип активности'), 
                                    help_text=_('Тип действия пользователя'))
    title = models.CharField(max_length=255, 
                            verbose_name=_('Название'), 
                            help_text=_('Название элемента, с которым взаимодействовал пользователь'))
    date = models.DateTimeField(auto_now_add=True, 
                               verbose_name=_('Дата'), 
                               help_text=_('Дата и время активности'))
    progress = models.PositiveIntegerField(null=True, blank=True, 
                                          verbose_name=_('Прогресс'), 
                                          help_text=_('Процент выполнения (для курсов)'))
    score = models.PositiveIntegerField(null=True, blank=True, 
                                       verbose_name=_('Оценка'), 
                                       help_text=_('Полученная оценка (для тестов)'))
    
    class Meta:
        verbose_name = _('Активность пользователя')
        verbose_name_plural = _('Активности пользователя')
        ordering = ['-date']
    
    def __str__(self):
        return f'{self.user.username} - {self.activity_type} - {self.title}'


class Test(models.Model):
    """
    Модель для хранения тестов по кибербезопасности
    """
    LEVEL_CHOICES = [
        ('Начальный', 'Начальный'),
        ('Средний', 'Средний'),
        ('Продвинутый', 'Продвинутый'),
    ]
    
    title = models.CharField(max_length=255, 
                            verbose_name=_('Название'), 
                            help_text=_('Название теста'))
    description = models.TextField(
                                  verbose_name=_('Краткое описание'), 
                                  help_text=_('Краткое описание теста'))
    long_description = models.TextField(blank=True, 
                                       verbose_name=_('Полное описание'), 
                                       help_text=_('Подробное описание теста'))
    image = models.URLField(
                           verbose_name=_('Изображение'), 
                           help_text=_('URL изображения для теста'))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='tests', 
                                verbose_name=_('Категория'), 
                                help_text=_('Категория, к которой относится тест'))
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, 
                            verbose_name=_('Уровень сложности'), 
                            help_text=_('Уровень сложности теста'))
    duration = models.CharField(max_length=50, 
                               verbose_name=_('Продолжительность'), 
                               help_text=_('Продолжительность прохождения теста'))
    questions_count = models.PositiveIntegerField(default=0, 
                                                verbose_name=_('Количество вопросов'), 
                                                help_text=_('Общее количество вопросов в тесте'))
    participants = models.PositiveIntegerField(default=0, 
                                             verbose_name=_('Участники'), 
                                             help_text=_('Количество участников, прошедших тест'))
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0, 
                                verbose_name=_('Рейтинг'), 
                                help_text=_('Средний рейтинг теста'))
    passing_score = models.PositiveIntegerField(default=70, 
                                              verbose_name=_('Проходной балл'), 
                                              help_text=_('Минимальный процент правильных ответов для прохождения теста'))
    max_attempts = models.PositiveIntegerField(default=0, 
                                             verbose_name=_('Максимальное количество попыток'), 
                                             help_text=_('Максимальное количество попыток прохождения теста (0 = без ограничений)'))
    featured = models.BooleanField(default=False, 
                                  verbose_name=_('Рекомендованный'), 
                                  help_text=_('Отметка о том, что тест является рекомендованным'))
    tags = models.ManyToManyField(Tag, related_name='tests', 
                                 verbose_name=_('Теги'), 
                                 help_text=_('Теги, связанные с тестом'))
    created_at = models.DateTimeField(auto_now_add=True, 
                                     verbose_name=_('Дата создания'), 
                                     help_text=_('Дата создания теста'))
    updated_at = models.DateTimeField(auto_now=True, 
                                     verbose_name=_('Дата обновления'), 
                                     help_text=_('Дата последнего обновления теста'))
    
    class Meta:
        verbose_name = _('Тест')
        verbose_name_plural = _('Тесты')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class TestQuestion(models.Model):
    """
    Вопросы для тестов
    """
    QUESTION_TYPE_CHOICES = [
        ('single', 'Один вариант'),
        ('multiple', 'Несколько вариантов'),
        ('text', 'Текстовый ответ'),
        ('true_false', 'Истина/Ложь'),
    ]
    
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions', 
                            verbose_name=_('Тест'), 
                            help_text=_('Тест, к которому относится вопрос'))
    topic = models.CharField(max_length=100, blank=True, 
                            verbose_name=_('Тема'), 
                            help_text=_('Тема или раздел, к которому относится вопрос'))
    question_text = models.TextField(
                                    verbose_name=_('Текст вопроса'), 
                                    help_text=_('Формулировка вопроса'))
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='single', 
                                    verbose_name=_('Тип вопроса'), 
                                    help_text=_('Тип вопроса (один вариант, несколько и т.д.)'))
    options = models.JSONField(default=list, 
                              verbose_name=_('Варианты ответов'), 
                              help_text=_('Варианты ответов в формате JSON для выбора'))
    correct_answer = models.JSONField(
                                     verbose_name=_('Правильный ответ'), 
                                     help_text=_('Правильный ответ или ответы в формате JSON'))
    explanation = models.TextField(blank=True, 
                                  verbose_name=_('Объяснение'), 
                                  help_text=_('Объяснение правильного ответа'))
    difficulty = models.PositiveIntegerField(default=1, 
                                           verbose_name=_('Сложность'), 
                                           help_text=_('Уровень сложности вопроса от 1 до 5'))
    points = models.PositiveIntegerField(default=1, 
                                        verbose_name=_('Баллы'), 
                                        help_text=_('Количество баллов за правильный ответ'))
    order = models.PositiveIntegerField(default=0, 
                                       verbose_name=_('Порядок'), 
                                       help_text=_('Порядок отображения вопроса в тесте'))
    
    class Meta:
        verbose_name = _('Вопрос теста')
        verbose_name_plural = _('Вопросы тестов')
        ordering = ['test', 'order']
        unique_together = ['test', 'order']
    
    def __str__(self):
        return f"{self.test.title} - Вопрос {self.order}"


class TestAttempt(models.Model):
    """
    Попытки прохождения тестов пользователями
    """
    STATUS_CHOICES = [
        ('in_progress', 'В процессе'),
        ('completed', 'Завершен'),
        ('expired', 'Истек'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts', 
                            verbose_name=_('Пользователь'), 
                            help_text=_('Пользователь, выполняющий тест'))
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts', 
                            verbose_name=_('Тест'), 
                            help_text=_('Тест, который проходит пользователь'))
    start_time = models.DateTimeField(auto_now_add=True, 
                                     verbose_name=_('Время начала'), 
                                     help_text=_('Время начала попытки'))
    end_time = models.DateTimeField(null=True, blank=True, 
                                   verbose_name=_('Время окончания'), 
                                   help_text=_('Время окончания попытки'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', 
                             verbose_name=_('Статус'), 
                             help_text=_('Текущий статус попытки'))
    score = models.PositiveIntegerField(null=True, blank=True, 
                                       verbose_name=_('Балл'), 
                                       help_text=_('Итоговый балл в процентах'))
    answers = models.JSONField(default=dict, 
                              verbose_name=_('Ответы'), 
                              help_text=_('Ответы пользователя в формате JSON'))
    attempt_number = models.PositiveIntegerField(default=1, 
                                               verbose_name=_('Номер попытки'), 
                                               help_text=_('Порядковый номер попытки пользователя для данного теста'))
    
    class Meta:
        verbose_name = _('Попытка теста')
        verbose_name_plural = _('Попытки тестов')
        ordering = ['-start_time']
        unique_together = ['user', 'test', 'attempt_number']
    
    def __str__(self):
        return f"{self.user.username} - {self.test.title} - Попытка {self.attempt_number}"


class TestResult(models.Model):
    """
    Результаты тестов
    """
    attempt = models.OneToOneField(TestAttempt, on_delete=models.CASCADE, related_name='result', 
                                  verbose_name=_('Попытка'), 
                                  help_text=_('Попытка теста, для которой сохраняется результат'))
    total_questions = models.PositiveIntegerField(
                                                verbose_name=_('Всего вопросов'), 
                                                help_text=_('Общее количество вопросов в тесте'))
    correct_answers = models.PositiveIntegerField(
                                                verbose_name=_('Правильных ответов'), 
                                                help_text=_('Количество правильных ответов'))
    score_percent = models.PositiveIntegerField(
                                              verbose_name=_('Процент правильных'), 
                                              help_text=_('Процент правильных ответов'))
    time_spent = models.DurationField(
                                     verbose_name=_('Затраченное время'), 
                                     help_text=_('Общее время, затраченное на тест'))
    passed = models.BooleanField(
                                verbose_name=_('Пройден'), 
                                help_text=_('Флаг, указывающий, что тест пройден успешно'))
    feedback = models.TextField(blank=True, 
                               verbose_name=_('Отзыв'), 
                               help_text=_('Отзыв системы о результатах'))
    detailed_results = models.JSONField(default=dict, 
                                       verbose_name=_('Детальные результаты'), 
                                       help_text=_('Детальная информация о результатах по темам и вопросам'))
    created_at = models.DateTimeField(auto_now_add=True, 
                                     verbose_name=_('Дата создания'), 
                                     help_text=_('Дата создания результата'))
    
    class Meta:
        verbose_name = _('Результат теста')
        verbose_name_plural = _('Результаты тестов')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.attempt.user.username} - {self.attempt.test.title} - {self.score_percent}%"
