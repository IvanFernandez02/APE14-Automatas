from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TokenType(str, Enum):
    VAR = "VAR"
    NUMBER = "NUMBER"
    OP_SUMA = "OP_SUMA"
    OP_RESTA = "OP_RESTA"
    OP_MULT = "OP_MULT"
    OP_DIV = "OP_DIV"
    OP_ASIGNACION = "OP_ASIGNACION"
    POWER = "POWER"
    UNKNOWN = "UNKNOWN"


class TokenSource(str, Enum):
    AFD = "AFD"
    LLM = "LLM"


@dataclass
class Token:
    tipo: TokenType
    valor: str
    fuente: TokenSource
    pos: int = 0
    tiempo_ms: float = 0.0


@dataclass
class CompilerError:
    fase: str
    token: str
    causa: str
    sugerencia: str
    posicion: int = 0


@dataclass
class FactorNode:
    tipo: str
    valor: str
    coeficiente: int = 1
    exponente: int = 1


@dataclass
class TermNode:
    signo: str = "+"
    factores: list[FactorNode] = field(default_factory=list)


@dataclass
class ExpressionNode:
    terminos: list[TermNode] = field(default_factory=list)


@dataclass
class EquationNode:
    izquierda: ExpressionNode
    derecha: ExpressionNode


@dataclass
class CompilerResult:
    entrada: str
    tokens: list[Token] = field(default_factory=list)
    ast: Optional[EquationNode] = None
    pasos_solucion: list[str] = field(default_factory=list)
    errors: list[CompilerError] = field(default_factory=list)
    tiempo_total_ms: float = 0.0
    tiempo_lexer_ms: float = 0.0
    tiempo_parser_ms: float = 0.0
    tiempo_semantic_ms: float = 0.0
    tiempo_llm_ms: float = 0.0
