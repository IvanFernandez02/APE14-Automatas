from abc import ABC, abstractmethod

from ..domain.ports import LLMPort


SYSTEM_PROMPT = """
Eres un clasificador léxico estricto para ecuaciones de primer grado.
Solo se permite la variable x, números, y operadores +, -, *, /, ^, =.

Tokens permitidos: VAR, NUMBER, OP_SUMA, OP_RESTA, OP_MULT, OP_DIV, OP_ASIGNACION, POWER, UNKNOWN.

Reglas:
- Si el fragmento coincide con un token válido, responde SOLO con el nombre del token.
- Si el fragmento NO es válido, responde UNICAMENTE con JSON:
{"errors":[{"token":"...","cause":"explicación técnica breve","suggestion":"corrección para el usuario"}]}
- Si parece una variable inválida (y, z, a, variable1, etc.), sugiere usar x.
- Si tiene caracteres no permitidos, sugiere eliminarlos.
- Si contiene números mal formados, sugiere corregirlos.
- Si no hay corrección razonable, sugiere "Elimine el token inválido.".

Ejemplos de clasificación:
más -> OP_SUMA
menos -> OP_RESTA
es igual a -> OP_ASIGNACION
x -> VAR
5 -> NUMBER
2x -> VAR

Ejemplos de error:
y -> {"errors":[{"token":"y","cause":"Variable no válida.","suggestion":"Utilice x."}]}
hola -> {"errors":[{"token":"hola","cause":"Palabra no reconocida.","suggestion":"Elimine el token inválido."}]}
3y -> {"errors":[{"token":"3y","cause":"Variable 'y' no es válida.","suggestion":"Use 3x en lugar de 3y."}]}
"""

EXPLAIN_PROMPT = """
Eres un experto en compiladores y análisis léxico.

Tokens válidos del lenguaje:

- VAR: variable x (ej: x, 2x)
- NUMBER: números enteros o decimales
- OP_SUMA: +
- OP_RESTA: -
- OP_MULT: *
- OP_DIV: /
- POWER: ^
- OP_ASIGNACION: =

Código fuente:
{source}

Errores detectados:
{errors}

Analiza cada error.

Reglas para las sugerencias:

1. Utiliza únicamente los tokens válidos definidos anteriormente.
2. No inventes nuevas palabras reservadas.
3. No inventes variables distintas de "x".
4. No inventes operadores o símbolos.
5. Si el token es similar a una palabra reservada, sugiere la palabra reservada más cercana.
6. Si parece una variable inválida (por ejemplo: y, z, a, variable1), sugiere utilizar "x".
7. Si contiene caracteres no permitidos, sugiere eliminarlos o reemplazarlos por un token válido.
8. Si no existe una corrección razonable, utiliza:
   "Elimine el token inválido."
9. La causa debe ser técnica, breve y clara.
10. La sugerencia debe estar orientada al usuario final.

Responde ÚNICAMENTE con JSON válido.

Formato esperado:

{{"errors":[{{"token":"token inválido","cause":"explicación breve del error","suggestion":"corrección sugerida"}}]}}

No agregues texto adicional.
No agregues markdown.
No agregues comentarios.
"""


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        ...


class OllamaClient(LLMClient):
    def __init__(self, model="llama3.2:3b", host="http://localhost:11434/api/generate"):
        self.model = model
        self.host = host

    def generate(self, prompt: str) -> str:
        import requests
        resp = requests.post(
            self.host,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0, "top_p": 0.1},
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["response"]


class LLMAdapter(LLMPort):
    def __init__(self, client: LLMClient):
        self._client = client

    def clasificar(self, fragmento: str) -> str:
        prompt = f"{SYSTEM_PROMPT}\n\nFragmento: {fragmento}"
        return self._client.generate(prompt)

    def explicar_errores(self, source: str, errors: list[dict]) -> str:
        import json
        prompt = EXPLAIN_PROMPT.format(
            source=source,
            errors=json.dumps(errors, ensure_ascii=False, indent=2),
        )
        return self._client.generate(prompt)


def create_llm(modelo: str = "llama3.2:3b") -> LLMPort:
    return LLMAdapter(OllamaClient(model=modelo))


def list_ollama_models(host: str = "http://localhost:11434/api/tags") -> list[str]:
    import requests

    resp = requests.get(host, timeout=20)
    resp.raise_for_status()

    data = resp.json()
    models = data.get("models", [])
    names = [m.get("name", "") for m in models]
    return [name for name in names if name]
