from django.urls import path
from .views import (
    add_remove_friend, edit_story, index, user_login, user_logout, register, profile_view, update_profile,
    room, start_private_chat, private_chat_view, user_directory, private_chat_list,
    home_page, upload_story, create_room, delete_story, delete_private_chat
)

urlpatterns = [
    path('', home_page, name='home'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('register/', register, name='register'),
    path('profile/', profile_view, name='profile'),
    path('profile/update/', update_profile, name='update_profile'),
    path('edit_story/<int:story_id>/', edit_story, name='edit_story'),
    path('directory/', user_directory, name='user_directory'),
    path('private/start/<str:target_username>/', start_private_chat, name='start_private_chat'),
    path('private/<int:chat_id>/', private_chat_view, name='private_chat'),
    path('room/<str:room_name>/', room, name='room'),
    path('upload_story/', upload_story, name='upload_story'),
    path('create_room/', create_room, name='create_room'),
    path('delete_story/<int:story_id>/', delete_story, name='delete_story'),
     path('friends/toggle/<str:username>/', add_remove_friend, name='add_remove_friend'),
    path('delete_private_chat/<int:chat_id>/', delete_private_chat, name='delete_private_chat'),
]
