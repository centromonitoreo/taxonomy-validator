# -*- coding: utf-8 -*-
"""
Created on Tue Aug 29 10:32:20 2023

@author: diego
"""

import pandas as pd 
import numpy as np 
from fuzzywuzzy import fuzz
from multiprocess import Pool
import multiprocessing
from lib_taxonomia.limpieza import limpiar_data, ajustar_genero
import os
import subprocess
import tkinter as tk

def rev_taxonomia(argumentos):
    import pygbif
    import numpy as np
    import requests
    import datetime
    import time
    from fuzzywuzzy import fuzz

    
    def probar_conexion():
        time_inicio = datetime.datetime.today()
        while (1 == 1):
            try:
                request = requests.get("http://www.google.com", timeout=5)
                return True
            except (requests.ConnectionError, requests.Timeout):
                print("Sin conexión a internet.")
                timepo_step = datetime.datetime.today()
                tiempo_paso = (timepo_step - time_inicio).seconds
                time.sleep(5)
        return False

   
    def evaluar_alternativa(alternativa, dict_taxonomia):
      #  print(alternativa)
        lista_nombres_definitivos = {'class':'CLASE', 'order':'ORDEN', 'family':'FAMILIA', 'genus':'GENERO','species':'ESPECIE'}
        dict_evaluacion = {}
        for taxonomia, _ in lista_nombres_definitivos.items():
            
            nombre = alternativa.get(taxonomia, None)
   
            correlacion_max = 0
            taxon_relacion = ''
            nombre_sugerido =  ''
            if not nombre is None:
                for taxon_usuario, nombre_usuario  in dict_taxonomia.items():
                    nombre_usuario = nombre_usuario if isinstance(nombre_usuario, str) else "No aplica"
                    correlacion = fuzz.ratio(nombre_usuario.lower(), nombre.lower())
                    if correlacion > correlacion_max:
                        correlacion_max = correlacion
                        taxon_relacion = taxon_usuario
                dict_evaluacion[taxonomia] = {'correlacion_max':correlacion_max, 'taxon_relacion':taxon_relacion, 'nombre_sugerido':nombre}
            else:        
                dict_evaluacion[taxonomia] = {'correlacion_max':0, 'taxon_relacion':"error", 'nombre_sugerido':nombre}
        dict_evaluacion['Alternativa'] = alternativa

        return dict_evaluacion


    def gbif_rev(taxonomia, nivel_taxonomia, dict_taxonomia):

        dict_permitidos = {'order':['order', 'family'], 'family':['genus', 'family', 'order'], 'genus':['genus', 'family'],'species':['species']}
        print('NIVEL TAXONOMIA--------->', nivel_taxonomia)
        list_alternativas = []
        probar_conexion()
        print('La consulta se esta ejecutando')
        species_busqueda = pygbif.species.name_backbone(name =taxonomia, verbose =True)
       # print(species_busqueda)
       # print(taxonomia, species_busqueda)
        if not species_busqueda['matchType']=='NONE' or 'alternatives' in list(species_busqueda.keys()):
            alternativas =  species_busqueda.get('alternatives', None)
            if not alternativas is None:
                for alternativa in alternativas:
                    print('--------------------ALTERNATIVA---------------------------------')
                    if alternativa['rank'].lower() in dict_permitidos[nivel_taxonomia]:
                     #   print(alternativa['rank'])
                        dict_alternativa = evaluar_alternativa(alternativa, dict_taxonomia)
                        list_alternativas.append(dict_alternativa)
                        print('--------------------evalaucion---------------------------------')

                if species_busqueda.get('rank', '').lower() in dict_permitidos[nivel_taxonomia]:      
                    dict_alternativa = evaluar_alternativa(species_busqueda, dict_taxonomia)
                    list_alternativas.append(dict_alternativa)
                    
            else:
                if species_busqueda.get('rank', '').lower() in dict_permitidos[nivel_taxonomia]:  
                    dict_alternativa = evaluar_alternativa(species_busqueda, dict_taxonomia)
                    list_alternativas.append(dict_alternativa)
       # print(list_alternativas)
        return list_alternativas


    def calificar_alternativa(alternativa, dict_taxonomia):

        taxon_menor = None
        taxon_mayor = None
        for taxon, valor_taxon in dict_taxonomia.items():
            if not pd.isna(valor_taxon):
                if taxon_menor is None:
                    taxon_menor = taxon
                else:
                    taxon_mayor = taxon

        dict_pesos = {}
        for taxon, _ in dict_taxonomia.items():
            dict_pesos[taxon] = 3 if taxon in [taxon_menor, taxon_mayor] else 1

        suma_alternativa = 0

        promedio_alternativa = []
        for taxonomia, valor in alternativa.items():
            if  taxonomia in dict_pesos.keys():
                if (taxonomia != 'Alternativa')&(valor is not None):
                    #print(valor, dict_pesos[taxonomia])
                    suma_alternativa += valor['correlacion_max']*dict_pesos[taxonomia]
                #    promedio_alternativa.append(valor['correlacion_max'])
                #   if valor['correlacion_max']>0:
                #      suma_alternativa += valor['correlacion_max']
        suma_alternativa = suma_alternativa/sum(list(dict_pesos.values()))
        return suma_alternativa
                
    

    def seleccionar_mejor_alternativa(dict_result, dict_taxonomia):
        puntaje_mejor_alternativa = 0
        coor = 0
        mejor_alternativa = {}
        #print(dict_result)
        for _, alternativas_taxon in dict_result.items():
            for alternativa_taxon in alternativas_taxon:
                if calificar_alternativa(alternativa_taxon, dict_taxonomia)>puntaje_mejor_alternativa:
                    puntaje_mejor_alternativa = calificar_alternativa(alternativa_taxon, dict_taxonomia)
                    mejor_alternativa = alternativa_taxon
        return mejor_alternativa, puntaje_mejor_alternativa

    try:
        key_fila, dict_taxonomia= argumentos
        #print('Inicio Consulta', key_fila)
        dict_result = {}
        #print(dict_taxonomia)
        for nivel_taxonomia, taxonomia in dict_taxonomia.items():
        
            dict_result[nivel_taxonomia] =  gbif_rev(taxonomia, nivel_taxonomia, dict_taxonomia)
        mejor_alternativa, coor = seleccionar_mejor_alternativa(dict_result, dict_taxonomia)
        #print('Termino Consulta', key_fila)
        alternativa_ =mejor_alternativa['Alternativa']
        coor_ = coor
        datos_iniciales_ = dict_taxonomia
        return {key_fila:{'alternativa':mejor_alternativa['Alternativa'], 'coor':coor, 'datos_iniciales':dict_taxonomia }}
    except Exception as e:
        return {key_fila:{'alternativa':{'class':np.nan, 'order':np.nan, 'family':np.nan, 'genus':np.nan, 'species':np.nan}, 'coor': e ,  'datos_iniciales':dict_taxonomia}}



