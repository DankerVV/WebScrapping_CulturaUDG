"""
Created on Tue Sep 26 11:51:06 2023

@author: carlossalcidoa
"""
from bs4 import BeautifulSoup
import requests
import os
from urllib.parse import urljoin
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from sqlalchemy import create_engine
from dateutil import parser

#------------------------------------------------------------------------------------------------------------------
#PARTE 0: Declarar todo lo necesario
#ACCEDER AL URL DE LA PROGRAMACIÓN DEL AUDITORIO
url = 'https://www.auditorio-telmex.com/programacion.php'
response = requests.get(url)

if response.status_code == 200:
    page_content = response.content
    print("Se accedió a la página")
else:
    print("Error al acceder a la página.")

soup = BeautifulSoup(page_content, 'html.parser')

meses = {#----------------------------------------------------------------------
        'Enero': 'jan',
        'Febrero': 'feb',
        'Marzo': 'mar',
        'Abril': 'apr',
        'Mayo': 'may',
        'Junio': 'jun',
        'Julio': 'jul',
        'Agosto': 'aug',
        'Septiembre': 'sep',
        'Octubre': 'oct',
        'Noviembre': 'nov',
        'Diciembre': 'dec'
}

# Función para convertir las fechas
def convertir_fecha(fecha):
    if fecha == '':
        return fecha  # Mantén la casilla vacía si está vacía
    try:
        fecha_obj = parser.parse(fecha, dayfirst=True, fuzzy=True)
        return fecha_obj.strftime("%m-%d")
    except ValueError:
        return fecha  # Mantén la casilla original si no se pudo analizar la fecha
    

# Define una función para convertir horas al formato deseado
def convertir_hora(hora):
    if pd.notna(hora) and hora != '':
        try:
            hora_obj = parser.parse(hora, fuzzy=True)
            return hora_obj.strftime("%H:%M:%S")
        except ValueError:
            return hora  # Mantén la casilla original si no se pudo analizar la hora
    else:
        return hora

# Define una función para convertir fechas y horas al formato deseado
def convertir_fecha_hora(fecha_hora):
    if pd.notna(fecha_hora) and fecha_hora != '':
        try:
            fecha_hora_obj = parser.parse(fecha_hora, dayfirst=True, fuzzy=True)
            return fecha_hora_obj.strftime("%m-%d %H:%M:%S")
        except ValueError:
            return fecha_hora  # Mantén la casilla original si no se pudo analizar la fecha y hora
    else:
        return fecha_hora


#------------------------------------------------------------------------------------------------------------------
#PARTE 1: 
logos = soup.find_all(class_='imgLogo')
txtLogos = soup.find_all(class_='txtLogo')

# Crear una lista para almacenar los datos
data = []
ruta_actual = os.getcwd()
# Crear una carpeta dentro del directorio actual para almacenar las imágenes si no existe
carpeta_imagenes = 'imagenes_chicas'
ruta_completa = os.path.join(ruta_actual, carpeta_imagenes)

if not os.path.exists(ruta_completa):
    os.makedirs(ruta_completa)
