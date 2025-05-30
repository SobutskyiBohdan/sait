from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='User')
    book = models.ForeignKey('Book', on_delete=models.CASCADE, verbose_name='Book')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Added')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Favorite book'
        verbose_name_plural = 'Favorite books'
        unique_together = ('user', 'book')  
        
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['book']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title}"


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Genre'
        verbose_name_plural = 'Genres'
    
    def __str__(self):
        return self.name

class Book(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    title = models.CharField(max_length=255, verbose_name='title')
    isbn = models.CharField(max_length=20, blank=True, null=True, verbose_name='ISBN')
    image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    genre = models.ForeignKey(
        Genre, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Жанр'
    )
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        verbose_name='Price'
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name='Rating'
    )
    in_stock = models.BooleanField(default=True, verbose_name='In stock')
    availability = models.CharField(max_length=100, blank=True, verbose_name='Available')
    
    source_url = models.URLField(blank=True, null=True, verbose_name='URL sources')
    last_scraped = models.DateTimeField(blank=True, null=True, verbose_name='Last update')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['genre']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"{self.title}"
    
    def get_absolute_url(self):
        return reverse('book-detail', kwargs={'pk': self.pk})
    
    @property
    def rating_display(self):
        return '★' * self.rating + '☆' * (5 - self.rating)

class ScrapingLog(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    total_books_found = models.IntegerField(default=0)
    books_created = models.IntegerField(default=0)
    books_updated = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('running', 'Виконується'),
            ('completed', 'Завершено'),
            ('failed', 'Помилка'),
            ('interrupted', 'Перервано')
        ],
        default='running'
    )
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Scraping log'
        verbose_name_plural = 'Scraping logs'
    
    def __str__(self):
        return f"Scraping {self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.status}"