# compilador_ecuaciones

Estructura del proyecto:

- `back/`: backend FastAPI y lógica del compilador.
- `front/`: frontend Angular.

## Backend

Para ejecutar el backend:

```bash
cd back
source ../venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Frontend

El frontend Angular quedó inicializado en `front/`.

```bash
cd front
npm install
npm start
```

## Notas

- El frontend fue creado con Angular CLI en modo standalone, con routing y SCSS.
- Si quieres conectar el frontend al backend, el siguiente paso es definir servicios HTTP en Angular para consumir los endpoints de FastAPI.
