from abc import ABC, abstractmethod
from typing import Optional
from .models import Token, CompilerError, EquationNode


class LexerPort(ABC):
    @abstractmethod
    def tokenizar(self, entrada: str) -> tuple[list[Token], list[CompilerError]]:
        ...


class ParserPort(ABC):
    @abstractmethod
    def parse(self, tokens: list[Token]) -> tuple[Optional[EquationNode], list[CompilerError]]:
        ...


class SemanticPort(ABC):
    @abstractmethod
    def validate(self, ast: Optional[EquationNode], tokens: list[Token]) -> list[CompilerError]:
        ...


class LLMPort(ABC):
    @abstractmethod
    def clasificar(self, fragmento: str) -> str:
        ...

    @abstractmethod
    def explicar_errores(self, source: str, errors: list[dict]) -> str:
        ...
