from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404
from django.utils.timezone import now
from .models import Category, Post, Comment
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .forms import CommentForm, PostForm
from django.views.generic import TemplateView
from django.contrib.auth.models import User
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from .forms import CommentForm
from pages.views import custom_403_view, custom_404_view
from .forms import EditProfileForm
from django.views.generic import UpdateView, TemplateView
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from .forms import EditProfileForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.timezone import now

User = get_user_model()


def get_published_posts():
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=now(),
        category__is_published=True,
    ).select_related("author", "category", "location")


def index(request):
    post_list = get_published_posts()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/index.html', {'page_obj': page_obj})


def category_posts(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)

    # Проверяем, опубликована ли категория
    if not category.is_published:
        return custom_404_view(request, None)

    posts = category.posts.filter(is_published=True, pub_date__lte=now())
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj,
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Проверяем, опубликован ли пост
    if not post.is_published:
        # Если пользователь автор поста, разрешаем доступ
        if post.author != request.user:
            raise Http404("Пост не найден.")

    # Проверяем, опубликована ли категория
    if not post.category.is_published:
        # Если пользователь автор поста, разрешаем доступ
        if post.author != request.user:
            raise Http404("Категория не найдена.")

    # Проверяем, отложен ли пост
    if post.pub_date > timezone.now():
        # Если пользователь не автор поста, возвращаем 404
        if post.author != request.user:
            raise Http404("Пост не найден.")

    comments = post.comments.order_by('created_at')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = CommentForm()

    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.post_set.all()
    paginator = Paginator(post_list, 10)  # Пагинация
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'pages/profile.html',
        {'user': user, 'page_obj': page_obj})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.pub_date = timezone.now()  # Установка даты публикации
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)  # Заполняем форму данными поста

    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    # Проверяем, является ли текущий пользователь автором комментария
    if comment.author != request.user:
        return custom_403_view(request, None)

    form = CommentForm(request.POST or None, instance=comment)

    # Если метод POST и форма валидна, сохраняем изменения
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)

    # Возвращаем шаблон редактирования комментария
    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
        'is_edit': True
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    # Проверка, является ли текущий пользователь автором комментария
    if comment.author != request.user:
        return custom_403_view(request, None)

    # Если метод GET, отобразим комментарий для подтверждения удаления
    if request.method == 'GET':
        return render(request, 'blog/comment.html', {
            'comment': comment,
            'is_delete': True
        })

    # Если метод POST, удаляем комментарий
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, 'blog/comment.html', {
        'comment': comment,
        'is_delete': True
    })


@login_required
def delete_post(request, post_id):
    # Получаем пост и проверяем, что автор совпадает
    post = get_object_or_404(Post, id=post_id, author=request.user)

    if request.method == 'POST':
        # Удаляем пост
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    return render(request, 'blog/delete_post.html', {'post': post})


class ProfilePageView(TemplateView):
    template_name = 'blog/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, username=self.kwargs['username'])
        context['profile'] = user
        post_list = user.posts.all()
        paginator = Paginator(post_list, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        return context


@method_decorator(login_required, name='dispatch')
class EditProfileView(UpdateView):
    model = User
    form_class = EditProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username})
