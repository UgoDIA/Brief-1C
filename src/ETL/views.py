from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from os.path import isfile, join
from django.urls import reverse
import os, shutil
import pandas as pd
import numpy as np
from os import walk,listdir
from os.path import isfile, join
from ETL.models import Pays, Ventes, Detailsventes, Produits

def index(request):
    return redirect('login')

@login_required(login_url='/ETL/login')
def uploadCsv(request):
    monRepertoire='CSV/'
    context ={}
    delete(monRepertoire)
    if request.method =='POST':
        for f in request.FILES.getlist('document'):
            fichierCSV=f
            fs=FileSystemStorage()
            fs.save(fichierCSV.name,fichierCSV)
        listeFichiers=[f for f in listdir(monRepertoire) if isfile(join(monRepertoire,f))]
        urlFichiers=[monRepertoire + f for f in listeFichiers]
        context['noms']=listeFichiers
        # delete(monRepertoire)
        df = pd.read_csv(urlFichiers[0],encoding = "ISO-8859-1")                              #(245903, 8)
        print('original : '+str(df.shape))
        df.drop(['CustomerID','UnitPrice'], inplace=True, axis=1)
        print('suppr colonne : '+str(df.shape))                        
        df=df.drop_duplicates(['InvoiceNo','StockCode']) 
        print('suppr dupli : '+str(df.shape)) 
        df['InvoiceNo']=pd.to_numeric(df['InvoiceNo'],errors='coerce') 
        df.dropna(subset=['InvoiceNo'], inplace = True)
        print('suppr avoirs : '+str(df.shape))
        df['InvoiceDate']=pd.to_datetime(df['InvoiceDate'], format='%m/%d/%Y %H:%M',errors='coerce')
        df.dropna(subset=['InvoiceDate'], inplace = True)
        print('suppr fdate :'+str(df.shape))
        df.loc[(df['StockCode'].str.len()<=4 )&( df['StockCode'].str.len()>2) ]=np.nan
        df.loc[df['StockCode'].str.len()>8 ]=np.nan
        df.dropna(subset=['StockCode'], inplace = True)
        print('suppr codes : '+str(df.shape))
        df=df[(df['Quantity']>0 |(df['Quantity'].isnull()))]
        print('suppr qté n :'+str(df.shape))
        df.drop(df[df['Country']== 'Unspecified'].index,inplace=True)
        print('suppr unsp :'+str(df.shape))
        listePays=df.drop_duplicates('Country')
        P=listePays['Country'].to_list()
        print('total pays : '+str(len(P)))
        listeFacture=df.drop_duplicates(subset=['InvoiceNo','InvoiceDate'])
        listeFacture.to_sql('ventes', if_exists='replace')
        
        for i in range(len(P)):
            newPays=Pays(pays=P[i])
            newPays.save()
    return render(request,'uploadCsv.html', context)

def delete(dossier):
    for root, dirs, files in os.walk(dossier):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))