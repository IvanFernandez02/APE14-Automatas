export interface AnalyzeRequest {
  entrada: string;
  modelo_llm: string;
}

export interface AnalyzeToken {
  tipo: string;
  valor: string;
  fuente: string;
}

export interface AnalyzeError {
  fase: string;
  token: string;
  causa: string;
  sugerencia: string;
}

export interface FactorNode {
  tipo: string;
  valor: string;
  coeficiente: number;
  exponente: number;
}

export interface TermNode {
  signo: string;
  factores: FactorNode[];
}

export interface ExpressionNode {
  terminos: TermNode[];
}

export interface AstNode {
  tipo: string;
  izquierda: ExpressionNode;
  derecha: ExpressionNode;
}

export interface AnalyzeResponse {
  entrada: string;
  tokens: AnalyzeToken[];
  errores: AnalyzeError[];
  arbol_sintactico: AstNode | null;
  pasos_solucion?: string[];
  tiempos: {
    total_ms: number;
    lexer_ms: number;
    parser_ms: number;
    semantic_ms: number;
    llm_ms: number;
  };
}

export interface ModelsResponse {
  modelos: string[];
}
