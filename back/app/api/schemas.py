from typing import Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    entrada: str = Field(
        ..., min_length=1,
        examples=["2x más 5 es igual a 13"],
    )
    modelo_llm: str = Field(
        default="llama3.2:3b",
        description="Nombre del modelo local de Ollama, por ejemplo: llama3.2:3b",
    )


class TokenResponse(BaseModel):
    tipo: str
    valor: str
    fuente: str


class CompilerErrorResponse(BaseModel):
    fase: str
    token: str
    causa: str
    sugerencia: str


class AnalyzeResponse(BaseModel):
    entrada: str
    tokens: list[TokenResponse]
    errores: list[CompilerErrorResponse]
    arbol_sintactico: Optional[dict] = None
    pasos_solucion: list[str] = []
    tiempos: dict


class ModelsResponse(BaseModel):
    modelos: list[str]
