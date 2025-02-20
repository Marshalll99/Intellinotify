from django.urls import path
from .views import home, notifications, signup, signin

urlpatterns = [
    path('', home, name='home'),
    path('notifications/', notifications, name='notifications'),
    path('signup/', signup, name='signup'),
    path('signin/', signin, name='signin'),
]
