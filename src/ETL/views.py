from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from os.path import isfile, join
from django.urls import reverse
import os, shutil, psycopg2
import pandas as pd
import numpy as np
from os import walk,listdir
from os.path import isfile, join
from ETL.models import Pays, Ventes, Detailsventes, Produits
from sqlalchemy import create_engine

def index(request):
    return redirect('login')

@login_required(login_url='/ETL/login')
def uploadCsv(request):
    monRepertoire='CSV/'
    conn= 'postgresql://postgres:0000@localhost:5432/ETLDB'
    engine=create_engine(conn)
    context ={}
    # pd.set_option('display.max_rows', None)
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
        df = pd.read_csv(urlFichiers[0],encoding = "ISO-8859-1")                             
        print('original : '+str(df.shape))
        df.rename(columns={'InvoiceNo':'noFacture','StockCode':'codeProduit','Description':'nomProduit','InvoiceDate':'dateFacture','Country':'pays'},inplace=True)
        df.drop(['CustomerID','UnitPrice'], inplace=True, axis=1)
        print('suppr colonne : '+str(df.shape))                        
        df=df.drop_duplicates(['noFacture','codeProduit']) 
        print('suppr dupli : '+str(df.shape)) 
        df['noFacture']=pd.to_numeric(df['noFacture'],errors='coerce') 
        df.dropna(subset=['noFacture'], inplace = True)
        print('suppr avoirs : '+str(df.shape))
        df['dateFacture']=pd.to_datetime(df['dateFacture'], format='%m/%d/%Y %H:%M',errors='coerce')
        df.dropna(subset=['dateFacture'], inplace = True)
        print('suppr fdate :'+str(df.shape))
        df.loc[(df['codeProduit'].str.len()<=4 )&( df['codeProduit'].str.len()>2) ]=np.nan
        df.loc[df['codeProduit'].str.len()>8 ]=np.nan
        df.dropna(inplace = True)
        print('suppr codes : '+str(df.shape))
        df=df[(df['Quantity']>0 |(df['Quantity'].isnull()))]
        df.drop(['Quantity'], inplace=True, axis=1)
        print('suppr qté n :'+str(df.shape))
        df.drop(df[df['pays']== 'Unspecified'].index,inplace=True)
        print('suppr unsp :'+str(df.shape))
        listePays=df.drop_duplicates('pays').copy()
        # listePays.drop(['noFacture','dateFacture','codeProduit','nomProduit','dateFacture'], inplace=True, axis=1)
        # listePays.to_sql('pays',engine, if_exists='append',index= False)
        P=listePays['pays'].to_list()
        print('total pays : '+str(len(P)))     
        for i in range(len(P)):
            newPays=Pays(pays=P[i])
            newPays.save()
        listeFacture=df.drop_duplicates(subset=['noFacture']).copy()
        listeFacture.drop(['codeProduit','nomProduit'], inplace=True, axis=1)
        try:  
            listeFacture.to_sql('ventes',engine, if_exists='append',index= False)
        except:
            pass    
        # for index, row in listeFacture.iterrows():
        #     newFacture=Ventes(nofacture=row['noFacture'],datefacture=row['dateFacture'],pays=Pays.objects.get(pays=row['pays']))
        #     newFacture.save()
        df.drop(['dateFacture','pays'], inplace=True, axis=1)   
        listeProduits=df.drop_duplicates(subset=['codeProduit'])
        for index, row in listeProduits.iterrows():
            newProduits=Produits(codeproduit=row['codeProduit'],nomproduit=row['nomProduit'])
            newProduits.save()
        df.drop(['nomProduit'], inplace=True, axis=1) 
        # for index, row in df.iterrows():
        #     newDetails=Detailsventes(nofacture=Ventes.objects.get(nofacture=row['noFacture']),codeproduit=Produits.objects.get(codeproduit=row['codeProduit']))
        #     newDetails.save()
        
        try:
            df.to_sql('detailsVentes',engine, if_exists='append',index= False)
        except:
            pass
    return render(request,'uploadCsv.html', context)

def delete(dossier):
    for root, dirs, files in os.walk(dossier):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))