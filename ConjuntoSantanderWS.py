"""
Created on Thu Sep 28 10:25:38 2023

@author: carlossalcidoa
"""
from bs4 import BeautifulSoup
import requests
import os
from urllib.parse import urljoin
import pandas as pd
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from sqlalchemy import create_engine
from dateutil import parser

#------------------------------------------------------------------------------------------------------------------
#PARTE 0: Declarar todo lo necesario
driver = webdriver.Chrome()
url = 'https://www.conjuntosantander.com/'  # URL DEL CONJUNTO SANTANDER
response = requests.get(url)
if response.status_code == 200:
    page_content = response.content
    print("Se accedió a la página")
else:
    print("Error al acceder a la página.")
soup = BeautifulSoup(page_content, 'html.parser')

meses = {#----------------------------------------------------------------------
    'ene': 'jan',
    'feb': 'feb',
    'mar': 'mar',
    'abr': 'apr',
    'may': 'may',
    'jun': 'jun',
    'jul': 'jul',
    'ago': 'aug',
    'sep': 'sep',
    'oct': 'oct',
    'nov': 'nov',
    'dic': 'dec'
}

def eliminar_contenido_si_hay_guion(celda):#----------------------------------------
    if '-' in str(celda):
        return ''
    else:
        return celda


# Define una función para convertir fechas al formato deseado
def convertir_fecha(fecha):#------------------------------------------------------------
    if ' y ' in fecha:
        return fecha
    if fecha == '':
        return fecha  # Mantén la casilla vacía si está vacía    
    for abreviatura, nombre_mes in meses.items():
       fecha = fecha.replace(abreviatura, nombre_mes)
    try:
        fecha_obj = parser.parse(fecha, dayfirst=True, fuzzy=True)
        return fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return fecha  # Mantén la casilla original si no se pudo analizar la fecha


def convertir_fechas(fila):#------------------------------------------------------------
    if '/' in fila:
        # Dividir la fila en las dos fechas
        fechas = fila.split(' / ')
        fecha1 = convertir_fecha(fechas[0])
        fecha2 = convertir_fecha(fechas[1])
        return f"{fecha1} / {fecha2}"
    else:
        # Mantener la fila original sin cambios si no contiene '/'
        return fila


data = []  # LA LISTA DATA ALMACENA LOS DATOS
# ENCONTRAR LOS ELEMENTOS QUE BUSCAMOS DENTRO DEL CONTENEDOR
artistas = soup.find_all(class_="txtGris font-12 mb-0 ipad-title")
fechas = soup.find_all(class_="mb-0 txtGris ipad-txt font-12")
salas = soup.find_all(class_="mb-0 txtGris font-12 ipad-txt")

imagenes = soup.find_all('img')#Encontrar todos los elementos img
enlaces = soup.find_all('a', href=lambda href: href and 'https://www.conjuntosantander.com/evento/' in href)
# Verificar que todas las listas tengan la misma longitud
if len(artistas) == len(fechas) == len(salas):
    for i in range(len(artistas)):
        data.append({
            'Titulo_bien': artistas[i].text.strip(),
            'Fecha': fechas[i].text.strip(),
            'Sala': salas[i].text.strip()
        })
else:
    print("Las listas no tienen la misma longitud. No se puede crear el DataFrame.")

# HACER UN DATAFRAME Y PONERLE LOS DATOS DE LA LISTA DATA[]
df = pd.DataFrame(data)




#------------------------------------------------------------------------------------------------------------------
#PARTE 1: Descargar imágenes
ruta_actual = os.getcwd()
carpeta_imagenes = 'imagenes_santander'
ruta_completa = os.path.join(ruta_actual, carpeta_imagenes)
if not os.path.exists(ruta_completa):
    os.makedirs(ruta_completa)
dfImagenes = pd.DataFrame()
imagenes_descargadas=[]
count = 1
for imagen in imagenes:
    imagen_url_rel = imagen['src']  # URL relativa de la imagen
    if "https://www.conjuntosantander.com/assets/eventos" in imagen_url_rel:
        imagen_url_abs = urljoin(url, imagen_url_rel)
        imagen_response = requests.get(imagen_url_abs)

        if imagen_response.status_code == 200:
            #nombre_archivo = f'imagen_{count}.jpg'
            nombre_archivo = os.path.join(ruta_completa, f'imagen_{count}.jpg')
            with open(nombre_archivo, 'wb') as archivo:
                archivo.write(imagen_response.content)
            #print(f'La imagen {nombre_archivo} ha sido descargada con éxito.')
            imagenes_descargadas.append(nombre_archivo)
            count += 1
        else:
            print(f'Error al descargar la imagen {imagen_url_abs}. Código de estado: {imagen_response.status_code}')
