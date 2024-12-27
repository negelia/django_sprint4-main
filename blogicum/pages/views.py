from django.shortcuts import render
from .forms import RegistrationForm
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy


class AboutPageView(TemplateView):
    template_name = 'pages/about.html'


class RulesPageView(TemplateView):
    template_name = 'pages/rules.html'


class RegistrationPageView(CreateView):
    form_class = RegistrationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        return super().form_valid(form)


def custom_500_view(request):
    return render(request, 'pages/500.html', status=500)


def custom_404_view(request, exception):
    return render(request, 'pages/404.html', status=404)


def custom_403_view(request, exception):
    return render(request, 'pages/403csrf.html', status=403)
