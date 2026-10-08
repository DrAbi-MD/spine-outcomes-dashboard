from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from registry.views import RegistryLoginView
urlpatterns = [path('login/', RegistryLoginView.as_view(template_name='registry/login.html'), name='login'), path('logout/', LogoutView.as_view(), name='logout'), path('', include('registry.urls'))]