dfImagenes= pd.DataFrame(imagenes_descargadas)
dfImagenes = dfImagenes.rename(columns={df.columns[0]: 'imagenURL'})
dfImagenes.insert(0, 'pertenece', 86)


#------------------------------------------------------------------------------------------------------------------
#PARTE 2: ACCEDER A LOS DATOS DE LOS ENLACES
# Crear una lista para almacenar los datos de los enlaces
datos_enlaces = []
enlaces_compra = []
# Iterar a través de los enlaces
enlaces_procesados = set()
count = 1
for enlace in enlaces:
    # Obtener el atributo 'href' del enlace
    href = enlace.get('href')
    # Verificar si el enlace ya ha sido procesado
    if href in enlaces_procesados:
        continue  # Saltar el procesamiento de enlaces duplicados
    # Agregar el enlace al conjunto de enlaces procesados
    enlaces_procesados.add(href)
    #print(f'enlace{count}: {href}')
    count += 1
    # Realizar una solicitud HTTP al enlace para obtener información adicional
    enlace_completo = urljoin(url, href)  # Utilizar urljoin para construir la URL completa
    response_enlace = requests.get(enlace_completo)

    if response_enlace.status_code == 200:
        pagina_enlace = response_enlace.content
        soup_enlace = BeautifulSoup(pagina_enlace, 'html.parser')

        # ESTO ES LO QUE VAMOS A EXTRAER
        titulo = soup_enlace.find(class_="txtGris mb-10 font-20").text.strip()
        sala2 = soup_enlace.find(class_="icon-map-marker")
        sala2=sala2.parent.text.strip()
        fecha2 = soup_enlace.find(class_="icon-calendar3")
        fecha2 = fecha2.parent.text.strip()
        try:
            precio = soup_enlace.find(class_="icon-dollar")
            precio = precio.parent.text.strip()
        except:
            precio = "No disponible"
        #nota = soup_enlace.find(class_="cargo mb-10") 
        enlace_compra = soup_enlace.find('a', href=lambda href: href and 'boletos' in href)
        enlace_compra = enlace_compra.get('href')
        enlaces_compra.append(enlace_compra)
        #print("Enlace de compra: ",enlace_compra,"\n")        
        
        # Agregar los datos del enlace a la lista
        datos_enlaces.append({
            'Enlace': enlace_completo,
            'Título': titulo,
            'Sala': sala2,
            'Fecha': fecha2,
            'Precio': precio
            #'Nota': nota
        })

df_enlaces = pd.DataFrame(datos_enlaces)





#------------------------------------------------------------------------------------------------------------------
#PARTE 3: OBTENER FECHAS, HORARIOS Y ENLACES DE BOLETOS
#print("------ComprarBoletos------")

# Inicializa listas para almacenar la información de los enlaces de compra
fechas_lista = []
horarios_lista = []
enlaces_boletos_lista = []
max_fechas_por_enlace = 6
max_enlaces_por_evento = 6
eventos_data = []
eventos_data2 = []
''''''

