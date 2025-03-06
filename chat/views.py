import logging

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import ProfileUpdateForm, StoryForm
from .models import ChatRoom, Message, PrivateChat, Profile, Story

logger = logging.getLogger(__name__)

def index(request):
    """Default landing page that displays the login/register form."""
    return render(request, 'chat/index.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user with provided credentials
        user = authenticate(request, username=username, password=password)
        if user:
            if not user.is_active:
                messages.error(request, "Your account is disabled.")
                return render(request, 'chat/index.html', {'error': 'Your account is disabled.'})
            login(request, user)
            Profile.objects.get_or_create(user=user)
            logger.info(f"User '{username}' logged in successfully.")
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials. Please try again.")
            return render(request, 'chat/index.html', {'error': 'Invalid credentials'})
    return render(request, 'chat/index.html')




@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
        logger.info(f"Profile created for user '{request.user.username}' on-demand.")
    avatar_url = profile.avatar.url if profile.avatar else None
    return render(request, 'chat/profile.html', {'profile': profile, 'avatar_url': avatar_url})


@login_required
def update_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
        logger.info(f"Profile created for user '{request.user.username}' on-demand in update_profile.")
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileUpdateForm(instance=profile)
    return render(request, 'chat/profile_update.html', {'form': form})


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email    = request.POST.get('email')
        password = request.POST.get('password')
        if username and password:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Username and password are required.")
    return render(request, 'chat/index.html')


def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('index')

@login_required
def home_page(request):
    """Displays user's stories and their friends' stories."""
    
    # Get my stories
    my_stories = Story.objects.filter(author=request.user).order_by('-created_at')

    # ✅ Get friends' User objects instead of Profile objects
    profile, created = Profile.objects.get_or_create(user=request.user)  
    friends_users = profile.friends.all().values_list('user', flat=True)  # Extract User objects

    # ✅ Get stories from friends (using User objects)
    friends_stories = Story.objects.filter(author__in=friends_users).order_by('-created_at')

    context = {
        'my_stories': my_stories,
        'friends_stories': friends_stories,
    }
    return render(request, 'chat/home.html', context)

@login_required
def room(request, room_name):
    room_obj, _ = ChatRoom.objects.get_or_create(name=room_name)
    msgs = Message.objects.filter(room=room_obj).order_by('timestamp')
    return render(request, 'chat/chat_room.html', {'room_name': room_name, 'messages': msgs})


@login_required
def start_private_chat(request, target_username):
    target_user = get_object_or_404(User, username=target_username)
    chats = PrivateChat.objects.filter(participants=request.user)
    chat = None
    for c in chats:
        participants = list(c.participants.all())
        if len(participants) == 2 and target_user in participants:
            chat = c
            break
    if not chat:
        chat = PrivateChat.objects.create()
        chat.participants.add(request.user, target_user)
        logger.info(f"Created new private chat between '{request.user.username}' and '{target_user.username}'.")
    return redirect('private_chat', chat_id=chat.id)


@login_required
def private_chat_view(request, chat_id):
    chat_obj = get_object_or_404(PrivateChat, id=chat_id)
    if request.user not in chat_obj.participants.all():
        messages.error(request, "You do not have access to this chat.")
        return render(request, 'chat/error.html', {'error': 'You do not have access to this chat.'})
    msgs = chat_obj.messages.all()
    return render(request, 'chat/private_chat.html', {'chat': chat_obj, 'messages': msgs})


@login_required
def user_directory(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'chat/user_directory.html', {'users': users})


@login_required
def private_chat_list(request):
    chats = PrivateChat.objects.filter(participants=request.user)
    return render(request, 'chat/private_chat_list.html', {'chats': chats})




@login_required
def add_remove_friend(request, username):
    """Toggles a friend (add or remove) for the logged-in user."""
    friend = get_object_or_404(User, username=username)
    profile = Profile.objects.get(user=request.user)

    if profile.friends.filter(id=friend.profile.id).exists():
        profile.friends.remove(friend.profile)
        messages.success(request, f"You removed {friend.username} from friends.")
    else:
        profile.friends.add(friend.profile)
        messages.success(request, f"You added {friend.username} as a friend.")

    return redirect('home')

@login_required
def upload_story(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        media = request.FILES.get('media')
        if title and content:
            story = Story.objects.create(author=request.user, title=title, content=content, media=media)
            logger.info(f"Story uploaded by {request.user.username}: {title}")
            messages.success(request, "Your story has been uploaded.")
        else:
            messages.error(request, "Title and content are required.")
        return redirect('home')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('home')


@login_required
def edit_story(request, story_id):
    """Allows a user to edit their story."""
    story = get_object_or_404(Story, id=story_id, author=request.user)

    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES, instance=story)
        if form.is_valid():
            form.save()
            messages.success(request, "Story updated successfully.")
            return redirect('home')  # Redirect to home after editing
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StoryForm(instance=story)

    return render(request, 'chat/edit_story.html', {'form': form, 'story': story})

@login_required
def create_room(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        if room_name:
            room_obj, created = ChatRoom.objects.get_or_create(name=room_name)
            if created:
                messages.success(request, f"Room '{room_name}' created successfully.")
            else:
                messages.info(request, f"Room '{room_name}' already exists.")
            return redirect('room', room_name=room_name)
        else:
            messages.error(request, "Please provide a valid room name.")
            return redirect('home')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('home')


# ----------------------- Deletion Views -----------------------

@login_required
def delete_story(request, story_id):
    """Allow users to delete their own story."""
    story = get_object_or_404(Story, id=story_id, author=request.user)
    if request.method == 'POST':
        story.delete()
        messages.success(request, "Story deleted successfully.")
        return redirect('home')
    return render(request, 'chat/confirm_delete.html', {'object': story, 'type': 'Story'})


@login_required
def delete_private_chat(request, chat_id):
    """Allow users to delete a private chat conversation they are a part of."""
    chat = get_object_or_404(PrivateChat, id=chat_id)
    if request.user not in chat.participants.all():
        messages.error(request, "You do not have permission to delete this chat.")
        return redirect('private_chat', chat_id=chat_id)
    if request.method == 'POST':
        chat.delete()
        messages.success(request, "Private chat deleted successfully.")
        return redirect('home')
    return render(request, 'chat/confirm_delete.html', {'object': chat, 'type': 'Private Chat'})
