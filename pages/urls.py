from django.urls import path
from .views import home, notifications, signup, signin
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', home, name='home'),
    path('notifications/', notifications, name='notifications'),
    path('signup/', signup, name='signup'),
    path('signin/', signin, name='signin'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
]
