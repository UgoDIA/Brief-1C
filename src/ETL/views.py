from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.db import connection
from os.path import isfile, join
from django.urls import reverse
import os, shutil, psycopg2
import pandas as pd
import numpy as np
from os import walk,listdir
from os.path import isfile, join
from ETL.models import Pays, Ventes, Detailsventes, Produits, Filtre
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
            df['codeProduit']=df['codeProduit'].str.upper()
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
            df.drop(df[df['nomProduit']== 'mailout'].index,inplace=True)
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
                df['codeProduit']=df['codeProduit'].str.upper()
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
                df.drop(df[df['nomProduit']== 'mailout'].index,inplace=True)
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
                listeProduits['nomProduit']=listeProduits['nomProduit'].str.rstrip()
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
    context={}
    allpays=Pays.objects.values_list(flat=True)
    context['allpays']=allpays
    cursor=connection.cursor()
    if request.method =='POST':
        if request.POST.get("top"):
            Filtre.objects.filter(nfiltre=1).update(filtrepays='top')
            filtre=Filtre.objects.get(nfiltre=1)
            filtred=filtre.filtredate
            filtrep=filtre.filtrepays
            filtretoppays=filtre.filtretoppays
            if filtred=="allD":
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 DESC LIMIT 10''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
            else:       
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s or EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 10''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM "dateFacture")=%(filtred)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,"filtred":filtred})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            pays=df[0].to_list()
            ventes=df[1].to_list()
            context['pays']=pays
            context['ventes']=ventes
            zipp=zip(pays,ventes)
            context['zipp']=zipp
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            return render(request,'graphPays.html',context)
        
        elif request.POST.get("tous"):
            Filtre.objects.filter(nfiltre=1).update(filtrepays='allPa')
            filtre=Filtre.objects.get(nfiltre=1)
            filtred=filtre.filtredate
            filtrep=filtre.filtrepays
            filtretoppays=filtre.filtretoppays
            if filtred=="allD":
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 DESC''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
            else:       
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s or EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM "dateFacture")=%(filtred)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,"filtred":filtred})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            pays=df[0].to_list()
            ventes=df[1].to_list()
            context['pays']=pays
            context['ventes']=ventes
            zipp=zip(pays,ventes)
            context['zipp']=zipp
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            return render(request,'graphPays.html',context)
            
        elif request.POST.get("flop"):
            Filtre.objects.filter(nfiltre=1).update(filtrepays='flop')
            filtre=Filtre.objects.get(nfiltre=1)
            filtred=filtre.filtredate
            filtrep=filtre.filtrepays
            filtretoppays=filtre.filtretoppays
            if filtred=="allD":
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 ASC LIMIT 10''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
            else:       
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s or EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 ASC LIMIT 10''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM "dateFacture")=%(filtred)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,"filtred":filtred})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            pays=df[0].to_list()
            ventes=df[1].to_list()
            context['pays']=pays
            context['ventes']=ventes
            zipp=zip(pays,ventes)
            context['zipp']=zipp
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            return render(request,'graphPays.html',context)
        
        elif request.POST.get("allDate"):
            Filtre.objects.filter(nfiltre=1).update(filtredate='allD')  
            filtre=Filtre.objects.get(nfiltre=1)
            filtrep=filtre.filtrepays
            filtred=filtre.filtredate
            filtretoppays=filtre.filtretoppays
            if filtrep=="top":
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 DESC LIMIT 10''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       

            elif filtrep=="allPa":
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 DESC''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       

            else:
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 ASC LIMIT 10''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            pays=df[0].to_list()
            ventes=df[1].to_list()
            context['pays']=pays
            context['ventes']=ventes
            zipp=zip(pays,ventes)
            context['zipp']=zipp
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            return render(request,'graphPays.html',context)
        
        elif request.POST.get("2010"):
            Filtre.objects.filter(nfiltre=1).update(filtredate='2010')
            filtre=Filtre.objects.get(nfiltre=1)
            filtrep=filtre.filtrepays
            filtred=filtre.filtredate
            filtretoppays=filtre.filtretoppays
            if filtrep=="top":
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=2010 GROUP BY pays ORDER BY 2 DESC LIMIT 10''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM ventes."dateFacture")=2010 GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
            elif filtrep=="allPa":
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=2010 GROUP BY pays ORDER BY 2 DESC''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM ventes."dateFacture")=2010 GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
            else:
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=2010 GROUP BY pays ORDER BY 2 ASC LIMIT 10''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM ventes."dateFacture")=2010 GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            pays=df[0].to_list()
            ventes=df[1].to_list()
            context['pays']=pays
            context['ventes']=ventes
            zipp=zip(pays,ventes)
            context['zipp']=zipp
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtre']=filtre
            context['filtrep']=filtrep
            return render(request,'graphPays.html',context)
        
        elif request.POST.get("2011"):
            Filtre.objects.filter(nfiltre=1).update(filtredate='2011')
            filtre=Filtre.objects.get(nfiltre=1)
            filtrep=filtre.filtrepays
            filtred=filtre.filtredate
            filtretoppays=filtre.filtretoppays
            if filtrep=="top":
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=2011 GROUP BY pays ORDER BY 2 DESC LIMIT 10''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM ventes."dateFacture")=2011 GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       

            elif filtrep=="allPa":
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=2011 GROUP BY pays ORDER BY 2 DESC''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM ventes."dateFacture")=2011 GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
            else:
                cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=2011 GROUP BY pays ORDER BY 2 ASC LIMIT 10''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM ventes."dateFacture")=2011 GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
            prod=cursor.fetchall()
            pf=pd.DataFrame(prod)
            df=pd.DataFrame(q)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            pays=df[0].to_list()
            ventes=df[1].to_list()
            context['pays']=pays
            context['ventes']=ventes
            zipp=zip(pays,ventes)
            context['zipp']=zipp
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            return render(request,'graphPays.html',context)
        elif request.POST.get("filtretop"):
            y=request.POST['filtretop']
            Filtre.objects.filter(nfiltre=1).update(filtretoppays=y)
            filtre=Filtre.objects.get(nfiltre=1)
            filtretoppays=filtre.filtretoppays
            filtrep=filtre.filtrepays
            filtred=filtre.filtredate
            if filtrep=="top":
                if filtred=="allD":
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 DESC LIMIT 10''')
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
                else:       
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s or EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 10''',{"filtred":filtred})
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM "dateFacture")=%(filtred)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,"filtred":filtred})       
            elif filtrep=="allPa":
                if filtred=="allD":
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 DESC''')
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
                else:       
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s or EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC''',{"filtred":filtred})
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM "dateFacture")=%(filtred)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,"filtred":filtred})       
            elif filtrep=="flop":
                if filtred=="allD":
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 ASC LIMIT 10''')
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
                else:       
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s or EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 ASC LIMIT 10''',{"filtred":filtred})
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM "dateFacture")=%(filtred)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,"filtred":filtred})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            pays=df[0].to_list()
            ventes=df[1].to_list()
            context['pays']=pays
            context['ventes']=ventes
            zipp=zip(pays,ventes)
            context['zipp']=zipp
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            return render(request,'graphPays.html',context)
    else:
        filtre=Filtre.objects.get(nfiltre=1)
        filtretoppays=filtre.filtretoppays
        filtrep=filtre.filtrepays
        filtred=filtre.filtredate
        if filtrep=="top":
                if filtred=="allD":
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 DESC LIMIT 10''')
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
                else:       
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s or EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 10''',{"filtred":filtred})
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM "dateFacture")=%(filtred)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,"filtred":filtred})       
        elif filtrep=="allPa":
                if filtred=="allD":
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 DESC''')
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
                else:       
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s or EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC''',{"filtred":filtred})
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM "dateFacture")=%(filtred)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,"filtred":filtred})       
        elif filtrep=="flop":
                if filtred=="allD":
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 ASC LIMIT 10''')
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,})       
                else:       
                    cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s or EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 ASC LIMIT 10''',{"filtred":filtred})
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT "nomProduit",count(*) FROM produits INNER JOIN "detailsVentes" ON produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture" = ventes."noFacture" Where pays = %(filtretoppays)s AND EXTRACT(YEAR FROM "dateFacture")=%(filtred)s GROUP BY "nomProduit" ORDER BY 2 DESC LIMIT 5 ''',{"filtretoppays":filtretoppays,"filtred":filtred})       
        prod=cursor.fetchall()
        df=pd.DataFrame(q)
        pf=pd.DataFrame(prod)
        topprod=pf[0].to_list()
        prodvente=pf[1].to_list()
        pays=df[0].to_list()
        ventes=df[1].to_list()
        context['pays']=pays
        context['ventes']=ventes
        zipp=zip(pays,ventes)
        context['zipp']=zipp
        context['topprod']=topprod
        context['prodvente']=prodvente
        context['filtred']=filtred
        context['filtrep']=filtrep
        context['filtre']=filtre
        return render(request,'graphPays.html',context)
        
    return render(request,'graphPays.html',context)

