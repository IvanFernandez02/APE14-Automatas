import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..domain.models import Token, TokenType, TokenSource, CompilerError, CompilerResult
from ..domain.ports import LexerPort, ParserPort, SemanticPort, LLMPort


class CompilerUseCase:
    def __init__(
        self,
        lexer: LexerPort,
        parser: ParserPort,
        semantic: SemanticPort,
        llm: LLMPort,
    ):
        self._lexer = lexer
        self._parser = parser
        self._semantic = semantic
        self._llm = llm

    def analizar(self, entrada: str) -> CompilerResult:
        result = CompilerResult(entrada=entrada)
        inicio = time.perf_counter()

        tokens, lex_errors = self._lexer.tokenizar(entrada)
        result.tokens = tokens
        result.errors.extend(lex_errors)

        tiempo_llm = 0.0
        if any(t.tipo == TokenType.UNKNOWN for t in tokens):
            inicio_llm = time.perf_counter()
            self._clasificar_unknowns(tokens, result.errors)
            tiempo_llm = (time.perf_counter() - inicio_llm) * 1000

        result.tiempo_lexer_ms = (time.perf_counter() - inicio) * 1000
        result.tiempo_llm_ms = tiempo_llm

        still_unknown = any(t.tipo == TokenType.UNKNOWN for t in tokens)
        if not lex_errors and tokens and not still_unknown:
            inicio_parse = time.perf_counter()
            ast, parse_errors = self._parser.parse(tokens)
            result.ast = ast
            result.errors.extend(parse_errors)
            result.tiempo_parser_ms = (time.perf_counter() - inicio_parse) * 1000

            if not parse_errors and ast:
                inicio_sem = time.perf_counter()
                sem_errors = self._semantic.validate(ast, tokens)
                result.errors.extend(sem_errors)
                result.tiempo_semantic_ms = (time.perf_counter() - inicio_sem) * 1000

                if not result.errors:
                    result.pasos_solucion = self._resolver_ecuacion(ast)

        result.tiempo_total_ms = (time.perf_counter() - inicio) * 1000

        if result.errors:
            self._enriquecer_errores_con_llm(entrada, result)

        return result

    def _clasificar_unknowns(self, tokens: list[Token], errors: list[CompilerError]):
        unknown_indices = [
            i for i, t in enumerate(tokens) if t.tipo == TokenType.UNKNOWN
        ]

        with ThreadPoolExecutor(max_workers=len(unknown_indices)) as executor:
            futuros = {
                executor.submit(self._llm.clasificar, tokens[idx].valor): i
                for i, idx in enumerate(unknown_indices)
            }
            for futuro in as_completed(futuros):
                i = futuros[futuro]
                respuesta = futuro.result().strip()
                idx = unknown_indices[i]
                nuevo_tipo, error = self._interpretar_respuesta(
                    respuesta, tokens[idx].valor,
                )
                tokens[idx].tipo = nuevo_tipo
                tokens[idx].fuente = TokenSource.LLM
                if error:
                    errors.append(error)

    def _interpretar_respuesta(
        self, respuesta: str, valor_original: str,
    ) -> tuple[TokenType, CompilerError | None]:
        if respuesta.startswith("{"):
            try:
                data = json.loads(respuesta)
                item = data.get("errors", [{}])[0]
                return TokenType.UNKNOWN, CompilerError(
                    fase="lexical",
                    token=str(item.get("token", valor_original)),
                    causa=str(item.get("cause", "Token no reconocido.")),
                    sugerencia=str(item.get("suggestion", "Elimine el token inválido.")),
                )
            except (json.JSONDecodeError, IndexError, KeyError):
                return TokenType.UNKNOWN, CompilerError(
                    fase="lexical", token=valor_original,
                    causa="Token no reconocido.",
                    sugerencia="Elimine el token inválido.",
                )

        tipo_str = respuesta.upper()
        if tipo_str == "UNKNOWN":
            return TokenType.UNKNOWN, CompilerError(
                fase="lexical", token=valor_original,
                causa=f"El token '{valor_original}' no es válido en el lenguaje.",
                sugerencia="Elimine el token inválido.",
            )

        try:
            return TokenType(tipo_str), None
        except ValueError:
            return TokenType.UNKNOWN, CompilerError(
                fase="lexical", token=valor_original,
                causa=f"El token '{valor_original}' no es reconocido.",
                sugerencia="Elimine el token inválido.",
            )

    def _enriquecer_errores_con_llm(self, entrada: str, result: CompilerResult):
        errors_dict = [
            {"fase": e.fase, "token": e.token, "causa": e.causa, "sugerencia": e.sugerencia}
            for e in result.errors
        ]
        try:
            respuesta = self._llm.explicar_errores(entrada, errors_dict).strip()
            if respuesta.startswith("{"):
                data = json.loads(respuesta)
                items = data.get("errors", [])
                for i, item in enumerate(items):
                    if i < len(result.errors):
                        result.errors[i].causa = str(item.get("cause", result.errors[i].causa))
                        result.errors[i].sugerencia = str(item.get("suggestion", result.errors[i].sugerencia))
        except Exception:
            pass

    def _resolver_ecuacion(self, ast) -> list[str]:
        def evaluar_expresion(expr):
            coef_x = 0.0
            val_const = 0.0
            for term in expr.terminos:
                term_coef = 1.0
                term_val = 1.0
                has_var = False
                for factor in term.factores:
                    if factor.tipo == "variable":
                        has_var = True
                        term_coef *= factor.coeficiente
                    elif factor.tipo == "number":
                        term_val *= float(factor.valor)
                
                signo_mult = 1.0 if term.signo == "+" else -1.0
                
                if has_var:
                    coef_x += term_coef * term_val * signo_mult
                else:
                    val_const += term_val * signo_mult
                    
            return coef_x, val_const

        c1, k1 = evaluar_expresion(ast.izquierda)
        c2, k2 = evaluar_expresion(ast.derecha)

        def format_side(c, k):
            if c == 0 and k == 0: return "0"
            parts = []
            if c != 0:
                if c == 1: parts.append("x")
                elif c == -1: parts.append("-x")
                else: parts.append(f"{c:g}x")
            if k != 0:
                if k > 0 and c != 0: parts.append(f"+ {k:g}")
                elif k < 0 and c != 0: parts.append(f"- {abs(k):g}")
                else: parts.append(f"{k:g}")
            return " ".join(parts)

        pasos = []
        # Paso 1: Original estructurada
        orig_izq = format_side(c1, k1)
        orig_der = format_side(c2, k2)
        pasos.append(f"{orig_izq} = {orig_der}")

        # c1*x + k1 = c2*x + k2
        # Paso 2: Agrupando terminos
        c_izq = c1 - c2
        k_der = k2 - k1
        if c2 != 0 or k1 != 0:
            pasos.append(f"{c1:g}x - {c2:g}x = {k2:g} - {k1:g}")

        # Paso 3: Simplificando
        if c1 != 0 or c2 != 0:
            pasos.append(f"{c_izq:g}x = {k_der:g}")

        # Paso 4: Despeje y división
        if c_izq == 0:
            if k_der == 0:
                pasos.append("Identidad matemática: Infinitas soluciones (0 = 0)")
            else:
                pasos.append(f"Contradicción: Sin solución (0 = {k_der:g})")
            return pasos
        
        if c_izq != 1:
            pasos.append(f"x = {k_der:g} / {c_izq:g}")

        # Paso 5: Resultado
        x_val = k_der / c_izq
        if x_val.is_integer():
            pasos.append(f"x = {int(x_val)}")
        else:
            pasos.append(f"x = {round(x_val, 4)}")
            
        return pasos
