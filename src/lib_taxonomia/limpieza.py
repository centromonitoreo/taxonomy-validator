import re
import pandas as pd
import numpy as np

def limpiar_data(df):
    # Convertir a minúsculas y llenar NaN con cadena vacía
    columnas = ['GENERO', 'ESPECIE']
    for col in columnas:
        df[col] = df[col].str.lower().fillna('')  # Convertir a minúsculas y llenar NaN con cadena vacía
        
        # Eliminar palabras no deseadas rodeadas de caracteres no alfabéticos o espacios
        palabras_no_deseadas = r'(?<![a-zA-Z])(morfo|morfoespecie|mf|subfamilia)(?![a-zA-Z])'
        df[col] = df[col].str.replace(palabras_no_deseadas, '', regex=True)
        
        # Eliminar caracteres específicos y números
        caracteres_especiales = r'[.,*?\"‡-]'
        df[col] = df[col].str.replace(caracteres_especiales, '', regex=True)
        df[col] = df[col].str.replace(r'\d', '', regex=True)

        # Eliminar letras acentuadas
        acentos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 
                   'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U'}
        for acento, letra in acentos.items():
            df[col] = df[col].str.replace(acento, letra)
        
        # Eliminar términos completos específicos
        df[col] = df[col].str.replace(r'\b(sp|cf|spp|aff|mf)\b', '', regex=True)
    
    # Mantener solo la primera palabra en 'GENERO' y las primeras dos en 'ESPECIE'
    df['GENERO'] = df['GENERO'].str.split().str[0]
    df['ESPECIE'] = df['ESPECIE'].str.split().str[:2].str.join(' ')
    
    # Alerta si alguna palabra en 'GENERO' termina en 'eae'
    if df['GENERO'].str.endswith('eae').any():
        print("¡Alerta! Al menos una palabra de la columna 'GENERO' termina en 'eae'.")

    return df

def contar_palabras_y_modificar(row):
    # Asumimos que 'GENERO' y 'ESPECIE' ya están limpias y no contienen NaN
    especie, genero = row['ESPECIE'], row['GENERO']
    palabras_especie = especie.split()
    if (len(palabras_especie) == 1) and (genero != especie) and (len(genero)>1):
        especie = f"{genero} {especie}"
    return especie

def ajustar_genero(df):
    df['ESPECIE'] = df.apply(contar_palabras_y_modificar, axis=1)
    return df