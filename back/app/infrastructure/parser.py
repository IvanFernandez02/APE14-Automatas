# pyrefly: ignore [missing-import]
from lark import Lark, Transformer, Token as LarkToken, UnexpectedInput, v_args

from ..domain.models import (
    CompilerError,
    EquationNode,
    ExpressionNode,
    FactorNode,
    TermNode,
    Token,
    TokenType,
)
from ..domain.ports import ParserPort


@v_args(inline=True)
class _EquationTransformer(Transformer):
    def start(self, equation):
        return equation

    def equation(self, left, _equals, right):
        return EquationNode(izquierda=left, derecha=right)

    def expression(self, first, *rest):
        terminos = [first]
        for operador, termino in zip(rest[0::2], rest[1::2]):
            termino.signo = "-" if operador.type == "MINUS" else "+"
            terminos.append(termino)
        return ExpressionNode(terminos=terminos)

    def term(self, first, *rest):
        factores = [first]
        for _operador, factor in zip(rest[0::2], rest[1::2]):
            factores.append(factor)
        return TermNode(signo="+", factores=factores)

    def variable(self, token: LarkToken):
        valor = str(token)
        coeficiente, variable = self._descomponer_var(valor)
        return FactorNode(tipo="variable", valor=variable, coeficiente=coeficiente, exponente=1)

    def variable_pow(self, token: LarkToken, _power: LarkToken, exponent: LarkToken):
        valor = str(token)
        coeficiente, variable = self._descomponer_var(valor)
        exponente = int(str(exponent)) if str(exponent).isdigit() else 1
        return FactorNode(tipo="variable", valor=variable, coeficiente=coeficiente, exponente=exponente)

    def number(self, token: LarkToken):
        valor = str(token)
        return FactorNode(tipo="number", valor="x" if valor == "0" else valor)

    @staticmethod
    def _descomponer_var(valor: str) -> tuple[int, str]:
        valor = valor.lower()
        if valor[:-1].isdigit():
            return int(valor[:-1]), "x"
        return 1, valor


class EquationParser(ParserPort):
    _GRAMMAR = r"""
        start: equation
        equation: expression EQUAL expression
        expression: term ((PLUS | MINUS) term)*
        term: factor ((TIMES | DIV) factor)*
        ?factor: VAR POWER NUMBER   -> variable_pow
               | VAR                -> variable
               | NUMBER             -> number

        PLUS: "+"
        MINUS: "-"
        TIMES: "*"
        DIV: "/"
        EQUAL: "="
        POWER: "^"
        VAR.2: /[0-9]*x/
        NUMBER.1: /\d+(?:\.\d+)?/
        %import common.WS
        %ignore WS
    """

    def __init__(self):
        self._parser = Lark(self._GRAMMAR, start="start", parser="lalr")
        self._transformer = _EquationTransformer()

    def parse(self, tokens: list[Token]) -> tuple[EquationNode | None, list[CompilerError]]:
        if not tokens:
            return None, [CompilerError(
                fase="syntax", token="",
                causa="No hay tokens para analizar.",
                sugerencia="Ingrese una ecuación válida.",
            )]

        try:
            entrada = self._normalizar_tokens(tokens)
            arbol = self._parser.parse(entrada)
            ast = self._transformer.transform(arbol)
            return ast, []
        except (SyntaxError, UnexpectedInput) as exc:
            token = self._extraer_token_error(exc, tokens)
            return None, [CompilerError(
                fase="syntax",
                token=token,
                causa=self._formatear_error(exc),
                sugerencia="Revise la sintaxis de la ecuación.",
            )]

    def _normalizar_tokens(self, tokens: list[Token]) -> str:
        partes: list[str] = []
        for token in tokens:
            if token.tipo == TokenType.UNKNOWN:
                raise SyntaxError(f"Token inesperado '{token.valor}' en la expresión.")
            partes.append(self._token_a_texto(token))
        return " ".join(partes)

    def _token_a_texto(self, token: Token) -> str:
        mapping = {
            TokenType.VAR: token.valor,
            TokenType.NUMBER: token.valor,
            TokenType.OP_SUMA: "+",
            TokenType.OP_RESTA: "-",
            TokenType.OP_MULT: "*",
            TokenType.OP_DIV: "/",
            TokenType.OP_ASIGNACION: "=",
            TokenType.POWER: "^",
        }
        return mapping[token.tipo]

    def _extraer_token_error(self, exc: Exception, tokens: list[Token]) -> str:
        if isinstance(exc, UnexpectedInput):
            if getattr(exc, "token", None) is not None:
                return str(exc.token)
            if tokens:
                posicion = max(getattr(exc, "pos_in_stream", 0), 0)
                indice = min(len(tokens) - 1, posicion)
                return tokens[indice].valor
        return tokens[-1].valor if tokens else ""

    def _formatear_error(self, exc: Exception) -> str:
        if isinstance(exc, UnexpectedInput):
            esperado = ", ".join(sorted(getattr(exc, "expected", []) or []))
            if esperado:
                return f"Sintaxis inválida. Se esperaba uno de: {esperado}."
            return "Sintaxis inválida en la ecuación."
        return str(exc)