def main (biotico):
    #print(biotico)
    lista_nombres_definitivos = {'order':'ORDEN', 'family':'FAMILIA', 'genus':'GENERO','species':'ESPECIE'}
    lista_argumentos = []
    for key_fila,row in biotico.iterrows():
        dict_taxonomia = {}
        cuenta_taxones = 0
        for key, value in lista_nombres_definitivos.items():

            dict_taxonomia[key] = row[value]
            if not pd.isna(row[value]):
               cuenta_taxones += 1
        lista_argumentos.append((key_fila, dict_taxonomia))


    pool=Pool(processes=16)
   
    result=pool.map(rev_taxonomia, lista_argumentos)
    print('aqui va')
    pool.close()
    print('aqui va abajo del close')
    
    pool.join()
    print('aqui va abajo del join')
   # resultados = result.get()
   # for key_fila, resultado in resultados.items():
    #    biotico.loc[key_fila , 'CLASE_SU']=resultado.get('class', np.nan)
     #   biotico.loc[key_fila , 'ORDEN_SU']=resultado.get('order', np.nan)
      #  biotico.loc[key_fila , 'FAMILIA_SU']=resultado.get('family', np.nan)
      #  biotico.loc[key_fila , 'GENERO_SU']=resultado.get('genus', np.nan)
      #  biotico.loc[key_fila , 'ESPECIE_SU']=resultado.get('species', np.nan)
    #print('termino')
   # biotico.to_excel(r'D:\User\cjrodriguez\Desktop\BIOTICO\biotico\resultado.xlsx', index=False)
    return result
    
  
def abrir_excel_con_powershell(ruta_excel):
    # Comando de PowerShell para abrir el archivo de Excel
    comando_powershell = f'Start-Process "{ruta_excel}"'
    subprocess.run(["powershell", "-Command", comando_powershell])

