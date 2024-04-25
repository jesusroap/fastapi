# app.py
from typing import Union

from fastapi import FastAPI, HTTPException, UploadFile, APIRouter, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import base64

from PIL import Image
from io import BytesIO
import os

from ftplib import FTP

from decouple import config

from sqlalchemy import create_engine, select, join
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
import mysql.connector

from routes import router

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from cryptography.fernet import Fernet

from jinja2 import Template

import httpx

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserDTO(BaseModel):
    email: str
    password: str

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None

class PayloadUploadFile(BaseModel):
    base64: str
    folder: str
    fileName: str

class UserPreferences(BaseModel):
    title: str
    name: str
    background_color: str
    font_color: str

# Configuración FTP del servidor externo
ftp_host = os.environ.get("FTP_HOST")
ftp_usuario = os.environ.get("FTP_USER")
ftp_contrasena = os.environ.get("FTP_PASS")

# Configuración de la conexión a la base de datos MySQL
# DATABASE_URL = config("DATABASE_URL")
# engine = create_engine(DATABASE_URL, pool_recycle=280, pool_pre_ping=True)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = automap_base()
# Base.prepare(engine, reflect=True)

# Configura los detalles del servidor de correo
smtp_server = os.environ.get("SMTP_SERVER")
smtp_port = os.environ.get("SMTP_PORT")
smtp_username = os.environ.get("SMTP_USERNAME")
smtp_password = os.environ.get("SMTP_PASS")

@app.get("/")
def read_root():
    return {"Hello": "World update 3"}

@app.delete("/auth/logout")
async def logout():
    return {
        "success": "true"
    }

@app.post("/auth/login")
async def login(user: UserDTO):
    # return {
    #     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Ik5pY2sgSm9uZXMiLCJwaWN0dXJlIjoiYXNzZXRzL2ltYWdlcy9uaWNrLnBuZyIsImVtYWlsIjoibmlja19qb25lc0BnbWFpbC5jb20iLCJpYXQiOjE1MTYyMzkwMjJ9.fTAK9gUtjoVwMYgznqTN9-6uXFMjedncCXSYtDLeZZE",
    #     "messages": "Has ingresado exitosamente.",
    # }

    # raise HTTPException(
    #     status_code=401,
    #     detail="Correo electrónico o contraseña incorrectos, inténtelo de nuevo."
    # )

    error_message = "Correo electrónico o contraseña incorrectos, inténtelo de nuevo."
    response_content = {"errors": error_message}
    return JSONResponse(content=response_content, status_code=401)
    

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}

