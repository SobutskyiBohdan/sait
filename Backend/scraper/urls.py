from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

urlpatterns = [
    path('start/', views.StartScrapingView.as_view(), name='start-scraping'),
    path('status/', views.ScrapingStatusView.as_view(), name='scraping-status'),
    path('status/<int:scraping_id>/', views.ScrapingStatusView.as_view(), name='scraping-status-detail'),
    path('stop/', views.StopScrapingView.as_view(), name='stop-scraping'),
    # path('stats/', views.ScrapingStatsView.as_view(), name='scraping-stats'),
    path('book_list/', views.BookListView.as_view(), name='all-books'),
    path('book_detail/<int:pk>/', views.BookDetailView.as_view(), name='detail-books'),
    path('book_create/', views.BookCreateView.as_view(), name='create-books'),
    path('book_recommended/', views.BookRecommendedView.as_view(), name='recommended_books'),
    path('book_update/<int:pk>/', views.BookUpdateView.as_view(), name='update-books'),
    path('book_delete/<int:pk>/', views.BookDeleteView.as_view(), name='delete_books'),
    path('book_search/', views.BookSearchView.as_view(), name='book-search'),
    path('book_stats/', views.BookStatsView.as_view(), name='book-stats'),
    path('book_favorites/', views.FavoriteListView.as_view(), name='favorite-list'),
    path('book_favorites_add/', views.FavoriteCreateView.as_view(), name='favorite-create'),
    path('book_favorites_remove/<int:book_id>/', views.FavoriteRemoveByBookView.as_view(), name='favorite-remove-by-book'),
    path('book_favorites_toggle/<int:book_id>/', views.FavoriteToggleView.as_view(), name='favorite-toggle'),
]