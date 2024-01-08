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
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime


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
            anio_actual = str(datetime.datetime.now().year)
            fecha_hora = anio_actual+fecha_hora
            fecha_hora_obj = parser.parse(fecha_hora, dayfirst=True, fuzzy=True)
            return fecha_hora_obj.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return fecha_hora  # Mantén la casilla original si no se pudo analizar la fecha y hora
    else:
        return fecha_hora


#------------------------------------------------------------------------------------------------------------------
#PARTE 1: DESCARGAR IMAGENES CHICAS
logos = soup.find_all(class_='imgLogo')
txtLogos = soup.find_all(class_='txtLogo')

# Crear una lista para almacenar los datos
data = []
ruta_actual = os.getcwd()
carpeta_imagenes = 'imagenes_chicas'
ruta_completa = os.path.join(ruta_actual, carpeta_imagenes)
if not os.path.exists(ruta_completa):
    os.makedirs(ruta_completa)
for count, (logo, txtLogo) in enumerate(zip(logos, txtLogos), start=1):
    # Encuentra la etiqueta de imagen dentro del enlace y obtén el atributo "src"
    imagen = logo.find('img')
    if imagen:
        imagen_url_rel = imagen['src']  # URL relativa de la imagen
        imagen_url_abs = urljoin(url, imagen_url_rel)# URL completa
        try:
            imagen_response = requests.get(imagen_url_abs)
            if imagen_response.status_code == 200:
                nombre_archivo = f"imagen_chica{count}.jpg"
                ruta_de_guardado = os.path.join(ruta_completa, nombre_archivo)
                with open(ruta_de_guardado, "wb") as archivo:
                    archivo.write(imagen_response.content)

                texto_txtLogo = [texto.strip() for texto in txtLogo.strings if texto.strip()]
                data_dict = {'Nombre de Archivo': ruta_de_guardado}
                for i, texto in enumerate(texto_txtLogo):
                    data_dict[f'Texto_txtLogo{i + 1}'] = texto.strip()
                data.append(data_dict)
            
            else:
                print(f"Error al descargar la imagen {imagen_url_abs}. Código de estado: {imagen_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error al realizar la solicitud HTTP para la imagen {imagen_url_abs}: {str(e)}")

# Crear un DataFrame de Pandas con los datos
df = pd.DataFrame(data)
dfImagenesChicas = df.iloc[:, :1]
dfImagenesChicas.insert(loc=0, column='pertenece', value='2')
dfImagenesChicas = dfImagenesChicas.rename(columns={dfImagenesChicas.columns[0]: 'pertenece'})
dfImagenesChicas = dfImagenesChicas.rename(columns={dfImagenesChicas.columns[1]: 'ImagenURL'})
# Guardar el DataFrame en un archivo CSV


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

#EXTRAER INFORMACIÓN DEL URL
cuadro = soup.find_all(class_='cuadro')
infoEvento = soup.find_all(class_='infoEvento efecto')
fondo = soup.find_all(class_='fondo')
informacion = soup.find_all(class_='informacion')
info_tit = soup.find_all(class_='infoTit')
info_txt = soup.find_all(class_='infoTxt')#.get_text(separator='\n', strip=True)

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
        #'Fondo': fondo[i].text.strip(),
        'Informacion': informacion[i].text.strip(),
        'InfoTit': info_tit[i].text.strip(),
        'fechas': info_txt[i].get_text(separator='\n', strip=True)#.text.strip()
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
#PARTE 3: DESCARGAR IMAGENES MEDIANAS
count = 1
data=[]
ruta_actual = os.getcwd()
carpeta_imagenes = 'imagenes_medianas'
ruta_completa = os.path.join(ruta_actual, carpeta_imagenes)
if not os.path.exists(ruta_completa):
    os.makedirs(ruta_completa)
ruta_completa = os.path.join(ruta_actual, carpeta_imagenes)
for imagen in imagenes:
    imagen_url_rel = imagen['src']  # URL relativa de la imagen
    if ("imagen_mediana.jpg" in imagen_url_rel) or ("imagen_mediana.png" in imagen_url_rel):
        # Construye la URL completa utilizando urljoin
        imagen_url_abs = urljoin(url, imagen_url_rel)
        imagen_response = requests.get(imagen_url_abs)
        if imagen_response.status_code == 200:
            # Obtén el nombre del archivo de la URL
            nombre_archivo = f'imagen_mediana_{count}.jpg'
            ruta_de_guardado = os.path.join(ruta_completa, nombre_archivo)
            with open(ruta_de_guardado, 'wb') as archivo:
                archivo.write(imagen_response.content)
            data.append(ruta_de_guardado)
            count += 1
        else:
            print(f'Error al descargar la imagen {imagen_url_abs}. Código de estado: {imagen_response.status_code}')

