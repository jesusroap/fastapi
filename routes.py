from fastapi import APIRouter

router = APIRouter()

@router.get("/servicio1")
def servicio_uno():
    return {"message": "Este es el servicio 1"}

@router.get("/servicio2")
def servicio_dos():
    return {"message": "Este es el servicio 2"}