count = 1
for enlace in enlaces_compra:
    responseC = requests.get(enlace)
    enlace = responseC.url
    driver.get(enlace)
    
    try:
    # Espera hasta que cierto elemento esté presente en la página
        elemento = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'buy-tickets'))
    )
        try:#AQUI INTENTAMOS OBTENER EL ENLACE DE COMPRA------------------------
            # Encuentra el elemento <a> con la clase "enlace-especifico"
            enlaces_disponibles = driver.find_elements(By.CLASS_NAME, "buy-tickets")
            # Inicializar una lista para almacenar los enlaces de este evento
            enlaces_enlace = []
            for enlace_element in enlaces_disponibles:
                url = enlace_element.get_attribute("href")
                enlaces_enlace.append(url)
                
            # Crear un diccionario para almacenar la información de este evento
            evento_data = {}
            # Agregar los enlaces a este evento
            for i in range(len(enlaces_enlace)):
                if len(enlaces_enlace) > i:
                    evento_data[f'Enlace_Fecha{i + 1}'] = enlaces_enlace[i]
                else:
                    evento_data[f'Enlace_Fecha{i + 1}'] = ""
            
            # Agregar este evento a la lista principal
            eventos_data.append(evento_data)
            
        except:
            evento_data = {
                'Enlace de Compra': "Boletos agotados"
            }
            for i in range(1):
                evento_data[f'Enlace_{i + 1}'] = ""
            eventos_data.append(evento_data)
            print("Boletos agotados\n")
            
        try:#AQUI INTENTAMOS OBTENER LA FECHA DE LA FUNCIÓN---------------------
            fechas_disponibles = driver.find_elements(By.CLASS_NAME, "pl-datetime") 
            #datetime = dt.text
            fechas_enlace = []

            for fecha_element in fechas_disponibles:
                fecha = fecha_element.text
                fechas_enlace.append(fecha)
                
            # Crear un diccionario para almacenar la información de este evento
            evento_data = {}
            # Agregar las fechas a este evento
            for i in range(len(fechas_enlace)):
                if len(fechas_enlace) > i:
                    evento_data[f'Fecha_{i + 1}'] = fechas_enlace[i]
                else:
                    evento_data[f'Fecha_{i + 1}'] = ""
    
            # Agregar este evento a la lista principal
            eventos_data2.append(evento_data)
                                    
        except:#----------------------------------------------------------------
            evento_data = {
                'Enlace de Boletos': "Boletos agotados"
            }
            for i in range(1):
                evento_data[f'Fecha_{i + 1}'] = ""
            eventos_data2.append(evento_data)
            print("Boletos agotados\n")
        
        
        
        #Imprime Datetime
        #print("Horario:",datetime)
        #fechas_lista.append(datetime)
        # Imprime la URL
        #print("URL del enlace:", url)
        enlaces_boletos_lista.append(url)
        #dfEventoPresencial["nombreEvento"] = df["Título"]
        #print("\n")
    
    except :
        evento_data = {}
        evento_data[f'Enlace_Fecha{1}'] = "Error"
        eventos_data.append(evento_data)
        
        evento_data = {}
        evento_data[f'Fecha_{1}'] = "Error"
        eventos_data2.append(evento_data)
        #datetime = "Boletos agotados"
        #url = "Boletos agotados"
        #print("Horario:",datetime)
        #fechas_lista.append(datetime)
        #print("URL del enlace:", url)
        #enlaces_boletos_lista.append(url)
        #print("\n")
    
    finally:
        #driver.quit()
        pass
#------------------------------------------------------------------------------------------------------------------
#PARTE 4: acomodar los dataframes   
df_enlaces_boletos= pd.DataFrame(eventos_data)
df_eventos = pd.DataFrame(eventos_data2)
df_temp=pd.concat([df_eventos,df_enlaces_boletos], axis=1)

# Crear un DataFrame solo con la columna de enlaces de boletos
#df_enlaces_boletos = pd.DataFrame({'Enlace de Boletos': enlaces_boletos_lista})

# Unir el DataFrame de información de enlaces con el DataFrame original
df_final = pd.concat([df, df_enlaces], axis=1)
df_final = pd.concat([df_final, df_temp], axis=1)

# Guardar el DataFrame final en un archivo CSV
df_final.to_csv('CarteleraConjuntoSantander.csv', index=False)
dfImagenes.to_csv('img_santander.csv', index=False)
dfEventoPresencial = pd.DataFrame(columns=["status", "solicitaEvento", "nombreEvento", "subtituloEvento", "areaProgramadora", "categoria",
                                  "subGenero", "grupoActividad", "sedeUniversitaria","foro", "duracion", "sinopsis", "enlaceVideo", 
                                  "evento", "temporada", "costoBoleto", "eventoActivo", "dat", "TS", "evento_especial", "otroGenero",
                                  "tipo_evento"])

dfEventoPresencial["nombreEvento"] = df_final["Titulo_bien"]

#------------------------------------------------------------------------------------------------------------------
#PARTE 5: Conexión a MYSQL
'''
#DATAFRAME DE CONJUNTO SANTANDER A MYSQL
try:
    # Crear una conexión a la base de datos MySQL utilizando SQLAlchemy
    engine = create_engine("mysql+mysqlconnector://root:@localhost:3306/EventosConjuntoSantander")

    print("Conexión exitosa a la base de datos")

    # Guardar ConjuntoSantander en la base de datos a través de SQLAlchemy
    df_final.to_sql(name='eventos', con=engine, if_exists='replace', index=False)
    
    #Guardar AudiotorioTelmex en la base de datos

except Exception as e:
    # Si hay un error en la conexión o en la operación, imprimirá el mensaje de error
    print("Error al conectar a la base de datos:", e)
'''




