from http.client import HTTPResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.template import loader
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# Create your views here.


def loginq(request):
    if request.method == "POST":
        username = request.POST['identifiant']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('accueil')
        else:
            messages.success(request, ("Mauvais identifiant ou mot de passe, veuillez ressayer."))
            return redirect('login')
    else:
        return render(request, 'login.html')


def logoutq(request):
    logout(request)
    messages.success(request, ("Session deconnectée"))
    return redirect('login')