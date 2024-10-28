# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 14:36:34 2023

@author: CJRodriguez
"""

import pandas as pd

ruta_excel=r'D:\User\cjrodriguez\Desktop\TEMPORAL\TAXONOMIA\lesly\fauna_limpieza.xlsx'
nombre_hoja= 'Hoja1'

df= pd.read_excel(ruta_excel)

df['ESPECIE'].fillna('', inplace=True)
df['GENERO'].fillna('', inplace=True)

# Función para contar palabras y modificar la columna "género"
def contar_palabras_y_modificar(row):
    especie = row['ESPECIE']
    genero = row['GENERO']
   
    palabras_especie = especie.split()
   
    if len(palabras_especie) == 1:
        especie = genero + ' ' + especie
   
    return especie

# Aplicar la función a cada fila del DataFrame
df['ESPECIE'] = df.apply(contar_palabras_y_modificar, axis=1)


ruta_archivo_modificado =r'D:\User\cjrodriguez\Desktop\TEMPORAL\TAXONOMIA\lesly\FAUNA_genero.xlsx'  # Reemplaza con la ruta donde deseas guardar el archivo modificado
df.to_excel(ruta_archivo_modificado, index=False)