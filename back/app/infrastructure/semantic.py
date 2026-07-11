import os
# pyrefly: ignore [missing-import]
import jpype
# pyrefly: ignore [missing-import]
import jpype.imports
from ..domain.models import CompilerError, EquationNode, Token
from ..domain.ports import SemanticPort

class SemanticAnalyzer(SemanticPort):

    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Usamos el JAR estandar, ya no tiene dependencias embebidas
        jar_path = os.path.join(current_dir, "java_semantic", "target", "semantic-analyzer-1.0-SNAPSHOT.jar")
        
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[jar_path])
        
        # Guardar referencias a las clases Java usando JClass
        self.JAnalyzer = jpype.JClass("com.compilador.SemanticAnalyzer")
        self.JTokenNode = jpype.JClass("com.compilador.SemanticAnalyzer$TokenNode")
        self.JAstNode = jpype.JClass("com.compilador.SemanticAnalyzer$AstNode")
        self.JExpressionNode = jpype.JClass("com.compilador.SemanticAnalyzer$ExpressionNode")
        self.JTermNode = jpype.JClass("com.compilador.SemanticAnalyzer$TermNode")
        self.JFactorNode = jpype.JClass("com.compilador.SemanticAnalyzer$FactorNode")
        self.JArrayList = jpype.JClass("java.util.ArrayList")
        
        # Instanciar el analizador
        self.analyzer_instance = self.JAnalyzer()

    def validate(self, ast: EquationNode | None, tokens: list[Token]) -> list[CompilerError]:
        errors: list[CompilerError] = []

        if ast is None:
            return errors

        try:
            # Construir el AST en Java
            java_ast = self._convert_ast_to_java(ast)
            
            # Construir la lista de tokens en Java
            java_tokens = self.JArrayList()
            for t in tokens:
                j_token = self.JTokenNode()
                j_token.tipo = t.tipo.value
                j_token.valor = t.valor
                java_tokens.add(j_token)
                
            # Llamada nativa a Java (memoria compartida)
            java_errors = self.analyzer_instance.validar(java_ast, java_tokens)
            
            # Convertir errores de Java a Python
            if java_errors:
                for j_err in java_errors:
                    errors.append(CompilerError(
                        fase=str(j_err.fase),
                        token=str(j_err.token),
                        causa=str(j_err.causa),
                        sugerencia=str(j_err.sugerencia)
                    ))

        except Exception as e:
            print(f"Error calling Java SemanticAnalyzer via JPype: {e}")

        return errors

    def _convert_ast_to_java(self, ast):
        if ast is None:
            return None
            
        j_ast = self.JAstNode()
        j_ast.tipo = "ecuacion"
        
        # Lado Izquierdo
        j_izq = self.JExpressionNode()
        for t in ast.izquierda.terminos:
            j_term = self.JTermNode()
            j_term.signo = t.signo
            for f in t.factores:
                j_factor = self.JFactorNode()
                j_factor.tipo = f.tipo
                j_factor.valor = f.valor
                j_factor.coeficiente = f.coeficiente
                j_factor.exponente = f.exponente
                j_term.factores.add(j_factor)
            j_izq.terminos.add(j_term)
        j_ast.izquierda = j_izq
        
        # Lado Derecho
        j_der = self.JExpressionNode()
        for t in ast.derecha.terminos:
            j_term = self.JTermNode()
            j_term.signo = t.signo
            for f in t.factores:
                j_factor = self.JFactorNode()
                j_factor.tipo = f.tipo
                j_factor.valor = f.valor
                j_factor.coeficiente = f.coeficiente
                j_factor.exponente = f.exponente
                j_term.factores.add(j_factor)
            j_der.terminos.add(j_term)
        j_ast.derecha = j_der
        
        return j_ast
