from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from django.contrib.auth.models import User
from .models import Wallet, Profile, Shop


def register_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created successfully.')
            return redirect('store:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'store/auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(username=username, password=password)
            if user is None:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                next_url = request.GET.get('next') or reverse('store:home')
                return redirect(next_url)
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'store/auth/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('store:home')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.profile, user=request.user)
        if form.is_valid():
            profile = form.save()
            if profile.is_seller and not request.user.shops.exists():
                Shop.objects.create(
                    owner=request.user,
                    name=f"{request.user.username}'s Shop",
                    description='Welcome to my shop!',
                    is_active=True
                )
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('store:profile')
    else:
        form = UserProfileForm(instance=request.user.profile, user=request.user)
    
    context = {
        'form': form,
        'user': request.user,
        'profile': request.user.profile,
        'wallet': request.user.wallet,
    }
    return render(request, 'store/auth/profile.html', context)


@login_required
def dashboard_view(request):
    context = {
        'user': request.user,
        'profile': request.user.profile,
        'wallet': request.user.wallet,
        'shops': request.user.shops.all(),
        'orders': request.user.orders.all().order_by('-order_date')[:5],
        'favorites': request.user.favorites.all()[:5],
    }
    return render(request, 'store/auth/dashboard.html', context)


def check_username_availability(request):
    if request.method == 'GET':
        username = request.GET.get('username', '')
        if username:
            exists = User.objects.filter(username=username).exists()
            return JsonResponse({'available': not exists})
    return JsonResponse({'error': 'Invalid request'})


def check_email_availability(request):
    if request.method == 'GET':
        email = request.GET.get('email', '')
        if email:
            exists = User.objects.filter(email=email).exists()
            return JsonResponse({'available': not exists})
    return JsonResponse({'error': 'Invalid request'}) 