dfImagenesMedianas = pd.DataFrame(data)
dfImagenesMedianas.insert(loc=0, column='pertenece', value='2')
dfImagenesMedianas = dfImagenesMedianas.rename(columns={dfImagenesMedianas.columns[0]: 'pertenece'})
dfImagenesMedianas = dfImagenesMedianas.rename(columns={dfImagenesMedianas.columns[1]: 'ImagenURL'})

#------------------------------------------------------------------------------------------------------------------
#PARTE 4: DESCARGAR IMAGENES GRANDES y obtener enlaces de compra (es el mismo para todos)
# Obtén los enlaces de eventos
count = 1
data_img=[]
ruta_actual = os.getcwd()
carpeta_imagenes = 'imagenes_grandes'
ruta_completa = os.path.join(ruta_actual, carpeta_imagenes)
if not os.path.exists(ruta_completa):
    os.makedirs(ruta_completa)
ruta_completa = os.path.join(ruta_actual, carpeta_imagenes)
event_links = [href for href in enlaces_href if "evento.php" in href]
data = []

for event_link in event_links:
    event_url_abs = urljoin(url, event_link)
    event_response = requests.get(event_url_abs)
    if event_response.status_code == 200:
        event_soup = BeautifulSoup(event_response.content, 'html.parser')
        imagen_grande = event_soup.find('img', src=lambda x: x and 'imagen_grande' in x)
        enlaces = event_soup.find_all('a', href=True)
        diccionario={}
        for enlace in enlaces:
            href = enlace['href']
            if href and 'www.ticketmaster.com.mx/venue' in href:#OJO! es el mismo enlace para todas las obras
                diccionario['enlaces'] = href    
                #data.append(href)
                break
        sinopsis = event_soup.find(class_='txtInfo')
        diccionario['Sinopsis'] = sinopsis.text
        
        diccionario['Precios'] = []
        precios = event_soup.find(class_='precios').find_all('li')
        precios = [item.get_text(strip=True) for item in precios]
        precios_aux=""
        for precio in precios:
            precios_aux = precios_aux + precio + "\n"
        diccionario['Precios'] = precios_aux
        data.append(diccionario)
 
        #a descargar las imagenes
        if imagen_grande:
            imagen_grande_url_rel = imagen_grande['src']
            imagen_grande_url_abs = urljoin(event_url_abs, imagen_grande_url_rel)
            imagen_grande_response = requests.get(imagen_grande_url_abs)

            if imagen_grande_response.status_code == 200:
                nombre_archivo = f'imagen_grande_{count}.jpg'
                ruta_de_guardado = os.path.join(ruta_completa, nombre_archivo)
                with open(ruta_de_guardado, 'wb') as archivo:
                    archivo.write(imagen_grande_response.content)
                data_img.append(ruta_de_guardado)
                count += 1
            else:
                print(f'Error al descargar la imagen {imagen_grande_url_abs}. Código de estado: {imagen_grande_response.status_code}')
    
    else:
        print(f'Error al acceder a la página del evento {event_url_abs}. Código de estado: {event_response.status_code}')
df3 = pd.DataFrame(data)#, columns=["enlaces"])
dfImagenesGrandes = pd.DataFrame(data_img)
dfImagenesGrandes.insert(loc=0, column='pertenece', value='2')
dfImagenesGrandes = dfImagenesGrandes.rename(columns={dfImagenesGrandes.columns[0]: 'pertenece'})
dfImagenesGrandes = dfImagenesGrandes.rename(columns={dfImagenesGrandes.columns[1]: 'ImagenURL'})

