import io
import threading
import random
from contextlib import redirect_stdout, redirect_stderr

from django.core.management import call_command
from django.utils import timezone
from django.http import Http404
from django.db.models import Q
from django.db.models import Count

from rest_framework import status, filters
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView, 
    RetrieveAPIView, 
    CreateAPIView, 
    UpdateAPIView, 
    DestroyAPIView
)
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin
)
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters

from .models import Book, ScrapingLog, Favorite, Genre
from .serializers import BookListSerializer, BookSerializer, ScrapingLogSerializer, FavoriteListSerializer, FavoriteCreateSerializer


class BookFilter(django_filters.FilterSet):
    genre = django_filters.CharFilter(
        field_name='genre', 
        lookup_expr='icontains',
        help_text="Genre filtration"
    )
    
    title = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        help_text="Searching by book's name"
    )
    
    search = django_filters.CharFilter(
        method='filter_search',
        help_text="General search"
    )
    
    class Meta:
        model = Book
        fields = ['genre', 'title', 'search']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) | 
            Q(description__icontains=value)
        )


class AdminRequiredMixin:
    permission_classes = [IsAdminUser]


class BookQuerysetMixin:
    queryset = Book.objects.all()
    
    filter_backends = [
        DjangoFilterBackend, 
        filters.SearchFilter, 
        filters.OrderingFilter
    ]
    filterset_class = BookFilter
    search_fields = ['title', 'description', 'genre', 'image']
    ordering_fields = ['title', 'created_at']
    ordering = ['-created_at']  

