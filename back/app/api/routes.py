# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException

from .schemas import AnalyzeRequest, AnalyzeResponse, TokenResponse, CompilerErrorResponse, ModelsResponse
from ..application.compiler import CompilerUseCase
from ..infrastructure.lexer import RegexLexer
from ..infrastructure.parser import EquationParser
from ..infrastructure.semantic import SemanticAnalyzer
from ..infrastructure.llm import create_llm, list_ollama_models

router = APIRouter(prefix="/compiler", tags=["Compilador"])


def _ast_to_dict(ast):
    if ast is None:
        return None
    return {
        "tipo": "ecuacion",
        "izquierda": {
            "terminos": [
                {
                    "signo": t.signo,
                    "factores": [
                        {
                            "tipo": f.tipo,
                            "valor": f.valor,
                            "coeficiente": f.coeficiente,
                            "exponente": f.exponente,
                        }
                        for f in t.factores
                    ],
                }
                for t in ast.izquierda.terminos
            ],
        },
        "derecha": {
            "terminos": [
                {
                    "signo": t.signo,
                    "factores": [
                        {
                            "tipo": f.tipo,
                            "valor": f.valor,
                            "coeficiente": f.coeficiente,
                            "exponente": f.exponente,
                        }
                        for f in t.factores
                    ],
                }
                for t in ast.derecha.terminos
            ],
        },
    }


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(body: AnalyzeRequest):
    try:
        llm = create_llm(body.modelo_llm)
        use_case = CompilerUseCase(
            lexer=RegexLexer(),
            parser=EquationParser(),
            semantic=SemanticAnalyzer(),
            llm=llm,
        )
        result = use_case.analizar(body.entrada)

        return AnalyzeResponse(
            entrada=result.entrada,
            tokens=[
                TokenResponse(tipo=t.tipo.value, valor=t.valor, fuente=t.fuente.value)
                for t in result.tokens
            ],
            errores=[
                CompilerErrorResponse(
                    fase=e.fase, token=e.token,
                    causa=e.causa, sugerencia=e.sugerencia,
                )
                for e in result.errors
            ],
            arbol_sintactico=_ast_to_dict(result.ast),
            pasos_solucion=result.pasos_solucion,
            tiempos={
                "total_ms": round(result.tiempo_total_ms, 3),
                "lexer_ms": round(result.tiempo_lexer_ms, 3),
                "parser_ms": round(result.tiempo_parser_ms, 3),
                "semantic_ms": round(result.tiempo_semantic_ms, 3),
                "llm_ms": round(result.tiempo_llm_ms, 3),
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health")
def health():
    return {"status": "ok", "servicio": "Compilador Ecuaciones - APE 012"}


@router.get("/models", response_model=ModelsResponse)
def models():
    try:
        return ModelsResponse(modelos=list_ollama_models())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo listar modelos de Ollama: {exc}")