#------------------------------------------------------------------------------------------------------------------
#PARTE 5: EXTRAER INFORMACIÓN DE LOS BOLETOS
#ATENCION: resumen del problema, la pagina del auditorio pone muchos impedimentos por alerta de robot
'''
url2 = enlaces_a_comprar[1]#TODOS LOS ENLACES DE LA LISTA SON IGUALES, ASI QUE DA IGUAL CUAL TOMEMOS
print("Nuevo URL:", url2)
# Iniciar un navegador web, esto porque Beautiful Soup no puede
driver = webdriver.Chrome()

# Abrir la página web
driver.get(url2)

#OJO: aquí sucede algo extraño que no pasaba antes. Dentro del try se rechazan o aceptan las cookies (eso no cambia el resultado final)
#Posteriormente, el try falla, sin presionar el botón que permite ver todas las obras, así que hago un segundo intento de presionarlo en el except
#Lo malo es que, parece que el navegador detecta este codigo como un robot, de forma que, aunque se presiona el botón, no se ejecuta su acción
#En consecuencia, no se puede obtener el enlace de cada obra individual para el auditorio telmex
try:
    time.sleep(5)
    cookies = WebDriverWait(driver, 10).until(
        #EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[id="onetrust-accept-btn-handler"]'))#aceptar
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[id="onetrust-reject-all-handler"]'))#rechazar
    )
    cookies.click()
    print("cookies aceptadas o rechazadas")
    time.sleep(5)
    boton = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="pagination-button"]'))
    )
    boton.click()

except Exception as e:
    boton = driver.find_element('css selector', 'button[data-testid="pagination-button"]')
    boton.click()
    #print("ERROR:", e)

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
        #for boleto in boletos:
            #print(boleto)
            #pass
       
        #for precio in precios:
            #print(precio)
            #pass
    else:
        print(f"Error al acceder al enlace. Código de estado: {response.status_code}")
'''

#------------------------------------------------------------------------------------------------------------------
#PARTE 6: UNIR LOS DATAFRAME EN UNO SOLO, LUEGO PASARLO COMO ARCHIVO CSV

#df2 = pd.read_csv('datos.csv')
# Combinar los DataFrames verticalmente (uno debajo del otro)
df_combined = pd.concat([df, df2], axis=1)

#df4 = pd.DataFrame(enlaces_ticketmaster2)
#df_combined2= pd.concat([df3, df4], axis=1)
#df_combined2=df3
df_final=pd.concat([df_combined, df3], axis=1)
#df_combined = df_combined.append(datos,ignore_index=True)
#df_combined = df_combined.append(enlaces_ticketmaster2,ignore_index=True)

# Opcionalmente, puedes restablecer los índices si lo deseas
#df_combined.reset_index(drop=True, inplace=True)
df_final.to_csv('CarteleraTelmex.csv', index=False)

#Dataframe imagnes chicas
dfImagenesChicas.to_csv('Imagenes_Chicas.csv', index=False)
#Dataframe imagnes medianas
dfImagenesMedianas.to_csv('Imagenes_Medianas.csv', index=False)
#Dataframe imagnes grandes
dfImagenesGrandes.to_csv('Imagenes_Grandes.csv', index=False)

#Dataframe fechas
dfFechas = pd.DataFrame(columns=["pertenece", "fecha", "boleto"])
lista_aux=df_final["fechas"]
nueva_lista = [item for sublist in [elemento.split('\n') for elemento in lista_aux] for item in sublist]
dfFechas["fecha"] = nueva_lista
dfFechas['fecha'] = dfFechas['fecha'].apply(convertir_fecha_hora)
dfFechas["pertenece"] = 2
aux = df_final.loc[0,"enlaces"]
dfFechas["boleto"] = aux
dfFechas.to_csv("fechas.csv", index=False)
#Dataframe eventos presenciales
dfEventoPresencial = pd.DataFrame(columns=["status", "solicitaEvento", "nombreEvento", "subtituloEvento", "areaProgramadora", "categoria",
                                  "subGenero", "grupoActividad", "sedeUniversitaria","foro", "duracion", "sinopsis", "enlaceVideo", 
                                  "evento", "temporada", "costoBoleto", "eventoActivo", "dat", "TS", "evento_especial", "otroGenero",
                                  "tipo_evento"])
dfEventoPresencial["nombreEvento"] = df["Texto_txtLogo1"]
dfEventoPresencial["sinopsis"] = df_final["Sinopsis"]
dfEventoPresencial["costoBoleto"] = df_final["Precios"]
dfEventoPresencial.to_csv("eventopresencial.csv", index=False)

'''
#------------------------------------------------------------------------------------------------------------------
#PARTE 7: DATAFRAMES DE AUDITORIO TELMEX A MYSQL
try:
    # Crear una conexión a la base de datos MySQL utilizando SQLAlchemy
    engine = create_engine("mysql+mysqlconnector://root:@localhost:3306/EventosAuditorioTelmex")
    print("Conexión exitosa a la base de datos")

    # Guardar AudiotorioTelmex en la base de datos a través de SQLAlchemy
    df_final.to_sql(name='eventos', con=engine, if_exists='replace', index=False)
    

except Exception as e:
    # Si hay un error en la conexión o en la operación, imprimirá el mensaje de error
    print("Error al conectar a la base de datos:", e)
'''      
     
