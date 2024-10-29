

def rev_taxonomia(argumentos):
    import numpy as np
    import requests
    import datetime
    import time
    from rapidfuzz import fuzz
    import aiohttp
    import asyncio
    import pandas as pd

    def probar_conexion(max_intentos=10, intervalo=5):
        tiempo_inicio = datetime.datetime.now()
        for intento in range(max_intentos):
            try:
                requests.get("http://www.google.com", timeout=5)
                return True
            except (requests.ConnectionError, requests.Timeout):
                tiempo_actual = datetime.datetime.now()
                tiempo_transcurrido = (tiempo_actual - tiempo_inicio).seconds
                print(
                    f"Intento {intento + 1} fallido. Sin conexión a Internet. Tiempo transcurrido: {tiempo_transcurrido} segundos"
                )
                time.sleep(intervalo)
        print("Conexión no establecida después de varios intentos.")
        return False

    def evaluar_alternativa(alternativa, dict_taxonomia, factor_castigo=0.8):
        lista_nombres_definitivos = {
            "class": "CLASE",
            "order": "ORDEN",
            "family": "FAMILIA",
            "genus": "GENERO",
            "species": "ESPECIE",
        }

        dict_evaluacion = {}

        for taxonomia in lista_nombres_definitivos.keys():
            nombre = alternativa.get(taxonomia)

            if nombre:
                nombre_lower = nombre.lower()
                
                similitudes = [
                    (
                        fuzz.ratio(nombre_usuario.lower(), nombre_lower) * (1 if taxon_usuario == taxonomia else factor_castigo),
                        taxon_usuario,
                    )
                    for taxon_usuario, nombre_usuario in dict_taxonomia.items()
                    if isinstance(nombre_usuario, str)
                ]
                correlacion_max, taxon_relacion = max(similitudes, default=(0, "error"))

                dict_evaluacion[taxonomia] = {
                    "correlacion_max": correlacion_max,
                    "taxon_relacion": taxon_relacion,
                    "nombre_sugerido": nombre,
                }
            else:
                dict_evaluacion[taxonomia] = {
                    "correlacion_max": 0,
                    "taxon_relacion": "error",
                    "nombre_sugerido": None,
                }

        dict_evaluacion["Alternativa"] = alternativa
        return dict_evaluacion


    async def gbif_rev_async(taxonomia, nivel_taxonomia, dict_taxonomia):
        url = f"https://api.gbif.org/v1/species/match?name={taxonomia}"
        dict_permitidos = {
            "order": ["order", "family"],
            "family": ["genus", "family", "order"],
            "genus": ["genus", "family"],
            "species": ["genus", "species"],
        }
        list_alternativas = []

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    species_busqueda = await response.json()
                    if species_busqueda.get("matchType") != "NONE" or "alternatives" in species_busqueda:
                        alternativas = species_busqueda.get("alternatives", [])
                        list_alternativas.extend(
                            evaluar_alternativa(alt, dict_taxonomia)
                            for alt in alternativas
                            if alt["rank"].lower() in dict_permitidos[nivel_taxonomia]
                        )
                        if species_busqueda.get("rank", "").lower() in dict_permitidos[nivel_taxonomia]:
                            list_alternativas.append(evaluar_alternativa(species_busqueda, dict_taxonomia))
        return list_alternativas
    
    def obtener_resultados_gbif(dict_taxonomia):
        async def ejecutar_consultas():
            tasks = [
                gbif_rev_async(taxon, nivel, dict_taxonomia)
                for nivel, taxon in dict_taxonomia.items()
            ]
            return await asyncio.gather(*tasks)

        return asyncio.run(ejecutar_consultas())

    def calificar_alternativa(alternativa, dict_taxonomia):

        taxones_no_nulos = [
            taxon for taxon, valor in dict_taxonomia.items() if (not pd.isna(valor) and valor !="")
        ]
        taxon_menor = taxones_no_nulos[0] if taxones_no_nulos else None
        taxon_mayor = taxones_no_nulos[-1] if taxones_no_nulos else None
        dict_pesos = {
            taxon: (3 if taxon in {taxon_menor, taxon_mayor} else 1)
            for taxon in taxones_no_nulos
        }

        suma_alternativa = sum(
            valor["correlacion_max"] * dict_pesos[taxonomia]
            for taxonomia, valor in alternativa.items()
            if taxonomia in dict_pesos
            and valor is not None
            and taxonomia != "Alternativa"
        )

        suma_alternativa /= sum(dict_pesos.values())
        print('---------------Evaluacion--------------------')
        print(dict_taxonomia, alternativa ,suma_alternativa)
        return suma_alternativa

    def seleccionar_mejor_alternativa(dict_result, dict_taxonomia):
        puntaje_mejor_alternativa = 0
        mejor_alternativa = {}

        for alternativas_taxon in dict_result.values():
            for alternativa_taxon in alternativas_taxon:
                puntaje_actual = calificar_alternativa(alternativa_taxon, dict_taxonomia)
                if puntaje_actual > puntaje_mejor_alternativa:
                    puntaje_mejor_alternativa = puntaje_actual
                    mejor_alternativa = alternativa_taxon

        return mejor_alternativa, puntaje_mejor_alternativa

    try:
        key_fila, dict_taxonomia = argumentos
        probar_conexion()
        resultados_gbif = obtener_resultados_gbif(dict_taxonomia)
        
        dict_result = {nivel: resultado for nivel, resultado in zip(dict_taxonomia.keys(), resultados_gbif)}

        mejor_alternativa, coor = seleccionar_mejor_alternativa(dict_result, dict_taxonomia)
        alternativa = mejor_alternativa.get("Alternativa", {
            "class": np.nan,
            "order": np.nan,
            "family": np.nan,
            "genus": np.nan,
            "species": np.nan,
        })

        return {
            key_fila: {
                "alternativa": alternativa,
                "coor": coor,
                "datos_iniciales": dict_taxonomia,
            }
        }

    except Exception as e:
        return {
            key_fila: {
                "alternativa": {
                    "class": np.nan,
                    "order": np.nan,
                    "family": np.nan,
                    "genus": np.nan,
                    "species": np.nan,
                },
                "coor": e,
                "datos_iniciales": dict_taxonomia,
            }
        }