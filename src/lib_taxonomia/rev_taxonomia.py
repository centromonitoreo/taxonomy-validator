import pandas as pd
import numpy as np

from multiprocess import Pool
import multiprocessing
from lib_taxonomia.limpieza import limpiar_data, ajustar_genero
from lib_taxonomia.multiprocess_gbif import rev_taxonomia
import os
import subprocess
import tkinter as tk

def procesar_taxonomia_en_paralelo(biotico):

    lista_nombres_definitivos = {
        "order": "ORDEN",
        "family": "FAMILIA",
        "genus": "GENERO",
        "species": "ESPECIE",
    }
    lista_argumentos = [
        (
            key_fila,
            {
                key: row[value]
                for key, value in lista_nombres_definitivos.items()
                if not pd.isna(row[value])
            },
        )
        for key_fila, row in biotico.iterrows()
    ]
    pool = Pool(processes=16)
    result = pool.map(rev_taxonomia, lista_argumentos)
    pool.close()
    pool.join()
    return result

def abrir_excel_con_powershell(ruta_excel):
    comando_powershell = f'Start-Process "{ruta_excel}"'
    subprocess.run(["powershell", "-Command", comando_powershell])

def imprimir_informacion_inicial():
    print("Ejecutable de taxonomía")
    print("Autoridad Nacional de Licencias Ambientales")
    print("Centro de Monitoreo")
    print("Última versión: 03/04/2024")

def procesar_datos_iniciales(df_data):
    df_limpio = limpiar_data(df_data)
    return ajustar_genero(df_limpio)

def preparar_biotico(df_genero_limpio):
    columnas_biotico = ["CLASE", "ORDEN", "FAMILIA", "GENERO", "ESPECIE"]
    columnas_sugeridas = [
        "CLASE_SU", "ORDEN_SU", "FAMILIA_SU", "GENERO_SU", "ESPECIE_SU", "usageKey", "CORREL"
    ]
    columnas_totales = columnas_biotico + columnas_sugeridas
    
    biotico = df_genero_limpio.copy()
    for columna in columnas_sugeridas:
        biotico[columna] = np.nan
    return biotico, columnas_totales

def procesar_resultados(biotico, resultados):
    for dict_result_fila in resultados:
        for _, resultado in dict_result_fila.items():
            dict_resultado = {
                taxonomia: (nombre if not pd.isna(nombre) else "Sin Dato") 
                for taxonomia, nombre in resultado["datos_iniciales"].items()
            }
            filtro = (
                (biotico["FAMILIA"] == dict_resultado["family"]) &
                (biotico["GENERO"] == dict_resultado["genus"]) &
                (biotico["ESPECIE"] == dict_resultado["species"])
            )
            
            columnas_a_asignar = {
                "CLASE_SU": resultado["alternativa"].get("class", np.nan),
                "ORDEN_SU": resultado["alternativa"].get("order", np.nan),
                "FAMILIA_SU": resultado["alternativa"].get("family", np.nan),
                "GENERO_SU": resultado["alternativa"].get("genus", np.nan),
                "ESPECIE_SU": resultado["alternativa"].get("species", np.nan),
                "CORREL": resultado["coor"]
            }
            
            for columna, valor in columnas_a_asignar.items():
                biotico.loc[filtro, columna] = valor

    return biotico.replace({"Sin Dato": np.nan})

def guardar_y_abrir_excel(biotico, dir_salida, dir_file, sheet_name):
    df_datos_original = pd.read_excel(dir_file, sheet_name=sheet_name)
    df_datos_original.update(biotico)
    output_path = os.path.join(dir_salida, "Taxonomia.xlsx")
    
    try:
        df_datos_original.to_excel(output_path, index=False)
        abrir_excel_con_powershell(output_path)
    except PermissionError:
        tk.messagebox.showerror(
            "Error",
            "El archivo Taxonomia.xlsx se encuentra abierto, cerrar antes de ejecutarlo",
        )

def revisar_taxonomia(dir_file, df_data, sheet_name):
    multiprocessing.freeze_support()
    imprimir_informacion_inicial()

    dir_salida = os.path.dirname(dir_file)
    df_genero_limpio = procesar_datos_iniciales(df_data)
    biotico, columnas_totales = preparar_biotico(df_genero_limpio)

    df_unicos = biotico[columnas_totales].drop_duplicates().reset_index(drop=True)
    
    resultados = procesar_taxonomia_en_paralelo(df_unicos)
    biotico = biotico[columnas_totales]
    biotico = procesar_resultados(biotico, resultados)

    guardar_y_abrir_excel(biotico, dir_salida, dir_file, sheet_name)