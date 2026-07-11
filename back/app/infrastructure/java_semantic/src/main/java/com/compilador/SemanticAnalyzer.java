package com.compilador;

import java.util.ArrayList;
import java.util.List;

public class SemanticAnalyzer {

    public static class TokenNode {
        public String tipo;
        public String valor;
    }

    public static class AstNode {
        public String tipo;
        public ExpressionNode izquierda;
        public ExpressionNode derecha;
    }

    public static class ExpressionNode {
        public List<TermNode> terminos;
        
        public ExpressionNode() {
            this.terminos = new ArrayList<>();
        }
    }

    public static class TermNode {
        public String signo;
        public List<FactorNode> factores;
        
        public TermNode() {
            this.factores = new ArrayList<>();
        }
    }

    public static class FactorNode {
        public String tipo;
        public String valor;
        public int coeficiente;
        public int exponente;
    }

    public static class CompilerError {
        public String fase;
        public String token;
        public String causa;
        public String sugerencia;

        public CompilerError(String fase, String token, String causa, String sugerencia) {
            this.fase = fase;
            this.token = token;
            this.causa = causa;
            this.sugerencia = sugerencia;
        }
    }

    public List<CompilerError> validar(AstNode ast, List<TokenNode> tokens) {
        List<CompilerError> errors = new ArrayList<>();

        if (ast == null) {
            return errors;
        }

        if (ast.izquierda == null || ast.izquierda.terminos == null || ast.izquierda.terminos.isEmpty()) {
            errors.add(new CompilerError(
                    "semantic", "",
                    "El lado izquierdo de la ecuación está vacío.",
                    "Agregue una expresión antes del '='."
            ));
        }

        if (ast.derecha == null || ast.derecha.terminos == null || ast.derecha.terminos.isEmpty()) {
            errors.add(new CompilerError(
                    "semantic", "",
                    "El lado derecho de la ecuación está vacío.",
                    "Agregue una expresión después del '='."
            ));
        }

        if (ast.izquierda != null && ast.izquierda.terminos != null) {
            for (TermNode term : ast.izquierda.terminos) {
                validarTermino(term, errors);
            }
        }

        if (ast.derecha != null && ast.derecha.terminos != null) {
            for (TermNode term : ast.derecha.terminos) {
                validarTermino(term, errors);
            }
        }

        if (tokens != null) {
            int eqCount = 0;
            for (TokenNode token : tokens) {
                if (token.tipo != null && token.tipo.contains("OP_ASIGNACION")) {
                    eqCount++;
                }
            }
            if (eqCount > 1) {
                errors.add(new CompilerError(
                        "semantic", "=",
                        "La ecuación tiene más de un signo '='.",
                        "Use solo un signo '=' para la ecuación."
                ));
            }
        }

        return errors;
    }

    private void validarTermino(TermNode term, List<CompilerError> errors) {
        if (term.factores == null) return;
        
        for (FactorNode factor : term.factores) {
            if ("variable".equals(factor.tipo) && !"x".equals(factor.valor)) {
                errors.add(new CompilerError(
                        "semantic", factor.valor,
                        "La variable '" + factor.valor + "' no es válida.",
                        "Use 'x' como única variable."
                ));
            }
            if ("variable".equals(factor.tipo) && factor.exponente > 1) {
                errors.add(new CompilerError(
                        "semantic", "^" + factor.exponente,
                        "Exponente " + factor.exponente + ": la ecuación debe ser de primer grado.",
                        "Use exponente 1 o simplemente '" + factor.valor + "'."
                ));
            }
        }
    }
}
