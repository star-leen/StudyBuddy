from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Room, Topic, Message
from .forms import RoomForm, UserForm
# from django.http import HttpResponse

# Create your views here.

# rooms = [
#     {'id':1, 'name':'Let\'s Learn Python!'},
#     {'id':2, 'name':'Figma!'},
#     {'id':3, 'name':'Frontend'},
# ]

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
        )
    topics = Topic.objects.all()[0:4]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    context = {'rooms':rooms, 'topics': topics, 'room_count':room_count, 'room_messages':room_messages}
    return render(request, 'base/home.html', context)

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')
            
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request, 'Username or Password is not correct')
        
    context = {'page':page}
    return render(request, 'base/login.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    page = 'register'
    form = UserCreationForm()
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registeration')
    
    context = {'page':page, 'form':form}
    return render(request, 'base/register.html', context)

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    members = room.members.all()
    
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body'),
        )
        room.members.add(request.user)
        return redirect('room', pk=room.id)
    
    context = {'room':room, 'room_messages': room_messages, 'members':members}
    return render(request, 'base/room.html', context)

def topics(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(
        Q(name__icontains=q)
        )
    context = {'topics':topics}
    return render(request, 'base/topics.html', context)

def activity(request):
    room_messages = Message.objects.all()
    context = {'room_messages':room_messages}
    return render(request, 'base/activity.html', context)

def userProfile(request, pk):
    user_profile = User.objects.get(id=pk)
    rooms = user_profile.room_set.all()
    room_messages = user_profile.message_set.all()
    topics = Topic.objects.all()[0:4]
    context = {'user_profile':user_profile, 'rooms':rooms, 'room_messages':room_messages, 'topics':topics}
    return render(request, 'base/profile.html', context)

@login_required(login_url='login')
def createRoom(request):
    page_type = 'create'
    topics = Topic.objects.all()
    form = RoomForm()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        
        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description')
        )          
        return redirect('home')
    context = {'form': form, 'page_type': page_type, 'topics':topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    page_type = 'update'
    topics = Topic.objects.all()
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    if request.user != room.host:
        return HttpResponse('You are not allowed to do this')
        
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
    
    context = {'form': form, 'page_type':page_type, 'topics':topics, 'room':room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    subject = 'room'
    room = Room.objects.get(id=pk)
    
    if request.user != room.host:
        return HttpResponse('You are not allowed to do this')
    
    if request.method =='POST':
        room.delete()
        return redirect('home')
    context = {'obj': room, 'subject':subject}
    return render(request, 'base/delete.html', context)

@login_required(login_url='login')
def deleteMessage(request, pk):
    subject = 'message'
    message = Message.objects.get(id=pk)
    room_id = message.room.id
    
    if request.user != message.user:
        return HttpResponse('You are not allowed to do this')
    
    if request.method =='POST':
        message.delete()
        return redirect('room', room_id)
    context = {'obj': message, 'subject':subject}
    return render(request, 'base/delete.html', context)

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    context = {'form':form}
    return render(request, 'base/update-user.html', context)