for count, (logo, txtLogo) in enumerate(zip(logos, txtLogos), start=1):
    # Encuentra la etiqueta de imagen dentro del enlace y obtén el atributo "src"
    imagen = logo.find('img')
    if imagen:
        imagen_url_rel = imagen['src']  # URL relativa de la imagen

        # Construye la URL completa utilizando urljoin
        imagen_url_abs = urljoin(url, imagen_url_rel)

        # AQUI SE DESCARGA LA IMAGEN CHICA Y SE GUARDA EN LA RUTA
        try:
            imagen_response = requests.get(imagen_url_abs)
            if imagen_response.status_code == 200:
                nombre_archivo = f"imagen_chica{count}.jpg"
                ruta_de_guardado = os.path.join(ruta_completa, nombre_archivo)
                with open(ruta_de_guardado, "wb") as archivo:
                    archivo.write(imagen_response.content)
                print(f"La imagen relacionada con imgLogo {count} ha sido descargada y guardada en {ruta_completa}")

                # Obtén el texto de "txtLogo" y agrégalo a la lista de datos
                #texto_txtLogo = txtLogo.text.strip()
                #data.append({'Nombre de Archivo': nombre_archivo, 'Texto_txtLogo': texto_txtLogo})
                texto_txtLogo = txtLogo.find_all(text=True)
                data_dict = {'Nombre de Archivo': nombre_archivo}
                for i, texto in enumerate(texto_txtLogo):
                    data_dict[f'Texto_txtLogo{i + 1}'] = texto.strip()
                data.append(data_dict)
            
            else:
                print(f"Error al descargar la imagen {imagen_url_abs}. Código de estado: {imagen_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error al realizar la solicitud HTTP para la imagen {imagen_url_abs}: {str(e)}")

# Crear un DataFrame de Pandas con los datos
df = pd.DataFrame(data)
# Guardar el DataFrame en un archivo CSV
#df.to_csv('AuditorioTelmex.csv', index=False)




#------------------------------------------------------------------------------------------------------------------
#PARTE 2: 
#ACCEDER AL URL DEL AUDITORIO TELMEX, ESTE URL ES DIFERENTE
url = "https://www.auditorio-telmex.com/"
response = requests.get(url)

if response.status_code == 200:
    page_content = response.content
    print("\nSe accedió a la página")
else:
    print("\nError al acceder a la página.")

soup = BeautifulSoup(page_content, 'html.parser')
title = soup.title.text
print(f'Título de la página: {title}')     

#EXTRAER INFORMACIÓN DEL URL
cuadro = soup.find_all(class_='cuadro')
infoEvento = soup.find_all(class_='infoEvento efecto')
fondo = soup.find_all(class_='fondo')
informacion = soup.find_all(class_='informacion')
info_tit = soup.find_all(class_='infoTit')
info_txt = soup.find_all(class_='infoTxt')

#Encontrar todos los elementos img
imagenes = soup.find_all('img')
# Encuentra todos los elementos <a> que contienen enlaces
enlaces = soup.find_all('a')
data2 = []#lista para guardar los datos

# Itera sobre los elementos y agrega los datos a la lista data
for i in range(len(cuadro)):
    data2.append({
        'Cuadro': cuadro[i].text.strip(),
        #'InfoEvento': infoEvento[i].text.strip(),
        'Fondo': fondo[i].text.strip(),
        'Informacion': informacion[i].text.strip(),
        'InfoTit': info_tit[i].text.strip(),
        'InfoTxt': info_txt[i].text.strip()
    })

# Crear un DataFrame a partir de la lista de datos
df2 = pd.DataFrame(data2)

# Agregar una columna al DataFrame para los enlaces href
enlaces_href = []
for enlace in enlaces:
    href = enlace.get('href')
    enlaces_href.append(href if href else '')

# Crear una lista para almacenar los enlaces de eventos
event_links = [href for href in enlaces_href if "evento.php" in href]
# Crear un DataFrame a partir de la lista de enlaces de eventos
df_event_links = pd.DataFrame({'Event_Links': event_links})
# Guardar el DataFrame de enlaces de eventos en un archivo CSV
#df_event_links.to_csv('event_links.csv', index=False)
#df = pd.concat([df, df_event_links], axis=1)
#Imprimir el DataFrame
#print(df2)
# Guardar el DataFrame en un archivo CSV
#df2.to_csv('datos.csv', index=False) 




