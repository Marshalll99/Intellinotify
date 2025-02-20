from django.urls import path
from .views import home, notifications

urlpatterns = [
    path('', home, name='home'),
    path('notifications/', notifications, name='notifications'),
]
