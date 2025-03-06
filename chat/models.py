from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, default='avatars/default.png')
    bio = models.TextField(max_length=500, blank=True)

    friends = models.ManyToManyField("self", symmetrical=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Create or update the user profile whenever the User object is saved.
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"

class PrivateChat(models.Model):
    participants = models.ManyToManyField(User, related_name='private_chats')
    # Optionally, you could add a unique_together constraint so that each pair has only one chat.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat between: {', '.join([u.username for u in self.participants.all()])}"


class PrivateMessage(models.Model):
    chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('timestamp',)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"


class Story(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    title = models.CharField(max_length=255)
    content = models.TextField()
    media = models.FileField(upload_to='stories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title