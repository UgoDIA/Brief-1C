"""ETL URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from ETL.views import index
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',index, name="index"),
    path('ETL/', include('identification.urls')),
    path('ETL/upload/',views.uploadCsv, name='upload'),
    path('ETL/save/',views.save, name='save'),
    path('ETL/visualisation/',views.menuVisu, name='visualisation'),
    path('ETL/accueil/',views.accueil, name='accueil'),
    path('ETL/visualisation/pays',views.graphPays, name='graphPays'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)