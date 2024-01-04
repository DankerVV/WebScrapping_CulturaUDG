#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  9 11:37:42 2023

@author: carlossalcidoa
"""
import pandas as pd
from bs4 import BeautifulSoup
import requests
import os
import re
from sqlalchemy import create_engine
from dateutil import parser
from datetime import datetime
#------------------------------------------------------------------------------------------------------------------
#PARTE 0: HACEMOS DECLARACIONES DE FUNCIONES, DICCIONARIOS, Y ESAS COSAS QUE VAN AL INICIO
url = 'https://www.cinetecaficg.com/cineforo/listings'
response = requests.get(url)

if response.status_code == 200:
    page_content = response.content
    print("Acceso exitoso a la página ", url)
else:
    print("Error al acceder a la página.")
soup = BeautifulSoup(page_content, 'html.parser')

meses = {
    'enero': 'January',
    'febrero': 'February',
    'marzo': 'March',
    'abril': 'April',
    'mayo': 'May',
    'junio': 'June',
    'julio': 'July',
    'agosto': 'August',
    'septiembre': 'September',
    'octubre': 'October',
    'noviembre': 'November',
    'diciembre': 'December'
}


def descargar_imgs():#----------------------------------------------------------------------
    if not os.path.exists("imagenes_cineforo"):# Crear una carpeta para almacenar las imágenes
        os.makedirs("imagenes_cineforo")   
    # Buscar elementos con la clase 'item poster' que contienen la URL de la imagen
    for index, element in enumerate(soup.find_all(class_='item poster'), start=1):
       style = element.get('style')

       # Utilizar una expresión regular para extraer la URL de la imagen
       img_url_match = re.search(r"url\('([^']+)'\)", style)
       if img_url_match:
           img_url = img_url_match.group(1)

           # Crear un nombre de archivo para la imagen con un número secuencial
           img_filename = os.path.join("imagenes_cineforo", f"imagen_{index}.jpg")
           img_data = requests.get(img_url).content# Descargar la imagen
           
           # Guardar la imagen en el directorio
           with open(img_filename, 'wb') as img_file:
               img_file.write(img_data)
           imagenes.append(os.path.abspath(img_filename)) 
           #print("Imagen descargada:", img_filename)

def formato_fecha(fecha_hora, hora):#----------------------------------------------------------------------
    fecha_hora = fecha_hora.replace('de ', '')
    # Expresión regular para eliminar el día de la semana
    fecha_hora = re.sub(r'^\w+\s+', '', fecha_hora)
    # Dividir la cadena en día y mes
    dia, mes = fecha_hora.split()
    # Reorganizar y unir para obtener el nuevo formato
    fecha_hora = f"{mes} {dia}"
    # Reemplazar el nombre del mes con su equivalente en inglés
    for mes_espanol, mes_ingles in meses.items():
        fecha_hora = fecha_hora.replace(mes_espanol, mes_ingles)
    fecha_hora = f"{fecha_hora} {hora}"
    #agregar el año al inicio
    ano_actual = datetime.now().year
    #VERIFICACIÓN PARA AGREGAR EL AÑO, Y VALIDAR LA POSIBILIDAD DE QUE SAQUEN OBRAS DE ENERO EN DICIEMBRE
    if(datetime.now().month == 12) and (mes_ingles == 'January'):
        ano_actual= ano_actual+1
        fecha_hora = f"{ano_actual} - {fecha_hora}"
    else:
        fecha_hora = f"{ano_actual} - {fecha_hora}"
    datetime_obj = parser.parse(fecha_hora)
    formatted_datetime = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
    
    return formatted_datetime
           

#--------------------------------------------------------------------------------------------------------------------------
enlaces_obras=[]#PARTE 1: EXTRAEMOS LOS ENLACES DE LAS OBRAS Y SUS RESPECTIVAS IMAGENES
imagenes=[]
for a in soup.find_all('a', href=True):
    if "https://www.cinetecaficg.com/movie" in a['href']:
        enlaces_obras.append(a['href'])
descargar_imgs()
df=pd.DataFrame(enlaces_obras)
dfImagenes=pd.DataFrame(imagenes)
dfImagenes = dfImagenes.rename(columns={df.columns[0]: 'imagenURL'})
df = df.rename(columns={df.columns[0]: 'Enlace Obra'})
#print(enlaces_obras)
#ATENCIÓN VAMOS A ENTRAR TRES VECES A LOS ENLACES PARA QUE EL DATAFRAME NO QUEDE REVUELTO

#--------------------------------------------------------------------------------------------------------------------------
#PARTE 2: EXTRAEMOS INFO DE LA OBRA
data = []
for enlace in enlaces_obras:
    response = requests.get(enlace)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')# Analizar el contenido HTML de la página vinculada
        content_elements = soup.find_all(class_='content')# Buscar elementos con la clase "content"
        obra = {}#DICCIONARIO PARA ALMACENAR LOS DATOS
        
        # Buscar el texto dentro de la etiqueta <h1> con la clase "heading"
        titulo_element = soup.find(class_='heading').find('h1')
        if titulo_element:
            titulo = titulo_element.text.strip()
            obra['Título'] = titulo  # Agregar el título al diccionario           
        # Iterar a través de los elementos con la clase "content"
        for content_element in content_elements:
            # Buscar elementos con la clase "key" (títulos)
            key_elements = content_element.find_all(class_='key')
            # Buscar elementos con la clase "value" (datos)
            value_elements = content_element.find_all(class_='value')

            # Combinar los títulos y datos en el diccionario
            for key, value in zip(key_elements, value_elements):
                titulo = key.text.strip()
                valor = value.text.strip()
                obra[titulo] = valor
        
        # Buscar el elemento con la clase "boxed" y extraer el texto como "Sinopsis"
        boxed_element = soup.find(class_='boxed')
        if boxed_element:
            sinopsis = boxed_element.text.strip()
            obra['Sinopsis'] = sinopsis  # Agregar la sinopsis al diccionario
        data.append(obra)# Agregar el diccionario a la lista data
        
    else:
        print("Error al acceder a la página:", response.status_code)
df2 = pd.DataFrame(data)
df = pd.concat([df, df2], axis=1)
        


#---------------------------------------------------------------------------------------------------------
data=[]#PARTE 3: EXTRAEMOS FECHAS Y BOLETOS DE CINEFORO
for enlace in enlaces_obras:
    response = requests.get(enlace)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')# Analizar el contenido HTML de la página vinculada
        content_elements = soup.find_all(class_='content')# Buscar elementos con la clase "content"
        obra = {}#DICCIONARIO PARA ALMACENAR LOS DATOS
        
        # Buscar la sección "cineforo-schedules"
        schedules_section = soup.find(class_='cineforo-schedules')
        if schedules_section:
            # Buscar elementos <h2> y elementos con la clase "time"
            h2_elements = schedules_section.find_all('h2')
            time_elements = schedules_section.find_all(class_='time')
            
            # Agregar fechas y enlaces al diccionario
            for j, (h2, time) in enumerate(zip(h2_elements, time_elements)):
                fecha = h2.text.strip() if h2 else None
                hora = time.text.strip() if time else None
            
                # Si hay fecha y hora, formatearlas
                if fecha and hora:
                    formatted_datetime= formato_fecha(fecha,hora)            
                    enlaces_compra = h2.find_next('a', href=lambda href: href and 'https://ticketing.useast.veezi.com/purchase/' in href)
                    enlace_compra = enlaces_compra.get('href', '').strip() if enlaces_compra else None
                    
                    data.append({'pertenece': '5', 'fecha': formatted_datetime, 'boleto': enlace_compra})
    else:
        print("Error al acceder a la página:", response.status_code)
dfFechasCineforo = pd.DataFrame(data)  
#df2 = pd.concat([df2, df3], axis=1)#juntar los dataframes
#---------------------------------------------------------------------------------------------------------

data=[]#PARTE 4: EXTRAEMOS FECHAS Y BOLETOS DE CINETECA
for enlace in enlaces_obras:
    response = requests.get(enlace)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')# Analizar el contenido HTML de la página vinculada
        content_elements = soup.find_all(class_='content')# Buscar elementos con la clase "content"
        obra = {}#DICCIONARIO PARA ALMACENAR LOS DATOS
        # Buscar la sección "cineforo-schedules"
        schedules_section = soup.find(class_='cineteca-schedules')
        if schedules_section:
            # Buscar elementos <h2> y elementos con la clase "time"
            h2_elements = schedules_section.find_all('h2')
            time_elements = schedules_section.find_all(class_='time')
            
            # Agregar fechas y enlaces al diccionario
            for j, (h2, time) in enumerate(zip(h2_elements, time_elements)):
                fecha = h2.text.strip() if h2 else None
                hora = time.text.strip() if time else None
            
                # Si hay fecha y hora, formatearlas
                if fecha and hora:
                    fecha = fecha.replace(',', '')
                    formatted_datetime= formato_fecha(fecha,hora)            
                    enlaces_compra = h2.find_next('a', href=lambda href: href and 'https://ticketing.useast.veezi.com/purchase/' in href)
                    enlace_compra = enlaces_compra.get('href', '').strip() if enlaces_compra else None
                    
                    data.append({'pertenece': '5', 'fecha': formatted_datetime, 'boleto': enlace_compra})
        
    else:
        print("Error al acceder a la página:", response.status_code)
dfFechasCineteca = pd.DataFrame(data)  
#df2 = pd.concat([df2, df3], axis=1)#juntar los dataframes


#---------------------------------------------------------------------------------------------------------
#PARTE 5: ORGANIZAR LOS DATAFRAMES
#IMAGENES
dfImagenes.insert(0, 'pertenece', 5)
dfImagenes.to_csv("Imagenes.csv", index=False)

#fecha_evento
dfFechasCineforo.to_csv("FechasCineforo.csv")
dfFechasCineteca.to_csv("FechasCineteca.csv")

#eventopresencial
dfEventoPresencial = pd.DataFrame(columns=["status", "solicitaEvento", "nombreEvento", "subtituloEvento", "areaProgramadora", "categoria",
                                  "subGenero", "grupoActividad", "sedeUniversitaria","foro", "duracion", "sinopsis", "enlaceVideo", 
                                  "evento", "temporada", "costoBoleto", "eventoActivo", "dat", "TS", "evento_especial", "otroGenero",
                                  "tipo_evento"])

dfEventoPresencial["nombreEvento"] = df["Título"]
dfEventoPresencial["sinopsis"] = df["Sinopsis"]
dfEventoPresencial["duracion"] = df["Duración:"]
dfEventoPresencial["costoBoleto"] = 50
dfEventoPresencial = dfEventoPresencial.where(pd.notna(dfEventoPresencial), None)

dfEventoPresencial.to_csv("eventopresencial.csv", index=False)
df.to_csv("cartelera.csv", index=False)

'''
#---------------------------------------------------------------------------------------------------------
#PARTE 6: CONEXIÓN A LA BASE DE DATOS PHPMYADMIN, EN EL LOCALHOST
try:
    # Crear una conexión a la base de datos MySQL utilizando SQLAlchemy
    engine = create_engine("mysql+mysqlconnector://root:@localhost:3306/EventosCineforo")
    print("Conexión exitosa a la base de datos")

    # Guardar AudiotorioTelmex en la base de datos a través de SQLAlchemy
    df.to_sql(name='eventos', con=engine, if_exists='replace', index=False)
    

except Exception as e:
    # Si hay un error en la conexión o en la operación, imprimirá el mensaje de error
    print("Error al conectar a la base de datos:", e)
'''
            
