# Auth Controller
### Inicio de Sesión

>**Endpoint**: /auth/login

Input:

```json
{
    "email": "string",
    "password": "string"
}
```

Output *(JWT Encoded)*:

```json
{
    "token": "string",
}
```

Output *(JWT Decoded)*:

```json
{
    "success": "boolean",
    "message": "string",
    "result":
    {
        "name": "string",
        "picture": "string",
        "email": "Ejemplolandia"
    }
}
```

### Registro

>**Endpoint**: /auth/register

Input:

```json
{
    "email": "string",
    "password": "string",
    "fullName": "string",
    "confirmPassword": "string",
    "rolId": "string"
}
```

Output *(JWT Encoded)*:

```json
{
    "token": "string"
}
```

Output *(JWT Decoded)*

```json
{
    "success": "boolean",
    "message": "string",
    "result": {}
}
```

### Cierre de Sesión

>**Endpoint**: /auth/logout

Input:

```json
{
    "email": "string",
}
```

Output:

```json
{
    "success": "boolean",
    "message": "string",
    "result": {}
}
```

### Recuperación de Contraseña

>**Endpoint**: /auth/forgot-pass

Input:

```json
{
    "email": "string",
}
```

Output:

```json
{
    "success": "boolean",
    "message": "string",
    "result": {}
}
```

### Nueva Contraseña

>**Endpoint**: /auth/new-pass

Input:

```json
{
    "email": "string",
    "password": "string",
    "confirmPassword": "string"
}
```

Output:

```json
{
    "success": "boolean",
    "message": "string",
    "result": {}
}
```

# Admin Controller
### Cargar Archivo

>**Endpoint**: /admin/upload-file

Input:

```json
{
    "email": "string",
    "base64": "string",
    "fileName": "string",
    "familyId": 0,
    "productId": 0
}
```

Output:

```json
{
    "success": "boolean",
    "message": "string",
    "result": {}
}
```

### Descargar Archivo

>**Endpoint**: /admin/get-file

Input:

```json
{
    "email": "string",
    "fileName": "string",
}
```

Output:

```json
{
    "success": "boolean",
    "message": "string",
    "result": {
        "name": "string",
        "type": "string",
        "data": "string"
    }
}
```

### Eliminar Cuenta

>**Endpoint**: /admin/delete-account

Input:

```json
{
    "email": "string",
}
```

Output:

```json
{
    "success": "boolean",
    "message": "string",
    "result": {}
}
```

### Catálogo del Usuario

>**Endpoint**: /admin/get-user-catalog

Input:

```json
{
    "email": "string",
}
```

Output:

```json
{
    "success": "boolean",
    "message": "string",
    "result": {
        "user": "string",
        "catalog": [
            "family": "string",
            "products": [
                "name": "string",
                "image": "string",
                "price": 0
            ]
        ]
    }
}
```