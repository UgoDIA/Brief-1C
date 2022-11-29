from http.client import HTTPResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.template import loader

# Create your views here.

def login(request):
    if request.method == "POST":
        identifiant = request.POST['identifiant']
        password = request.POST['password']
        user = authenticate(request, identifiant=identifiant, password=password)
        if user is not None:
            login(request, user)
            return redirect('login')
        else:
            messages.success(request, ("Erreur de matricule ou de mot de passe, veuillez ressayer"))
            return redirect('login')
    else:
        return render(request, 'login.html', {})


# def logout_user(request):
#     logout(request)
#     messages.success(request, ("Session deconnectée"))
#     return redirect('login')