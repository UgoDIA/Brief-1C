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
    # conn= 'postgresql://postgres:0000@localhost:5432/ETLDB'
    # engine=create_engine(conn)
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
        original=[]
        duppli=[]
        avoirs=[]
        dates=[]
        produits=[]
        quant=[]
        pays=[]
        total=[]
        pourcent=[]
        # delete(monRepertoire)
        for i in range(len(listeFichiers)):
            df = pd.read_csv(urlFichiers[i],encoding = "ISO-8859-1")                            
            original.append(len(df))
            context['original']=original
            df.rename(columns={'InvoiceNo':'noFacture','StockCode':'codeProduit','Description':'nomProduit','InvoiceDate':'dateFacture','Country':'pays'},inplace=True)
            df.drop(['CustomerID','UnitPrice'], inplace=True, axis=1)
            # print('suppr colonne : '+str(df.shape))                        
            df=df.drop_duplicates(['noFacture','codeProduit']) 
            # print('suppr dupli : '+str(df.shape))
            duppli.append(len(df))
            context['duppli']=duppli
            df['noFacture']=pd.to_numeric(df['noFacture'],errors='coerce') 
            df.dropna(subset=['noFacture'], inplace = True)
            # print('suppr avoirs : '+str(df.shape))
            avoirs.append(len(df))
            context['avoirs']=avoirs
            df['dateFacture']=pd.to_datetime(df['dateFacture'], format='%m/%d/%Y %H:%M',errors='coerce')
            df.dropna(subset=['dateFacture'], inplace = True)
            # print('suppr fdate :'+str(df.shape))
            dates.append(len(df))
            context['dates']=dates
            df.loc[(df['codeProduit'].str.len()<=4 )&( df['codeProduit'].str.len()>2) ]=np.nan
            df.loc[df['codeProduit'].str.len()>8 ]=np.nan
            df.dropna(inplace = True)
            # print('suppr codes : '+str(df.shape))
            produits.append(len(df))
            context['produits']=produits
            df=df[(df['Quantity']>0 |(df['Quantity'].isnull()))]
            df.drop(['Quantity'], inplace=True, axis=1)
            # print('suppr qté n :'+str(df.shape))
            quant.append(len(df))
            context['quant']=quant
            df.drop(df[df['pays']== 'Unspecified'].index,inplace=True)
            # print('suppr unsp :'+str(df.shape))
            pays.append(len(df))
            context['pays']=pays
            total.append(len(df))
            context['total']=total
            listePays=df.drop_duplicates('pays').copy()
            listePays.drop(['noFacture','dateFacture','codeProduit','nomProduit','dateFacture'], inplace=True, axis=1)
            P=listePays['pays'].to_list()
            # print('total pays : '+str(len(P)))     
            # for i in range(len(P)):
            #     newPays=Pays(pays=P[i])
            #     newPays.save()
            listeFacture=df.drop_duplicates(subset=['noFacture']).copy()
            # listeFacture.drop(['codeProduit','nomProduit'], inplace=True, axis=1)
            # try: 
            #     listeFacture.to_sql('ventes',engine, if_exists='append',index= False)
            # except:
            #     pass
            # for index, row in listeFacture.iterrows():
            #     newFacture=Ventes(nofacture=row['noFacture'],datefacture=row['dateFacture'],pays=Pays.objects.get(pays=row['pays']))
            #     newFacture.save()
            df.drop(['dateFacture','pays'], inplace=True, axis=1)
            listeProduits=df.drop_duplicates(subset=['codeProduit']).copy()
            listeProduits.drop(['noFacture'], inplace=True, axis=1)
            # for index, row in listeProduits.iterrows():
            #     newProduits=Produits(codeproduit=row['codeProduit'],nomproduit=row['nomProduit'])
            #     newProduits.save()
            df.drop(['nomProduit'], inplace=True, axis=1)
            # for index, row in df.iterrows():
            #     newDetails=Detailsventes(nofacture=Ventes.objects.get(nofacture=row['noFacture']),codeproduit=Produits.objects.get(codeproduit=row['codeProduit']))
            #     newDetails.save()
            # try:
            #     df.to_sql('detailsVentes',engine, if_exists='append',index= False)
            # except:
            #     pass
        sub=np.subtract(original,total)
        pourcent=[k/m for k,m in zip(sub,original)]
        pourcent=[p *100 for p in pourcent]
        pourcent=[round(p,2)for p in pourcent]
        context['sub']=sub
        context['pourcent']=pourcent
        # print(context) 
    return render(request,'uploadCsv.html', context=context)

def save(request):
    monRepertoire='CSV/'
    conn= 'postgresql://postgres:0000@localhost:5432/ETLDB'
    engine=create_engine(conn)
    if request.method =='POST':
        for f in request.FILES.getlist('document'):
                fichierCSV=f
                fs=FileSystemStorage()
                fs.save(fichierCSV.name,fichierCSV)
        listeFichiers=[f for f in listdir(monRepertoire) if isfile(join(monRepertoire,f))]
        urlFichiers=[monRepertoire + f for f in listeFichiers]
        for i in range(len(listeFichiers)):
                df = pd.read_csv(urlFichiers[i],encoding = "ISO-8859-1")                            
                df.rename(columns={'InvoiceNo':'noFacture','StockCode':'codeProduit','Description':'nomProduit','InvoiceDate':'dateFacture','Country':'pays'},inplace=True)
                df.drop(['CustomerID','UnitPrice'], inplace=True, axis=1)
                # print('suppr colonne : '+str(df.shape))                        
                df=df.drop_duplicates(['noFacture','codeProduit']) 
                # print('suppr dupli : '+str(df.shape))
                df['noFacture']=pd.to_numeric(df['noFacture'],errors='coerce') 
                df.dropna(subset=['noFacture'], inplace = True)
                # print('suppr avoirs : '+str(df.shape))
                df['dateFacture']=pd.to_datetime(df['dateFacture'], format='%m/%d/%Y %H:%M',errors='coerce')
                df.dropna(subset=['dateFacture'], inplace = True)
                # print('suppr fdate :'+str(df.shape))
                df.loc[(df['codeProduit'].str.len()<=4 )&( df['codeProduit'].str.len()>2) ]=np.nan
                df.loc[df['codeProduit'].str.len()>8 ]=np.nan
                df.dropna(inplace = True)
                # print('suppr codes : '+str(df.shape))
                df=df[(df['Quantity']>0 |(df['Quantity'].isnull()))]
                df.drop(['Quantity'], inplace=True, axis=1)
                # print('suppr qté n :'+str(df.shape))
                df.drop(df[df['pays']== 'Unspecified'].index,inplace=True)
                # print('suppr unsp :'+str(df.shape))
                listePays=df.drop_duplicates('pays').copy()
                listePays.drop(['noFacture','dateFacture','codeProduit','nomProduit','dateFacture'], inplace=True, axis=1)
                P=listePays['pays'].to_list()
                # print('total pays : '+str(len(P)))     
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
                listeProduits=df.drop_duplicates(subset=['codeProduit']).copy()
                listeProduits.drop(['noFacture'], inplace=True, axis=1)
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
            # print(context) 
    return redirect('visualisation')
    
@login_required(login_url='/ETL/login')    
def menuVisu(request):
    return render(request,'visualisation.html')

@login_required(login_url='/ETL/login')
def accueil(request):
    return render(request,'accueil.html')

@login_required(login_url='/ETL/login')
def graphPays(request):
    return render(request,'graphPays.html')
    
def delete(dossier):
    for root, dirs, files in os.walk(dossier):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))