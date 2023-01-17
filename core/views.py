from itertools import chain

from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import random
from core.models import Profile, Post, LikePost, FollowersCount


# Create your views here.
@login_required(login_url="/signin")
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    users_we_follow_list = []
    feed = []

    users_we_follow = FollowersCount.objects.filter(follower=request.user.username)

    for user_we_follow in users_we_follow:
        users_we_follow_list.append(user_we_follow.user)

    for user_we_follow in users_we_follow_list:
        obj_to_app = Post.objects.filter(user=user_we_follow)
        feed.append(obj_to_app)

    posts = list(chain(*feed))  # Post.objects.all()

    # user suggestions
    all_users = User.objects.all()
    user_following_all = []

    for user in users_we_follow:
        user_list = User.objects.get(username=user.user)
        user_following_all.append(user_list)

    new_suggestions_list = [
        user for user in list(all_users)
        if user not in list(user_following_all) and user.username != request.user.username
    ]

    random.shuffle(new_suggestions_list)

    suggested_profiles = []
    user_ids = []

    for user in new_suggestions_list:
        user_ids.append(user.id)

    for ids in user_ids:
        suggested_profiles.append(Profile.objects.filter(id_user=ids))

    suggested_profiles = list(chain(*suggested_profiles))[:4]

    return render(request, "index.html", {"user_profile": user_profile, "posts": posts,
                                          "suggested_profiles": suggested_profiles})


def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, "Email already taken")
                return redirect("signup")
            elif User.objects.filter(username=username).exists():
                messages.info(request, "Username already taken")
                return redirect("signup")
            else:
                user = User.objects.create_user(username, email, password)
                user.save()

                # TODO: login user and direct to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                # create profile object for new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model,
                                                     id_user=user_model.id)
                new_profile.save()
                return redirect("settings")
        else:
            messages.info(request, "Passwords do not match")
            return redirect("signup")  # the url
    else:
        return render(request, "signup.html")


def signin(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect("/")
        else:
            messages.info(request, "Credentials invalid")
            return redirect("signin")
    else:
        return render(request, "signin.html")


@login_required(login_url="/signin")
def logout(request):
    auth.logout(request)
    return redirect("signin")


@login_required(login_url="/signin")
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == "POST":
        # image value depends on if new one was submitted
        image = (
            user_profile.profile_img if request.FILES.get("image") is None
            else request.FILES.get("image")
        )

        bio = request.POST['bio']
        location = request.POST['location']

        user_profile.profile_img = image
        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()

        return redirect("settings")

    return render(request, "setting.html", {"user_profile": user_profile})


@login_required(login_url="/signin")
def upload(request):
    if request.method == "POST":
        user = request.user.username
        image = request.FILES.get("image_upload")
        caption = request.POST['caption']

        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

        return redirect("/")
    else:
        return redirect("/")


@login_required(login_url="/signin")
def like_post(request):
    username = request.user.username
    post_id = request.GET.get("post_id")
    post = Post.objects.get(id=post_id)
    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    if like_filter is None:
        new_like_post = LikePost(post_id=post_id, username=username)
        new_like_post.save()

        post.no_of_likes += 1
        post.save()

        return redirect("/")
    else:
        like_filter.delete()
        post.no_of_likes -= 1
        post.save()

        return redirect("/")


@login_required(login_url="/")
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_posts_length = len(user_posts)

    follower = request.user.username
    user = pk

    button_text = (
        'Unfollow' if FollowersCount.objects.filter(follower=follower, user=user).first()
        else 'Follow'
    )

    follower_count = len(FollowersCount.objects.filter(user=pk))
    following_count = len(FollowersCount.objects.filter(follower=pk))

    context = {
        "user_object": user_object,
        "user_profile": user_profile,
        "user_posts": user_posts,
        "user_posts_length": user_posts_length,
        "button_text": button_text,
        "follower_count": follower_count,
        "following_count": following_count
    }

    return render(request, "profile.html", context)


@login_required(login_url="/")
def follow(request):
    if request.method == "POST":
        follower = request.POST['follower']
        user = request.POST['user']

        if follower == user:
            return

        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()

            return redirect("/profile/" + user)
        else:
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect("/profile/" + user)
    else:
        return redirect("/")


@login_required(login_url="/")
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == "POST":
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains=username)
        username_profiles_ids = []
        username_profiles_list = []

        for users in username_object:
            username_profiles_ids.append(users.id)

        for ids in username_profiles_ids:
            profile_list = Profile.objects.filter(id_user=ids)
            username_profiles_list.append(profile_list)

        username_profiles_list = list(chain(*username_profiles_list))

        return render(request, "search.html", {"user_profile": user_profile,
                                               "username_profiles_list": username_profiles_list}
                      )
    else:
        return redirect("/")
