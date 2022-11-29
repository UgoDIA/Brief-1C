from http.client import HTTPResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.template import loader

# Create your views here.

def login(request):
    return render(request, 'login.html', {})


# def logout_user(request):
#     logout(request)
#     messages.success(request, ("Session deconnectée"))
#     return redirect('login')