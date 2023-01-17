import django.utils.timezone
from django.db import models
from django.contrib.auth import get_user_model
import uuid

# Create your models here.

User = get_user_model()


# this creates a database entry
# <app-name>_<model-name>, here: core-profile
class Profile(models.Model):
    # this is our users id
    id_user = models.IntegerField()
    bio = models.TextField(blank=True)
    profile_img = models.ImageField(upload_to="profile_images", default="blank_profile_picture.png")
    location = models.CharField(max_length=100, blank=True)

    # this is the user_id of a user we follow, if the followed user
    # gets deleted, delete the entries on all followers
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.CharField(max_length=100)
    image = models.ImageField(upload_to="post_images")
    caption = models.TextField()
    created_at = models.DateTimeField(default=django.utils.timezone.now)
    no_of_likes = models.IntegerField(default=0)

    def __str__(self):
        return self.user


class LikePost(models.Model):
    post_id = models.CharField(max_length=500)
    username = models.CharField(max_length=100)

    def __str__(self):
        return self.username


class FollowersCount(models.Model):
    follower = models.CharField(max_length=100)
    user = models.CharField(max_length=100)

    def __str__(self):
        return self.user