@app.post("/subir_archivo/")
async def subir_archivo(file: UploadFile, folder: str):
    try:
        # Crear una conexión FTP
        with FTP(ftp_host) as ftp:
            # Iniciar sesión con las credenciales FTP
            ftp.login(user=ftp_usuario, passwd=ftp_contrasena)

            # Verificar si el directorio ya existe
            if folder not in ftp.nlst():
                # Si el directorio no existe, créalo
                ftp.mkd(folder)

            # Cambiar al directorio de destino en el servidor externo
            ftp.cwd(folder)

            # Leer el contenido del archivo en partes pequeñas y cargarlo por FTP
            with file.file as archivo:
                ftp.storbinary(f"STOR {file.filename}", archivo)

        return {"mensaje": f"El archivo '{file.filename}' se ha subido exitosamente al servidor FTP."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir el archivo: {str(e)}")

@app.post("/subir_archivo_base64/")
async def subir_archivo(payload: PayloadUploadFile):
    try:
        # Crear una conexión FTP
        with FTP(ftp_host) as ftp:
            # Iniciar sesión con las credenciales FTP
            ftp.login(user=ftp_usuario, passwd=ftp_contrasena)

            # Verificar si el directorio ya existe
            if payload.folder not in ftp.nlst():
                # Si el directorio no existe, créalo
                ftp.mkd(payload.folder)

            # Cambiar al directorio de destino en el servidor externo
            ftp.cwd(payload.folder)

            # Decodificar la cadena Base64 en datos binarios
            datos_binarios = base64.b64decode(payload.base64)

            # Leer el contenido del archivo en partes pequeñas y cargarlo por FTP
            with BytesIO(datos_binarios) as archivo:
                ftp.storbinary(f"STOR {payload.fileName}", archivo)

        return {"mensaje": f"El archivo '{payload.fileName}' se ha subido exitosamente al servidor FTP."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir el archivo: {str(e)}")
    
@app.get("/descargar_archivo/")
async def descargar_archivo(nombre_archivo: str, folder: str):
    try:
        # Crear una conexión FTP
        with FTP(ftp_host) as ftp:
            # Iniciar sesión con las credenciales FTP
            ftp.login(user=ftp_usuario, passwd=ftp_contrasena)

            ftp.cwd(folder)

            # Descargar el archivo desde el servidor FTP
            with open(nombre_archivo, "wb") as archivo_local:
                ftp.retrbinary(f"RETR {nombre_archivo}", archivo_local.write)
            
            # Leer el contenido del archivo descargado
            with open(nombre_archivo, "rb") as archivo_local:
                contenido = archivo_local.read()

        imagen = Image.open(BytesIO(contenido))
        imagen_base64 = base64.b64encode(contenido).decode("utf-8")

        # Eliminar el archivo después de leerlo
        os.remove(nombre_archivo)

        imagen_json = {
            "name": nombre_archivo,
            "type": Image.MIME[imagen.format],
            "data": imagen_base64
        }

        return imagen_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al descargar el archivo: {str(e)}")
    
@app.post("/eliminar_directorio/")
async def eliminar_directorio(nombre_directorio: str):
    try:
        # Crear una conexión FTP
        with FTP(ftp_host) as ftp:
            # Iniciar sesión con las credenciales FTP
            ftp.login(user=ftp_usuario, passwd=ftp_contrasena)

            # Cambiar al directorio que se va a eliminar
            ftp.cwd(nombre_directorio)

            # Listar archivos y subdirectorios en el directorio
            lista_archivos = []
            lista_new = []

            ftp.retrlines("LIST", lista_archivos.append)
            for linea in lista_archivos:
                if not (linea.startswith("d") and (linea.endswith(" .") or linea.endswith(" .."))):
                    # Si la línea no comienza con "d" o no termina con " ." o " ..", la agregamos
                    nombre_item = linea.split()[-1]
                    lista_new.append(nombre_item)                         

            # Eliminar archivos en el directorio
            for nombre_archivo in lista_new:
                ftp.delete(nombre_archivo)

            # Regresar al directorio padre
            ftp.cwd("..")

            # Eliminar el directorio actual
            ftp.rmd(nombre_directorio)

        return {"mensaje": f"Directorio '{nombre_directorio}' y su contenido eliminados exitosamente en el servidor FTP."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar directorio y su contenido: {str(e)}")

# @app.get("/user_catalog/")
# async def get_user_catalog(email: str):
#     try:
#         user = Base.classes.users
#         family = Base.classes.familys
#         product = Base.classes.products
#         family_product = Base.classes.familyproducts

#         # Crear una sesión de base de datos
#         db = SessionLocal()

#         # Consulta SQL para obtener el catálogo del usuario
#         stmt = (
#             select(
#                 user.email,
#                 family.name.label('family'),
#                 product.name.label('name'),
#                 product.namefile,
#                 product.price
#             )
#             .select_from(
#                 join(family_product, family, family.id == family_product.family_id)
#                 .join(product, family_product.producto_id == product.id)
#                 .join(user, family.user_id == user.id)
#             )
#             .where(user.email == email)
#         )

#         result = db.execute(stmt)

#         # Organizar los resultados en la estructura JSON requerida
#         catalog = {}
#         for row in result:
#             family_name = row[1]
#             product_data = {
#                 "name": row[2],
#                 "image": row[3],
#                 "price": row[4]
#             }

#             if family_name not in catalog:
#                 catalog[family_name] = {"family": family_name, "products": []}

#             catalog[family_name]["products"].append(product_data)

#         user_data = {"user": email, "catalog": list(catalog.values())}

#         db.close()

#         return user_data
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
app.include_router(router, prefix="/services", tags=["services"])

@app.post("/send-email/")
async def send_email(email_to: str, subject: str, message: str):
    # Crea un mensaje de correo electrónico
    msg = MIMEMultipart()
    msg["From"] = "contact@websmaker.co"
    msg["To"] = email_to
    msg["Subject"] = subject

    # Agrega el cuerpo del mensaje
    msg.attach(MIMEText(message, "plain"))

    try:
        # Conéctate al servidor SMTP
        server = smtplib.SMTP("websmaker.co", "465")
        # server = smtplib.SMTP_SSL(smtp_server, smtp_port) # Para enviar por SSL
        # server.starttls()  # Usar TLS (si estás usando SMTPS, elimina esta línea)
        server.login("contact@websmaker.co", "@te6x8%A8B")

        # Envía el correo electrónico
        server.sendmail("contact@websmaker.co", email_to, msg.as_string())

        # Cierra la conexión
        server.quit()

        return {"message": "Correo electrónico enviado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al enviar el correo electrónico: {str(e)}")
    

# clave_secreta = Fernet.generate_key()
clave_secreta = os.environ.get('KEY_SECRET_AES')
clave_secreta = clave_secreta.encode("utf-8")
fernet = Fernet(clave_secreta)

@app.post("/encrypt/")
async def encriptar_datos(datos_a_encriptar: str):
    datos_a_encriptar_bytes = datos_a_encriptar.encode()
    datos_encriptados = fernet.encrypt(datos_a_encriptar_bytes)
    return {"datos_encriptados": datos_encriptados}

@app.post("/decrypt/")
async def desencriptar_datos(datos_encriptados: str):
    try:
        datos_desencriptados = fernet.decrypt(datos_encriptados.encode()).decode()
        return {"datos_desencriptados": datos_desencriptados}
    except Exception as e:
        return {"error": "No se pudo desencriptar los datos."}

@app.post("/build_template")
async def build_template(user_prefs: UserPreferences, folder: str):
    # TODO: Primero guardar en DB, y posterior traer la data de DB y esa seria la nueva data (user_prefs)
    template_path = 'template.html'
    generator = CodeGenerator(template_path)
    generated_html = generator.generate_code(user_prefs)

    with FTP(ftp_host) as ftp:
        ftp.login(user=ftp_usuario, passwd=ftp_contrasena)

        if folder not in ftp.nlst():
            ftp.mkd(folder)

        ftp.cwd(folder)

        html_bytes = BytesIO(generated_html.encode('utf-8'))
        ftp.storbinary(f'STOR {"index.html"}', html_bytes)

    return 'El template se creo exitosamente.'


@app.post("/create_subdomain")
async def create_subdomain(domain: str = Form(...)):
    try:
        data_dns = {
            "data": "",
            "name": "",
            "ttl": 10800,
            "type": "A"
        }

        headers_dns = {
            "Content-Type": "application/json",
            "Authorization": ""
        }


        # Datos a enviar como form-data
        form_data_cpanel = {
            "domain": domain,
            "rootdomain": "websmaker.co",
            "canoff": "1",
            "disallowdot": "0",
            "dir": config('DIR_TEMPLATE')
        }

        # Encabezados para la solicitud al servicio externo
        headers = {
            "Content-Type": "multipart/form-data",
            "Authorization": config('AUTHORIZATION_CPANEL_API'),
        }

        # Realizar una solicitud POST al servicio externo
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://websmaker.co:2083/execute/SubDomain/addsubdomain",
                data=form_data,
                headers=headers,
            )

        # Verificar si la solicitud fue exitosa (código 200)
        if response.status_code == 200:
            # Devolver los datos del servicio externo como respuesta
            return response.json()
        else:
            # Levantar una excepción si la solicitud no fue exitosa
            raise HTTPException(status_code=response.status_code, detail="Error al crear el subdominio")

    except Exception as e:
        # Capturar cualquier error y devolverlo como una respuesta de error
        raise HTTPException(status_code=500, detail=str(e))
    

class CodeGenerator:
    def __init__(self, template_path):
        # Cargar la plantilla desde un archivo
        with open(f'templates/{template_path}', 'r') as file:
            self.template = Template(file.read())

    def generate_code(self, user_preferences):
        # Generar código utilizando la plantilla y las preferencias del usuario
        generated_code = self.template.render(user_preferences)
        return generated_code