#------------------------------------------------------------------------------------------------------------------
#PARTE 3: 
# DESCARGAR IMAGENES MEDIANAS
count = 1
for imagen in imagenes:
    imagen_url_rel = imagen['src']  # URL relativa de la imagen
    # Si la URL contiene "imagen_mediana.jpg", descarga la imagen
    if ("imagen_mediana.jpg" in imagen_url_rel) or ("imagen_mediana.png" in imagen_url_rel):
        # Construye la URL completa utilizando urljoin
        imagen_url_abs = urljoin(url, imagen_url_rel)

        # Realiza una solicitud HTTP GET para obtener la imagen
        imagen_response = requests.get(imagen_url_abs)

        # Verifica si la solicitud fue exitosa (código de estado 200)
        if imagen_response.status_code == 200:
            # Obtén el nombre del archivo de la URL
            nombre_archivo = f'imagen_mediana_{count}.jpg'
            # Guarda la imagen en un archivo local
            with open(nombre_archivo, 'wb') as archivo:
                archivo.write(imagen_response.content)
            print(f'La imagen {nombre_archivo} ha sido descargada con éxito.')
            count += 1
        else:
            print(f'Error al descargar la imagen {imagen_url_abs}. Código de estado: {imagen_response.status_code}')



#------------------------------------------------------------------------------------------------------------------
#PARTE 4: DESCARGAR IMAGENES GRANDES y obtener enlaces de compra (es el mismo para todos)
# Obtén los enlaces de eventos
count = 1
print("\n")
event_links = [href for href in enlaces_href if "evento.php" in href]

# Crea una lista para almacenar las rutas de las imágenes "imagen_grande"
imagen_grande_links = []
enlaces_a_comprar = []

# Itera a través de los enlaces de eventos
for event_link in event_links:
    # Construye la URL completa del evento utilizando urljoin
    event_url_abs = urljoin(url, event_link)

    # Realiza una solicitud HTTP GET para obtener la página del evento
    event_response = requests.get(event_url_abs)

    # Verifica si la solicitud fue exitosa (código de estado 200)
    if event_response.status_code == 200:
        # Parsea la página del evento
        event_soup = BeautifulSoup(event_response.content, 'html.parser')

        # Encuentra la imagen con nombre que contiene "imagen_grande"
        imagen_grande = event_soup.find('img', src=lambda x: x and 'imagen_grande' in x)
        # Buscar todos los elementos <a> en event_soup
        enlaces = event_soup.find_all('a', href=True)

        # Iterar a través de los enlaces y buscar el que contiene 'www.ticketmaster.com' en su atributo 'href'
        for enlace in enlaces:
            href = enlace['href']
            if href and 'www.ticketmaster.com.mx/venue' in href:#OJO! es el mismo enlace para todas las obras
                enlaces_a_comprar.append(href)
                print("Enlace a comprar:", href)
                break
        
        if imagen_grande:
            # Obtiene la URL de la imagen "imagen_grande"
            imagen_grande_url_rel = imagen_grande['src']
            imagen_grande_url_abs = urljoin(event_url_abs, imagen_grande_url_rel)

            # Realiza una solicitud HTTP GET para descargar la imagen
            imagen_grande_response = requests.get(imagen_grande_url_abs)

            # Verifica si la solicitud de la imagen fue exitosa
            if imagen_grande_response.status_code == 200:
                # Obtén el nombre del archivo de la URL
                nombre_archivo = f'imagen_grande_{count}.jpg'
                # Guarda la imagen en un archivo local
                with open(nombre_archivo, 'wb') as archivo:
                    archivo.write(imagen_grande_response.content)
                print(f'La imagen {nombre_archivo} ha sido descargada con éxito.')
                count += 1
            else:
                print(f'Error al descargar la imagen {imagen_grande_url_abs}. Código de estado: {imagen_grande_response.status_code}')
    
    else:
        print(f'Error al acceder a la página del evento {event_url_abs}. Código de estado: {event_response.status_code}')



#------------------------------------------------------------------------------------------------------------------
#PARTE 5: EXTRAER INFORMACIÓN DE LOS BOLETOS
url2 = enlaces_a_comprar[1]#TODOS LOS ENLACES DE LA LISTA SON IGUALES, ASI QUE DA IGUAL CUAL TOMEMOS
print("\n\nNuevo URL:", url2)
# Iniciar un navegador web, esto porque Beautiful Soup no puede
driver = webdriver.Chrome()

