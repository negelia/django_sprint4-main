from django.urls import path
from .views import AboutPageView, RulesPageView, RegistrationPageView

app_name = 'pages'

urlpatterns = [
    path('about/', AboutPageView.as_view(), name='about'),
    path('rules/', RulesPageView.as_view(), name='rules'),
    path(
        'auth/registration/',
        RegistrationPageView.as_view(),
        name='registration'),
]