def revisar_taxonomia(dir_file, df_data, sheet_name):
    multiprocessing.freeze_support()
    print('Ejecutable de taxonomía')
    print('Autoridad Nacional de Licencias Ambientales')
    print('Centro de Monitoreo')
    print('Última versión: 03/04/2024')
    
    dir_salida = os.path.dirname(dir_file)
   # df_genero_limpio.to_excel(r'D:\TEMP_CINDY\codigo\taxonomia_\FAUNA\FAUNA\error_de_cindy.xlsx', index=True) 
    df_limpio_data = limpiar_data(df_data)
    df_genero_limpio =  ajustar_genero(df_limpio_data)
    #df_genero_limpio.to_excel(r'D:\User\cjrodriguez\Desktop\2024\CODIGOS\Taxonomia\error_de_cindy.xlsx', index=True)
    biotico = df_genero_limpio.copy()
    biotico['CLASE_SU']=np.nan
    biotico['ORDEN_SU']=np.nan
    biotico['FAMILIA_SU']=np.nan
    biotico['GENERO_SU']=np.nan
    biotico['ESPECIE_SU']=np.nan
    biotico['usageKey']=np.nan
    biotico['CORREL']=np.nan
    df_unicos = biotico[['CLASE', 'ORDEN', 'FAMILIA', 'GENERO','ESPECIE', 'CLASE_SU', 'ORDEN_SU', 'FAMILIA_SU', 'GENERO_SU', 'ESPECIE_SU']].fillna('Sin Dato').value_counts().reset_index()
    df_unicos = df_unicos.replace({'Sin Dato': np.nan})
    result = main(df_unicos)
    resultados = result
    biotico = biotico[['CLASE', 'ORDEN', 'FAMILIA', 'GENERO','ESPECIE', 'CLASE_SU', 'ORDEN_SU', 'FAMILIA_SU', 'GENERO_SU', 'ESPECIE_SU', 'CORREL']].fillna('Sin Dato')
    for dict_result_fila in resultados:
        for key_fila, resultado in dict_result_fila.items():
            dict_resultado = resultado['datos_iniciales']
            for taxonomia, nombre in dict_resultado.items():
                dict_resultado[taxonomia] = nombre if not pd.isna(nombre) else 'Sin Dato'
            biotico.loc[((biotico['FAMILIA'] == dict_resultado['family'])&
                    (biotico['GENERO'] == dict_resultado['genus'])&
                    (biotico['ESPECIE'] == dict_resultado['species'])), 'CLASE_SU']=resultado['alternativa'].get('class', np.nan)
            biotico.loc[((biotico['FAMILIA'] == dict_resultado['family'])&
                    (biotico['GENERO'] == dict_resultado['genus'])&
                    (biotico['ESPECIE'] == dict_resultado['species'])), 'ORDEN_SU']=resultado['alternativa'].get('order', np.nan)
            biotico.loc[((biotico['FAMILIA'] == dict_resultado['family'])&
                    (biotico['GENERO'] == dict_resultado['genus'])&
                    (biotico['ESPECIE'] == dict_resultado['species'])), 'FAMILIA_SU']=resultado['alternativa'].get('family', np.nan)
            biotico.loc[((biotico['FAMILIA'] == dict_resultado['family'])&
                    (biotico['GENERO'] == dict_resultado['genus'])&
                    (biotico['ESPECIE'] == dict_resultado['species'])), 'GENERO_SU']=resultado['alternativa'].get('genus', np.nan)
            biotico.loc[((biotico['FAMILIA'] == dict_resultado['family'])&
                    (biotico['GENERO'] == dict_resultado['genus'])&
                    (biotico['ESPECIE'] == dict_resultado['species'])), 'ESPECIE_SU']=resultado['alternativa'].get('species', np.nan)
            biotico.loc[((biotico['FAMILIA'] == dict_resultado['family'])&
                    (biotico['GENERO'] == dict_resultado['genus'])&
                    (biotico['ESPECIE'] == dict_resultado['species'])), 'CORREL']=resultado['coor']
    df_datos_original = pd.read_excel(dir_file, sheet_name=sheet_name)
    biotico = biotico.replace({'Sin Dato': np.nan})
    for column in biotico.columns:
        df_datos_original[column] = biotico[column].values
    try:
        df_datos_original.to_excel(os.path.join(dir_salida, 'Taxonomia.xlsx'), index=False)
        abrir_excel_con_powershell(os.path.join(dir_salida, 'Taxonomia.xlsx'))
    except PermissionError as perm_error:
        tk.messagebox.showerror('Error', 'El archivo Taxonomia.xlsx se encuentra abierto, cerrar antes de ejecutarlo')
  