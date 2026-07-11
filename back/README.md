# APE 012 — Compilador Ecuaciones de Primer Grado
**UNL · Teoría de Autómatas y Computabilidad Avanzada · 6to Ciclo**

Analizador léxico híbrido: AFD (expresiones regulares) + LLM (Ollama local).

---

## Requisitos previos
- Python 3.10+
- [Ollama](https://ollama.com) instalado y corriendo con llama3.2:3b:
  ```bash
  ollama pull llama3.2:3b
  ollama serve          # en otra terminal si no corre como servicio
  ```

---

## Instalación

```bash
# 1. Clonar / copiar el proyecto
cd compilador_ecuaciones

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

---

## Ejecución

```bash
# Desde la raíz del proyecto (compilador_ecuaciones/)
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva: http://localhost:8000/docs

---

## Endpoints

| Método | URL             | Descripción                        |
|--------|-----------------|------------------------------------|
| GET    | /               | Info de la API                     |
| GET    | /lexer/health   | Health check                       |
| POST   | /lexer/analyze  | Analizar una ecuación               |

---

## Prueba con Insomnia

### POST /lexer/analyze

**URL:** `http://localhost:8000/lexer/analyze`  
**Method:** POST  
**Body → JSON:**

```json
{ "entrada": "2x más 5 es igual a 13" }
```

**Prueba 2:**
```json
{ "entrada": "3y menos 7 es igual a 2" }
```

Respuesta esperada con error léxico:

```json
{
  "entrada": "3y menos 7 es igual a 2",
  "tokens": [],
  "errors": [
    {
      "token": "3y",
      "cause": "La variable no es válida para esta ecuación.",
      "suggestion": "Utilice x."
    }
  ]
}
```

**Prueba 3:**
```json
{ "entrada": "x más 10 es igual a 4x menos 2" }
```

### GET /lexer/health

**URL:** `http://localhost:8000/lexer/health`  
**Method:** GET

---

## Arquitectura Clean Architecture

```
compilador_ecuaciones/
└── app/
    ├── core.py      ← Entidades, puertos y caso de uso
    ├── adapters.py  ← Router FastAPI, schemas y adaptadores externos
    └── main.py      ← Punto de entrada de FastAPI
```

**Flujo:**
1. Insomnia → POST /lexer/analyze
2. FastAPI Router → LexicalAnalyzerUseCase
3. Use case → RegexLexerAdapter (AFD, < 1ms)
4. Use case → OllamaLLMAdapter × N hilos (ThreadPoolExecutor)
5. Resultado ensamblado → JSON response
