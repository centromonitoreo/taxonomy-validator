# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 16:27:25 2023

@author: diego
"""
import re
import pandas as pd
import numpy as np

def limpiar_texto(texto):
    # Eliminar puntos, comas, guiones y números
    texto = re.sub(r'[.,-]', '', str(texto))
    texto = re.sub(r'\([^)]*\)', '', texto)
    texto = re.sub(r'\d', '', texto)
    texto = re.sub(r'\*', '', texto)
    texto = re.sub(r'\?', '', texto)
    texto = re.sub(r'[áéíóúÁÉÍÓÚ]', '', texto)
    texto = texto.replace('morfo', '')
    texto = texto.replace('morfoespecie', '')
    texto = texto.replace('Morfoespecie', '')
    texto = texto.replace('mf', '')
    texto = texto.replace('subfamilia', '')
    texto = texto.replace('"', '')
    texto = texto.replace("‡", '')
    
    return texto

def words_delete(texto):
    palabras = texto.split()
    palabras_filtradas = [palabra for palabra in palabras if len(palabra) > 1]
    return ' '.join(palabras_filtradas)


def limpiar_data(df):
    nombre_genero = 'GENERO'
    df[nombre_genero] = df[nombre_genero].str.lower()
    df[nombre_genero] = df[nombre_genero].apply(limpiar_texto)
    df[nombre_genero] = df[nombre_genero].apply(lambda x: ' '.join(x.split()[:1]))
    df[nombre_genero] = df[nombre_genero].str.replace(r'\b(sp|cf|spp|aff|mf)\b', '', regex=True)
    # Verificar si alguna palabra de la columna termina en "eae"
    condicion = df[nombre_genero].str.endswith('eae').any()

    # Generar la alerta si se cumple la condición
    if condicion:
        print("¡Alerta! Al menos una palabra de la columna 'genero' termina en 'eae'.")
        
    nombre_especie = 'ESPECIE'

    df[nombre_especie] = df[nombre_especie].str.lower()
    df[nombre_especie] = df[nombre_especie].apply(limpiar_texto)
    df[nombre_especie] = df[nombre_especie].apply(lambda x: ' '.join(x.split()[:2]))
    df[nombre_especie] = df[nombre_especie].apply(words_delete)

    # Crear una columna temporal para almacenar los datos originales
    df['especie_original'] = df[nombre_especie]

    # Eliminar las palabras "spp", "aff" y "cf" de la columna "especie"
    df[nombre_especie] = df[nombre_especie].str.replace(r'\b(sp|cf|spp|aff|mf)\b', '', regex=True)

  #  ruta_archivo_modificado =r'D:\User\cjrodriguez\Desktop\TEMPORAL\TAXONOMIA\lesly\fauna_limpieza.xlsx'  # Reemplaza con la ruta donde deseas guardar el archivo modificado
   # df.to_excel(ruta_archivo_modificado, index=False)
    return df


def contar_palabras_y_modificar(row):
    if (isinstance(row['ESPECIE'], str)) & (isinstance(row['GENERO'], str)):
        especie = row['ESPECIE']
        genero = row['GENERO']
        palabras_especie = especie.split()
        if (len(palabras_especie) == 1) and (not pd.isna(genero)):
            if genero.lower() != especie.lower():  # Verifica si las palabras no son idénticas
                if genero.lower() != palabras_especie[0].lower():  # Verifica si género no es igual a la primera palabra de la especie
                    especie = genero + ' ' + especie
        return especie
    return row['ESPECIE']

def ajustar_genero(df):
    df['ESPECIE'].fillna('', inplace=True)
    df['GENERO'].fillna('', inplace=True)
    df['ESPECIE'] = df['ESPECIE'].replace({'nan':np.nan})
    df['GENERO'].fillna('', inplace=True)
    df['GENERO'] = df['GENERO'].replace({'nan':np.nan})
    df['ESPECIE'] = df.apply(contar_palabras_y_modificar, axis=1)
    return df
