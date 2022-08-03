from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.models import User

from .models import Profile, Skill
from .forms import ProfileForm, SkillForm, CustomUserCreationForm, MessageForm
from .utils import paginateProfiles, searchProfiles


@login_required(login_url='login')
def profiles(request):
    profiles, search_query = searchProfiles(request)
    custom_range, profiles = paginateProfiles(request, profiles, 6)
    context = {
        'profiles': profiles,
        'search_query': search_query,
        'custom_range': custom_range
    }
    
    return render(request, 'profiles.html', context)


@login_required(login_url='login')
def user_profile(request, pk):
    profile = Profile.objects.get(pk=pk)
    main_skills = profile.skills.all()[:2]
    extra_skills = profile.skills.all()[2:]
    context = {
        'profile': profile,
        'extra_skills': extra_skills,
        'main_skills': main_skills,
    }
    
    return render(request, 'user_profile.html', context)


@login_required(login_url='login')
def profiles_by_skills(request, skill_slag):
    skill = get_object_or_404(Skill.objects.all(), slug=skill_slag)
    profiles = Profile.objects.filter(skills__in=[skill])
    context = {
        'profiles': profiles,
    }
    return render(request, 'profiles.html', context)


@login_required(login_url='login')
def user_account(request):
    profile = request.user.profile
    skills = profile.skills.all()
    projects = profile.projects.all()
    
    context = {
        'profile': profile,
        'skills': skills,
        'projects': projects,
    }
    return render(request, 'user_profile.html', context)


@login_required(login_url='login')
def edit_account(request):
    profile = request.user.profile
    form = ProfileForm(instance=profile)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('account')
        
    context = {
        'form': form,
    }
    return render(request, 'profile_form.html', context)


@login_required(login_url='login')
def create_skill(request):
    profile = request.user.profile
    form = SkillForm()
    
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill_slug = request.POST.get('slug')
            skill_description = request.POST.get('description')
            profile.skills.get_or_create(name=skill, slug=skill_slug, description=skill_description)
            messages.success(request, 'Навык добавлен')
            return redirect('account')

    context = {'form': form}
    return render(request, 'skill_form.html', context)


def register_user(request):
    page = 'register'
    form = CustomUserCreationForm()
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            # profile = Profile.objects.create(user=user, name=user.username, email=user.email)
            # profile.save()

            messages.success(request, 'Account successfully registered!')
            login(request, user)
            return redirect('edit-account')
        else:
            messages.info(request, 'Something wrong, please try again')
            
    context = {
        'form': form,
        'page': page
        }
    return render(request, 'login_register.html', context)


@login_required(login_url='login')
def delete_skill(request, skill_slug):
    skill = Skill.objects.get(slug=skill_slug)
    if request.method == 'POST':
        skill.delete()
        return redirect('account')
    
    context = {
        'object': skill
    }
    return render(request, 'delete.html', context)


@login_required(login_url='login')
def update_skill(request, skill_slug):
    skill = Skill.objects.get(slug=skill_slug)
    form = SkillForm(instance=skill)
    
    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            return redirect('account')
    context = {
        'form': form,
    }
    return render(request, 'skill_form.html', context)


def login_user(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('account')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User doesn\'t exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(request.GET['next'] if 'next' in request.GET else 'account')

        else:
            messages.error(request, 'Wrong username or password')
    context = {
        'page': page
    }
    return render(request, 'login_register.html', context)


@login_required(login_url='login')
def logout_user(request):
    logout(request)
    messages.info(request, 'You successfully logged out')
    return redirect('login')


@login_required(login_url='login')
def inbox(request):
    profile = request.user.profile
    messageRequests = profile.messages.all()
    unreadCount = messageRequests.filter(is_read=False).count()
    context = {'messageRequests': messageRequests, 'unreadCount': unreadCount}
    return render(request, 'inbox.html', context)


@login_required(login_url='login')
def view_message(request, pk):
    profile = request.user.profile
    message = profile.messages.get(id=pk)
    if message.is_read == False:
        message.is_read = True
        message.save()
    context = {'message': message}
    return render(request, 'message.html', context)



def create_message(request, username):
    recipient = Profile.objects.get(username=username)
    form = MessageForm()

    try:
        sender = request.user.profile
    except:
        sender = None

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = sender
            message.recipient = recipient

            if sender:
                message.name = sender.name
                message.email = sender.email
            message.save()

            messages.success(request, 'Your message was successfully sent!')
            return redirect('user-profile', username=recipient.username)

    context = {'recipient': recipient, 'form': form}
    return render(request, 'message_form.html', context)