# Abrir la página web
driver.get(url2)

# Encontrar y hacer clic en el botón
boton = driver.find_element('css selector', 'button[data-testid="pagination-button"]')
boton.click()
time.sleep(5)
# Cierra el navegador
#driver.quit()

#examinar la página con beautiful soup
page_content = driver.page_source
soup = BeautifulSoup(page_content, 'html.parser')
# Encontrar todos los enlaces que contienen "https://www.ticketmaster.com.mx/"
enlaces_ticketmaster = soup.find_all('a', href=lambda href: href and 'https://www.ticketmaster.com.mx/' in href and 'zapopan' in href)

# Imprimir los enlaces encontrados
enlaces_ticketmaster2=[]#nueva lista, aqui vamos a guardar el texto de los href 
count=1
for enlace in enlaces_ticketmaster:
    print(count,":")
    print(enlace['href'])
    enlace=enlace['href']
    enlaces_ticketmaster2.append(enlace)
    count+=1
    
    #EN TEORÍA FUNCIONA, PERO NOS BLOQUEA EL ACCESO POR SOSEPECHA DE ROBOT
    
    # Obtener el contenido de la página del enlace utilizando requests
    response = requests.get(enlace)
   
    if response.status_code == 200:
        page_content_enlace = response.content
        
        # Analizar el contenido del enlace con BeautifulSoup
        enlace_soup = BeautifulSoup(page_content_enlace, 'html.parser')
       
        # Encontrar elementos con clase "sc-148tjjv-3 izkONI"
        boletos = enlace_soup.find_all(class_='sc-148tjjv-3 izkONI')
       
        # Encontrar elementos con clase "sc-148tjjv-5 fzyEmD"
        precios = enlace_soup.find_all(class_='sc-148tjjv-5 fzyEmD')
       
        # Procesar los elementos encontrados como sea necesario
        for boleto in boletos:
            print(boleto)
            pass
       
        for precio in precios:
            print(precio)
            pass
    else:
        print(f"Error al acceder al enlace. Código de estado: {response.status_code}")




#------------------------------------------------------------------------------------------------------------------
#PARTE 6: UNIR LOS DATAFRAME EN UNO SOLO, LUEGO PASARLO COMO ARCHIVO CSV

#df2 = pd.read_csv('datos.csv')
# Combinar los DataFrames verticalmente (uno debajo del otro)
df_combined = pd.concat([df, df2], axis=1)
df3 = pd.DataFrame(enlaces_a_comprar)
df4 = pd.DataFrame(enlaces_ticketmaster2)
df_combined2= pd.concat([df3, df4], axis=1)
df_final=pd.concat([df_combined, df_combined2], axis=1)
#df
#df_combined = df_combined.append(enlaces_a_comprar,ignore_index=True)
#df_combined = df_combined.append(enlaces_ticketmaster2,ignore_index=True)

# Opcionalmente, puedes restablecer los índices si lo deseas
#df_combined.reset_index(drop=True, inplace=True)
df_final.to_csv('CarteleraTelmex.csv', index=False)
print("---------FIN---------")

#------------------------------------------------------------------------------------------------------------------
#PARTE 7: DATAFRAME DE AUDITORIO TELMEX A MYSQL
try:
    # Crear una conexión a la base de datos MySQL utilizando SQLAlchemy
    engine = create_engine("mysql+mysqlconnector://root:@localhost:3306/EventosAuditorioTelmex")
    print("Conexión exitosa a la base de datos")

    # Guardar AudiotorioTelmex en la base de datos a través de SQLAlchemy
    df_final.to_sql(name='eventos', con=engine, if_exists='replace', index=False)
    

except Exception as e:
    # Si hay un error en la conexión o en la operación, imprimirá el mensaje de error
    print("Error al conectar a la base de datos:", e)
            
            
            