def filtrePays(request,pays):
    Filtre.objects.filter(nfiltre=1).update(filtretoppays=pays)
    return HttpResponseRedirect(reverse('graphPays'))

def filtreProduits(request,produits):
    prod=Produits.objects.get(nomproduit=produits)
    Filtre.objects.filter(nfiltre=1).update(filtreproduits=prod.codeproduit)
    return HttpResponseRedirect(reverse('graphProduits'))

@login_required(login_url='/ETL/login')
def graphProduits(request):
    context={}
    allproduits=Produits.objects.values_list(flat=True)
    context['allproduits']=allproduits
    cursor=connection.cursor()
    if request.method =='POST':
        if request.POST.get("top"):
            Filtre.objects.filter(nfiltre=1).update(filtrepays='top')
            filtre=Filtre.objects.get(nfiltre=1)
            filtred=filtre.filtredate
            filtrep=filtre.filtrepays
            filtreproduits=filtre.filtreproduits
            filtretoppays=filtre.filtretoppays
            if filtred=="allD":
                cursor.execute(f'''SELECT  produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" GROUP BY  produits."codeProduit", "nomProduit" ORDER BY 3 DESC LIMIT 10 ''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit"  = %(filtreproduits)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,})       
            else:       
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC LIMIT 10''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit"  = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            codeprod=df[0].to_list()
            pays=df[1].to_list()
            ventes=df[2].to_list()
            filtreselected=Produits.objects.get(codeproduit=filtreproduits)
            filtreselected=filtreselected.nomproduit
            context['pays']=pays
            context['ventes']=ventes
            zipp=zip(pays,ventes)
            zipprod=zip(codeprod,pays)
            context['zipprod']=zipprod
            context['zipp']=zipp
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            context['filtreselected']=filtreselected
            return render(request,'graphProduits.html',context)
        
        elif request.POST.get("tous"):
            Filtre.objects.filter(nfiltre=1).update(filtrepays='allPa')
            filtre=Filtre.objects.get(nfiltre=1)
            filtred=filtre.filtredate
            filtrep=filtre.filtrepays
            filtreproduits=filtre.filtreproduits
            filtretoppays=filtre.filtretoppays
            if filtred=="allD":
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,})       
            else:       
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 2 DESC''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            codeprod=df[0].to_list()
            pays=df[1].to_list()
            ventes=df[2].to_list()
            filtreselected=Produits.objects.get(codeproduit=filtreproduits)
            filtreselected=filtreselected.nomproduit
            context['pays']=pays
            context['ventes']=ventes
            zipp=zip(pays,ventes)
            zipprod=zip(codeprod,pays)
            context['zipp']=zipp
            context['zipprod']=zipprod
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            context['filtreselected']=filtreselected

            return render(request,'graphProduits.html',context)
            
        elif request.POST.get("flop"):
            Filtre.objects.filter(nfiltre=1).update(filtrepays='flop')
            filtre=Filtre.objects.get(nfiltre=1)
            filtred=filtre.filtredate
            filtrep=filtre.filtrepays
            filtreproduits=filtre.filtreproduits
            filtretoppays=filtre.filtretoppays
            if filtred=="allD":
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 ASC LIMIT 10 ''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,})       
            else:       
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 ASC LIMIT 10''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            codeprod=df[0].to_list()
            pays=df[1].to_list()
            ventes=df[2].to_list()
            filtreselected=Produits.objects.get(codeproduit=filtreproduits)
            filtreselected=filtreselected.nomproduit
            context['pays']=pays
            context['ventes']=ventes
            zipprod=zip(codeprod,pays)
            zipp=zip(pays,ventes)
            context['zipp']=zipp
            context['zipprod']=zipprod
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            context['filtreselected']=filtreselected
            return render(request,'graphProduits.html',context)
        
        elif request.POST.get("allDate"):
            Filtre.objects.filter(nfiltre=1).update(filtredate='allD')  
            filtre=Filtre.objects.get(nfiltre=1)
            filtrep=filtre.filtrepays
            filtred=filtre.filtredate
            filtreproduits=filtre.filtreproduits
            filtretoppays=filtre.filtretoppays
            if filtrep=="top":
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC LIMIT 10 ''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,})       

            elif filtrep=="allPa":
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,})       

            else:
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 ASC LIMIT 10 ''')
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            filtreselected=Produits.objects.get(codeproduit=filtreproduits)
            filtreselected=filtreselected.nomproduit
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            codeprod=df[0].to_list()
            pays=df[1].to_list()
            ventes=df[2].to_list()
            context['pays']=pays
            context['ventes']=ventes
            zipprod=zip(codeprod,pays)
            zipp=zip(pays,ventes)
            context['zipp']=zipp
            context['zipprod']=zipprod
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            context['filtreselected']=filtreselected
            return render(request,'graphProduits.html',context)
        
        elif request.POST.get("2010"):
            Filtre.objects.filter(nfiltre=1).update(filtredate='2010')
            filtre=Filtre.objects.get(nfiltre=1)
            filtrep=filtre.filtrepays
            filtred=filtre.filtredate
            filtreproduits=filtre.filtreproduits
            filtretoppays=filtre.filtretoppays
            if filtrep=="top":
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC LIMIT 10''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       
            elif filtrep=="allPa":
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       
            else:
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 ASC LIMIT 10''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            filtreselected=Produits.objects.get(codeproduit=filtreproduits)
            filtreselected=filtreselected.nomproduit
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            codeprod=df[0].to_list()
            pays=df[1].to_list()
            ventes=df[2].to_list()
            context['pays']=pays
            context['ventes']=ventes
            zipprod=zip(codeprod,pays)
            zipp=zip(pays,ventes)
            context['zipp']=zipp
            context['zipprod']=zipprod
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtre']=filtre
            context['filtrep']=filtrep
            context['filtreselected']=filtreselected
            return render(request,'graphProduits.html',context)
        
        elif request.POST.get("2011"):
            Filtre.objects.filter(nfiltre=1).update(filtredate='2011')
            filtre=Filtre.objects.get(nfiltre=1)
            filtrep=filtre.filtrepays
            filtred=filtre.filtredate
            filtreproduits=filtre.filtreproduits
            filtretoppays=filtre.filtretoppays
            if filtrep=="top":
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC LIMIT 10''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       

            elif filtrep=="allPa":
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       
            else:
                cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 ASC LIMIT 10''',{"filtred":filtred})
                q=cursor.fetchall()
                cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       
            prod=cursor.fetchall()
            pf=pd.DataFrame(prod)
            df=pd.DataFrame(q)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            filtreselected=Produits.objects.get(codeproduit=filtreproduits)
            filtreselected=filtreselected.nomproduit
            codeprod=df[0].to_list()
            pays=df[1].to_list()
            ventes=df[2].to_list()
            context['pays']=pays
            context['ventes']=ventes
            zipprod=zip(codeprod,pays)
            zipp=zip(pays,ventes)
            context['zipprod']=zipprod
            context['zipp']=zipp
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            context['filtreselected']=filtreselected
            return render(request,'graphProduits.html',context)
        elif request.POST.get("filtretop"):
            y=request.POST['filtretop']
            Filtre.objects.filter(nfiltre=1).update(filtreproduits=y)
            filtre=Filtre.objects.get(nfiltre=1)
            filtrep=filtre.filtrepays
            filtred=filtre.filtredate
            filtreproduits=filtre.filtreproduits
            if filtrep=="top":
                if filtred=="allD":
                    cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC LIMIT 10 ''')
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,})
                else:       
                    cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC LIMIT 10''',{"filtred":filtred})
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       
            elif filtrep=="allPa":
                if filtred=="allD":
                    cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC''')
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,})       
                else:       
                    cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC''',{"filtred":filtred})
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       
            else:
                if filtred=="allD":
                    cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 ASC LIMIT 10 ''')
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,})       
                else:       
                    cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" INNER JOIN ventes ON "detailsVentes"."noFacture"=ventes."noFacture" WHERE EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 ASC LIMIT 10''',{"filtred":filtred})
                    q=cursor.fetchall()
                    cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" WHERE produits."codeProduit" = %(filtreproduits)s AND EXTRACT(YEAR FROM ventes."dateFacture")=%(filtred)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,"filtred":filtred})       
            prod=cursor.fetchall()
            df=pd.DataFrame(q)
            pf=pd.DataFrame(prod)
            filtreselected=Produits.objects.get(codeproduit=filtreproduits)
            filtrecode=filtreselected.codeproduit
            filtreselected=filtreselected.nomproduit
            print(filtrecode)
            topprod=pf[0].to_list()
            prodvente=pf[1].to_list()
            codeprod=df[0].to_list()
            pays=df[1].to_list()
            ventes=df[2].to_list()
            context['pays']=pays
            context['ventes']=ventes
            zipprod=zip(codeprod,pays)
            zipp=zip(pays,ventes)
            context['zipprod']=zipprod
            context['zipp']=zipp
            context['topprod']=topprod
            context['prodvente']=prodvente
            context['filtred']=filtred
            context['filtrep']=filtrep
            context['filtre']=filtre
            context['filtrecode']=filtrecode
            context['filtreselected']=filtreselected
            return render(request,'graphProduits.html',context)
    else:
        Filtre.objects.filter(nfiltre=1).update(filtrepays='top')
        Filtre.objects.filter(nfiltre=1).update(filtredate='allD')
        filtre=Filtre.objects.get(nfiltre=1)
        filtrep=filtre.filtrepays
        filtreproduits=filtre.filtreproduits
        filtred=filtre.filtredate    
        filtretoppays=filtre.filtretoppays
        cursor.execute(f'''SELECT produits."codeProduit", "nomProduit", COUNT(*) FROM produits INNER JOIN "detailsVentes" on produits."codeProduit" = "detailsVentes"."codeProduit" GROUP BY produits."codeProduit", "nomProduit" ORDER BY 3 DESC LIMIT 10 ''')       
        q=cursor.fetchall()
        cursor.execute(f'''SELECT pays,count(*) FROM ventes INNER JOIN "detailsVentes" ON ventes."noFacture"="detailsVentes"."noFacture" INNER JOIN produits ON "detailsVentes"."codeProduit" = produits."codeProduit" Where produits."codeProduit" = %(filtreproduits)s GROUP BY pays ORDER BY 2 DESC LIMIT 5''',{"filtreproduits":filtreproduits,})       
        prod=cursor.fetchall()
        df=pd.DataFrame(q)
        pf=pd.DataFrame(prod)
        topprod=pf[0].to_list()
        prodvente=pf[1].to_list()
        filtreselected=Produits.objects.get(codeproduit=filtreproduits)
        filtreselected=filtreselected.nomproduit
        # topprod=[i[0] for i in prod]
        # prodvente=[i[1] for i in prod]
        codeprod=df[0].to_list()
        pays=df[1].to_list()
        ventes=df[2].to_list()
        context['filtre']=filtre
        context['pays']=pays
        context['ventes']=ventes
        context['topprod']=topprod
        context['prodvente']=prodvente
        zipprod=zip(codeprod,pays)
        zipp=zip(pays,ventes)
        context['zipp']=zipp
        context['zipprod']=zipprod
        context['filtred']=filtred
        context['filtrep']=filtrep
        context['filtreproduits']=filtreproduits
        context['filtreselected']=filtreselected
        return render(request,'graphProduits.html',context)
        
    return render(request,'graphProduits.html',context)
    
def delete(dossier):
    for root, dirs, files in os.walk(dossier):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
            
            
            







#  if request.POST.get("ukCheck"):
#             ukCheck=request.POST['ukCheck']
#             uk=ukCheck
#             cursor.execute(f'''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 DESC OFFSET %(uk)s ROWS LIMIT 10''',{"uk":uk,})
#             q=cursor.fetchall()
#             df=pd.DataFrame(q)
#             pays=df[0].to_list()
#             ventes=df[1].to_list()
#             context['pays']=pays
#             context['ventes']=ventes
#             context['check']=uk
#             print(uk)



# if request.method =='POST':
#             if request.POST.get("allDate"):
#                 cursor.execute('''SELECT pays, COUNT(pays) FROM ventes INNER JOIN "detailsVentes" on ventes."noFacture" = "detailsVentes"."noFacture" GROUP BY pays ORDER BY 2 DESC LIMIT 10''')
#                 q=cursor.fetchall()
#                 df=pd.DataFrame(q)
#                 pays=df[0].to_list()
#                 ventes=df[1].to_list()
#                 context['pays']=pays
#                 context['ventes']=ventes
#                 zipp=zip(pays,ventes)
#                 context['zipp']=zipp
#         return render(request,'graphPays.html',context)