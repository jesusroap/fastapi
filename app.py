# app.py
from typing import Union

from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI()

# Crear una instancia de APIRouter
router = APIRouter()

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

# Configuración FTP del servidor externo
ftp_host = config("FTP_HOST")
ftp_usuario = config("FTP_USER")
ftp_contrasena = config("FTP_PASS")

# Configuración de la conexión a la base de datos MySQL
DATABASE_URL = config("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = automap_base()
Base.prepare(engine, reflect=True)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/auth/login")
async def login(user: UserDTO):
    token = {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Ik5pY2sgSm9uZXMiLCJwaWN0dXJlIjoiYXNzZXRzL2ltYWdlcy9uaWNrLnBuZyIsImVtYWlsIjoibmlja19qb25lc0BnbWFpbC5jb20iLCJpYXQiOjE1MTYyMzkwMjJ9.fTAK9gUtjoVwMYgznqTN9-6uXFMjedncCXSYtDLeZZE"}
    return token

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}

@app.post("/subir_archivo/")
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

@app.get("/user_catalog/")
async def get_user_catalog(email: str):
    user = Base.classes.users
    family = Base.classes.familys
    product = Base.classes.products
    family_product = Base.classes.familyproducts

    # Crear una sesión de base de datos
    db = SessionLocal()

    # Consulta SQL para obtener el catálogo del usuario
    stmt = (
        select(
            user.email,
            family.name.label('family'),
            product.name.label('name'),
            product.namefile,
            product.price
        )
        .select_from(
            join(family_product, family, family.id == family_product.family_id)
            .join(product, family_product.producto_id == product.id)
            .join(user, family.user_id == user.id)
        )
        .where(user.email == email)
    )

    result = db.execute(stmt)

    # Organizar los resultados en la estructura JSON requerida
    catalog = {}
    for row in result:
        family_name = row[1]
        product_data = {
            "name": row[2],
            "image": row[3],
            "price": row[4]
        }

        if family_name not in catalog:
            catalog[family_name] = {"family": family_name, "products": []}

        catalog[family_name]["products"].append(product_data)

    user_data = {"user": email, "catalog": list(catalog.values())}

    db.close()

    return user_data