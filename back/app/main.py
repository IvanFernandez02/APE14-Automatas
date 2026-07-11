# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as compiler_router

app = FastAPI(
    title="Compilador Ecuaciones — APE 012",
    description=(
        "Analizador léxico, sintáctico y semántico para ecuaciones de primer grado. "
        "Híbrido: AFD (expresiones regulares) + LLM (Ollama local). "
        "UNL — Teoría de Autómatas 2026."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compiler_router)


@app.get("/")
def root():
    return {
        "mensaje": "API activa. Visita /docs para la documentación interactiva.",
        "endpoints": {
            "analyze": "POST /compiler/analyze",
            "health": "GET  /compiler/health",
            "docs": "GET  /docs",
        },
    }