class FavoriteListView(ListAPIView):
    serializer_class = FavoriteListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Favorite.objects.filter(user=self.request.user).select_related('book', 'book__genre')
        genre = self.request.query_params.get('genre', None)
        title = self.request.query_params.get('title', None)
        search = self.request.query_params.get('search', None)
        rating = self.request.query_params.get('rating', None)

        if genre:
            queryset = queryset.filter(book__genre__name__icontains=genre)
                
        if title:
            queryset = queryset.filter(book__title__icontains=title)
            
        if rating:
            try:
                rating_value = int(rating)
                if 1 <= rating_value <= 5:
                    queryset = queryset.filter(book__rating=rating_value)
            except ValueError:
                pass
            
        if search:
            queryset = queryset.filter(
                Q(book__title__icontains=search) | 
                Q(book__description__icontains=search)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        
        active_filters = {}
        for param in ['genre', 'title', 'rating', 'search']:
            value = request.query_params.get(param)
            if value:
                active_filters[param] = value
        
        response_data = {
            'count': queryset.count(),
            'active_filters': active_filters,
            'results': serializer.data
        }
        
        return Response(response_data)

class FavoriteCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = FavoriteCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            favorite = serializer.save()
            response_serializer = FavoriteListSerializer(favorite)
            return Response(
                {
                    'message': 'Book was added to favorites',
                    'favorite': response_serializer.data
                }, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FavoriteRemoveByBookView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, book_id, *args, **kwargs):
        try:
            book = get_object_or_404(Book, id=book_id)
            favorite = get_object_or_404(Favorite, user=request.user, book=book)
            favorite.delete()
            
            return Response(
                {'message': f'Book "{book.title}" deleted from favorite'}, 
                status=status.HTTP_200_OK
            )
        except Favorite.DoesNotExist:
            return Response(
                {'error': 'This book was not in favorites'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class FavoriteToggleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, book_id, *args, **kwargs):
        try:
            book = get_object_or_404(Book, id=book_id)
            favorite, created = Favorite.objects.get_or_create(
                user=request.user, 
                book=book
            )
            
            if created:
                serializer = FavoriteListSerializer(favorite)
                return Response(
                    {
                        'message': f'Книга "{book.title}" додана в улюблене',
                        'action': 'added',
                        'favorite': serializer.data
                    }, 
                    status=status.HTTP_201_CREATED
                )
            else:
                favorite.delete()
                return Response(
                    {
                        'message': f'Книга "{book.title}" видалена з улюбленого',
                        'action': 'removed'
                    }, 
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class BookListView(BookQuerysetMixin, ListAPIView):
    serializer_class = BookListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        genre = self.request.query_params.get('genre', None)
        title = self.request.query_params.get('title', None)
        search = self.request.query_params.get('search', None)
        image = self.request.query_params.get('image', None)

        if genre:
            queryset = queryset.filter(genre__name__icontains=genre)
                
        if title:
            queryset = queryset.filter(title__icontains=title)

        if image:
            if image.lower() in ['true', '1', 'yes']:
                queryset = queryset.exclude(image__isnull=True).exclude(image='')
            elif image.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(Q(image__isnull=True) | Q(image=''))
            
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
    
        active_filters = {}
        for param in ['genre', 'title', 'image', 'search']:
            value = request.query_params.get(param)
            if value:
                active_filters[param] = value
        
        response_data = {
            'count': queryset.count(),
            'active_filters': active_filters,
            'results': serializer.data
        }
        
        return Response(response_data)


class BookRecommendedView(BookQuerysetMixin, ListAPIView):
    serializer_class = BookListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        genre = self.request.query_params.get('genre', None)
        title = self.request.query_params.get('title', None)
        search = self.request.query_params.get('search', None)
        image = self.request.query_params.get('image', None)

        if genre:
            queryset = queryset.filter(genre__name__icontains=genre)
                
        if title:
            queryset = queryset.filter(title__icontains=title)

        if image:
            if image.lower() in ['true', '1', 'yes']:
                queryset = queryset.exclude(image__isnull=True).exclude(image='')
            elif image.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(Q(image__isnull=True) | Q(image=''))
            
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        count = queryset.count()
        
        if count == 0:
            return Response({
                'detail': 'No books found matching the criteria',
                'active_filters': self._get_active_filters(request),
                'total_count': 0
            }, status=status.HTTP_404_NOT_FOUND)
        
        random_count = min(int(request.query_params.get('count', 4)), count)
        
        random_indices = random.sample(range(count), random_count)
        
        random_books = []
        for index in random_indices:
            book = queryset[index]
            random_books.append(book)
        
        serializer = self.get_serializer(random_books, many=True)
        
        response_data = {
            'count': random_count,
            'total_count': count,
            'active_filters': self._get_active_filters(request),
            'results': serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)
    
    def _get_active_filters(self, request):
        active_filters = {}
        for param in ['genre', 'title', 'image', 'search', 'count']:
            value = request.query_params.get(param)
            if value:
                active_filters[param] = value

        return active_filters


class BookDetailView(BookQuerysetMixin, RetrieveAPIView):
    serializer_class = BookSerializer
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            response_data = serializer.data
            
            if instance.image:
                response_data['image_metadata'] = {
                    'has_image': True,
                    'image_name': instance.image.name,
                    'image_size': instance.image.size if hasattr(instance.image, 'size') else None,
                }
            else:
                response_data['image_metadata'] = {
                    'has_image': False,
                    'image_name': None,
                    'image_size': None,
                }
            
            return Response(response_data)
            
        except Http404:
            return Response(
                {'detail': 'Book not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'detail': f'Error retrieving book: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BookCreateView(AdminRequiredMixin, BookQuerysetMixin, CreateAPIView):
    serializer_class = BookSerializer


class BookUpdateView(AdminRequiredMixin, BookQuerysetMixin, UpdateAPIView):
    serializer_class = BookSerializer


class BookDeleteView(AdminRequiredMixin, BookQuerysetMixin, DestroyAPIView):
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            "Item was successfully deleted!", 
            status=status.HTTP_204_NO_CONTENT
        )


class ScrapingLogQuerysetMixin:
    queryset = ScrapingLog.objects.all()
    serializer_class = ScrapingLogSerializer


class ScrapingValidationMixin:
    def check_running_scraping(self):
        return ScrapingLog.objects.filter(status='running').exists()
    
    def get_running_scraping_logs(self):
        return ScrapingLog.objects.filter(status='running')


class StartScrapingView(AdminRequiredMixin, ScrapingValidationMixin, CreateAPIView):
    serializer_class = ScrapingLogSerializer
    
    def create(self, request, *args, **kwargs):
        if self.check_running_scraping():
            return Response(
                {'error': 'Scraping is in work'}, 
                status=status.HTTP_409_CONFLICT
            )
        
        scraping_log = ScrapingLog.objects.create()
        
        pages_limit = request.data.get('pages', None)
        
        scraping_thread = threading.Thread(
            target=self._run_scraping, 
            args=(scraping_log, pages_limit)
        )
        scraping_thread.daemon = True
        scraping_thread.start()
        
        return Response({
            'message': 'Scraping started',
            'scraping_id': scraping_log.id,
            'status': 'running'
        }, status=status.HTTP_202_ACCEPTED)
    
    def _run_scraping(self, scraping_log, pages_limit=None):
        try:
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                if pages_limit:
                    call_command('scrape_books', pages=pages_limit)
                else:
                    call_command('scrape_books')
            
            scraping_log.status = 'completed'
            scraping_log.total_books_found = Book.objects.count()
            
        except Exception as e:
            scraping_log.status = 'failed'
            scraping_log.error_message = str(e)
        finally:
            scraping_log.finished_at = timezone.now()
            scraping_log.save()


from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

class ScrapingStatusView(AdminRequiredMixin, ScrapingLogQuerysetMixin, APIView):
    
    @swagger_auto_schema(
        operation_description="Get scraping status. If ID is specified, returns specific status, otherwise, returns last 10 records",
        operation_summary="Scraping status",
        tags=['Scraping'],
        manual_parameters=[
            openapi.Parameter(
                'scraping_id', 
                openapi.IN_QUERY, 
                description="ID of a specific scraping (optional)", 
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: openapi.Response(
                description="Scraping status",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID скрапінгу'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Статус (running, completed, failed, interrupted)'),
                        'started_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Час початку'),
                        'finished_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Час завершення'),
                        'total_products': openapi.Schema(type=openapi.TYPE_INTEGER, description='Загальна кількість товарів'),
                        'processed_products': openapi.Schema(type=openapi.TYPE_INTEGER, description='Оброблено товарів'),
                        'error_message': openapi.Schema(type=openapi.TYPE_STRING, description='Повідомлення про помилку'),
                    }
                )
            ),
            404: openapi.Response(
                description="Scraping was not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Scraping log not found')
                    }
                )
            ),
            403: openapi.Response(description="Access denied - administrator rights required"),
        }
    )
    def get(self, request, scraping_id=None, *args, **kwargs):
        if scraping_id:
            return self._get_specific_status(scraping_id)
        else:
            return self._get_recent_statuses()
    
    def _get_specific_status(self, scraping_id):
        try:
            log = ScrapingLog.objects.get(id=scraping_id)
            serializer = self.serializer_class(log)
            return Response(serializer.data)
        except ScrapingLog.DoesNotExist:
            return Response(
                {'error': 'Scraping log not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _get_recent_statuses(self):
        logs = ScrapingLog.objects.all()[:10]
        serializer = self.serializer_class(logs, many=True)
        return Response(serializer.data)


class StopScrapingView(AdminRequiredMixin, ScrapingValidationMixin, APIView):
    
    @swagger_auto_schema(
        operation_description="Stop all active scraping processes. Changes the status to 'interrupted' and sets the end time",
        operation_summary="Stop scraping",
        tags=['Scraping'],
        responses={
            200: openapi.Response(
                description="Scraping was stopped",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Scraping was stopped')
                    }
                )
            ),
            404: openapi.Response(
                description="No active scraping",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='No active scraping')
                    }
                )
            ),
            403: openapi.Response(description="Access denied - administrator rights required"),
        }
    )
    def post(self, request, *args, **kwargs):
        running_logs = self.get_running_scraping_logs()
        
        if not running_logs.exists():
            return Response(
                {'error': 'No active scraping'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        for log in running_logs:
            log.status = 'interrupted'
            log.finished_at = timezone.now()
            log.save()
        
        return Response({'message': 'Scraping was stopped'})


class BookSearchView(BookQuerysetMixin, ListAPIView):
    serializer_class = BookListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        filters = {}
        
        genre = self.request.query_params.get('genre')
        if genre:
            filters['genre__name__icontains'] = genre
                
        title = self.request.query_params.get('title')
        if title:
            filters['title__icontains'] = title
            
        if filters:
            queryset = queryset.filter(**filters)
    
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(genre__icontains=search)
            )
        
        return queryset
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        search_params = {
            'genre': request.query_params.get('genre'),
            'title': request.query_params.get('title'),
            'search': request.query_params.get('search'),
        }
        
        active_search = {k: v for k, v in search_params.items() if v}
        
        return Response({
            'search_parameters': active_search,
            'total_found': queryset.count(),
            'books': serializer.data
        })


class BookStatsView(APIView):
    def get(self, request):
        total_books = Book.objects.count()
        
        genres = Book.objects.values_list('genre', flat=True).distinct().order_by('genre')
        genres = [g for g in genres if g]  
        
        return Response({
            'total_books': total_books,
            'available_genres': list(genres),
            'filter_examples': {
                'by_genre': '/book_list/?genre=фантастика',
                'by_title': '/book_list/?title=гаррі',
                'general_search': '/book_list/?search=магія',
                'combined': '/book_list/?genre=фантастика&year_from=2010&search=дракон'
            }
        })
    
    def get(self, request, *args, **kwargs):
        stats = self._calculate_stats()
        return Response(stats)
    
    def _calculate_stats(self):
        total_books = Book.objects.count()
        recent_books = Book.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        last_scraping = ScrapingLog.objects.first()
        
        stats = {
            'total_books': total_books,
            'books_added_last_week': recent_books,
            'last_scraping': None
        }
        
        if last_scraping:
            stats['last_scraping'] = {
                'date': last_scraping.started_at,
                'status': last_scraping.status,
                'books_created': last_scraping.books_created,
                'books_updated': last_scraping.books_updated
            }
        
        return stats
