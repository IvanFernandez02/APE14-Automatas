import re
import time

from ..domain.models import Token, TokenType, TokenSource, CompilerError
from ..domain.ports import LexerPort


class RegexLexer(LexerPort):

    PATRONES: list[tuple[str, str]] = [
        ("VAR", r"\b\d*x\b"),
        ("NUMBER", r"\b\d+(\.\d+)?\b"),
        ("POWER", r"\^"),
        ("OP_SUMA", r"\+"),
        ("OP_RESTA", r"\-"),
        ("OP_MULT", r"\*"),
        ("OP_DIV", r"\/"),
        ("OP_ASIGNACION", r"="),
    ]

    FRAGMENTOS_NL: tuple[str, ...] = (
        "es igual a", "igual a", "más", "mas", "menos",
        "resta", "suma", "por", "veces", "multiplicado",
        "dividido", "entre", "partido", "añade", "quita",
    )

    def __init__(self):
        self._regex = re.compile(
            "|".join(f"(?P<{n}>{p})" for n, p in self.PATRONES),
            re.IGNORECASE,
        )

    def tokenizar(self, entrada: str) -> tuple[list[Token], list[CompilerError]]:
        inicio = time.perf_counter()
        tokens: list[Token] = []
        errors: list[CompilerError] = []
        palabras = entrada.strip().split()
        indice = 0

        while indice < len(palabras):
            palabra = palabras[indice]
            m = self._regex.fullmatch(palabra)
            if m:
                tipo = TokenType(m.lastgroup)
                tokens.append(Token(
                    tipo=tipo, valor=palabra,
                    fuente=TokenSource.AFD, pos=indice,
                    tiempo_ms=(time.perf_counter() - inicio) * 1000,
                ))
                indice += 1
                continue

            frag, salto = self._coincide_fragmento(palabras, indice)
            if frag:
                tokens.append(Token(
                    tipo=TokenType.UNKNOWN, valor=frag,
                    fuente=TokenSource.AFD, pos=indice,
                    tiempo_ms=(time.perf_counter() - inicio) * 1000,
                ))
                indice += salto
                continue

            partes = [palabra]
            indice += 1
            while indice < len(palabras):
                sig = palabras[indice]
                if self._regex.fullmatch(sig):
                    break
                sig_frag, _ = self._coincide_fragmento(palabras, indice)
                if sig_frag:
                    break
                partes.append(sig)
                indice += 1

            tokens.append(Token(
                tipo=TokenType.UNKNOWN, valor=" ".join(partes),
                fuente=TokenSource.AFD, pos=indice - len(partes),
                tiempo_ms=(time.perf_counter() - inicio) * 1000,
            ))

        return tokens, errors

    def _coincide_fragmento(self, palabras: list[str], indice: int) -> tuple[str | None, int]:
        for long in range(3, 0, -1):
            if indice + long > len(palabras):
                continue
            cand = " ".join(palabras[indice:indice + long]).lower()
            if cand in self.FRAGMENTOS_NL:
                return cand, long
        return None, 0
