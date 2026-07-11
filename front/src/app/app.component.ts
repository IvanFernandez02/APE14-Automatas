import { CommonModule, JsonPipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { finalize } from 'rxjs';

import { CompilerApiService } from './compiler-api.service';
import { AnalyzeResponse } from './compiler-api.types';

interface ExampleCase {
  label: string;
  value: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, JsonPipe, ReactiveFormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly api = inject(CompilerApiService);

  readonly fallbackModelos = ['llama3.2:3b', 'mistral:latest', 'llama3:latest'];
  modelosDisponibles: string[] = [...this.fallbackModelos];
  cargandoModelos = false;

  readonly form = this.fb.group({
    entrada: this.fb.control('2x - 3 = x + 1', [Validators.required, Validators.minLength(1)]),
    modelo_llm: this.fb.control('llama3.2:3b', [Validators.required, Validators.minLength(1)])
  });

  readonly ejemplos: ExampleCase[] = [
    { label: '✅ Válido (Símbolos)', value: '5x - 8 = 23' },
    { label: '✅ Válido (Texto)', value: '2x más 3 es igual a 15' },
    { label: '❌ Err. Léxico (Símbolos)', value: '2y + 5 = 13' },
    { label: '❌ Err. Léxico (Texto)', value: '2x patata 5 es igual a 13' },
    { label: '❌ Err. Sintáctico (Símbolos)', value: '5x - = 23' },
    { label: '❌ Err. Sintáctico (Texto)', value: '2x más es igual a 15' },
    { label: '❌ Err. Semántico (Símbolos)', value: 'x ^ 2 = 16' },
    { label: '❌ Err. Semántico (Texto)', value: 'x elevado a 2 es igual a 16' }
  ];

  resultado: AnalyzeResponse | null = null;
  errorMensaje = '';
  cargando = false;

  constructor() {
    this.cargarModelos();
  }

  get resumen() {
    return {
      tokens: this.resultado?.tokens.length ?? 0,
      errores: this.resultado?.errores.length ?? 0,
    };
  }

  get totalMs(): number {
    return this.resultado?.tiempos.total_ms ?? 0;
  }

  get reglasSemanticas() {
    if (!this.resultado) return null;
    
    // Si se encontraron errores léxicos o sintácticos, Java nunca llegó a ejecutarse.
    if (this.resultado.tiempos.semantic_ms === 0 && this.resultado.errores.some(e => e.fase !== 'semantic')) {
      return { evaluado: false, reglas: [] };
    }

    const erroresSemanticos = this.resultado.errores.filter(e => e.fase === 'semantic');
    const causas = erroresSemanticos.map(e => e.causa.toLowerCase());

    return {
      evaluado: true,
      reglas: [
        {
          nombre: "Lado Izquierdo Válido",
          descripcion: "Debe existir al menos un término matemático antes del signo de igual.",
          cumple: !causas.some(c => c.includes('lado izquierdo'))
        },
        {
          nombre: "Lado Derecho Válido",
          descripcion: "Debe existir al menos un término matemático después del signo de igual.",
          cumple: !causas.some(c => c.includes('lado derecho'))
        },
        {
          nombre: "Variable exclusiva 'x'",
          descripcion: "Solo se permite el uso de la variable 'x' en toda la expresión.",
          cumple: !causas.some(c => c.includes('no es válida'))
        },
        {
          nombre: "Ecuación de Primer Grado",
          descripcion: "Ninguna variable puede tener un exponente mayor a 1 (e.g., x^2 no está permitido).",
          cumple: !causas.some(c => c.includes('primer grado'))
        },
        {
          nombre: "Único signo de igualdad",
          descripcion: "La ecuación debe estar dividida por un único '='.",
          cumple: !causas.some(c => c.includes('signos de igual') || c.includes('signo de igual'))
        }
      ]
    };
  }

  get tablaSimbolos() {
    const ast = this.resultado?.arbol_sintactico;
    if (!ast) return null;

    const simbolos: { id: string; tipo: string; coeficiente: number | null; exponente: number | null; ubicacion: string }[] = [];

    const recolectar = (exp: any, ubicacion: string) => {
      if (!exp?.terminos) return;
      for (const term of exp.terminos) {
        if (!term.factores) continue;
        for (const f of term.factores) {
          const isVar = f.tipo === 'variable';
          // Para mostrarlo bonito, armamos el nombre completo de la variable
          let nombre = f.valor;
          if (isVar) {
            const coef = f.coeficiente !== 1 ? f.coeficiente : '';
            const expStr = f.exponente !== 1 ? `^${f.exponente}` : '';
            nombre = `${coef}${f.valor}${expStr}`;
          }

          simbolos.push({
            id: nombre,
            tipo: isVar ? 'Variable' : 'Constante',
            coeficiente: isVar ? f.coeficiente : null,
            exponente: isVar ? f.exponente : null,
            ubicacion
          });
        }
      }
    };

    recolectar(ast.izquierda, 'Lado Izquierdo');
    recolectar(ast.derecha, 'Lado Derecho');

    return simbolos;
  }

  cargarEjemplo(ejemplo: string): void {
    this.form.patchValue({ entrada: ejemplo });
    this.form.markAsDirty();
  }

  cargarModelos(): void {
    this.cargandoModelos = true;
    this.api.getModels()
      .pipe(finalize(() => {
        this.cargandoModelos = false;
      }))
      .subscribe({
        next: ({ modelos }) => {
          const depurados = Array.from(new Set(modelos.filter((m) => m?.trim())));
          if (!depurados.length) {
            this.errorMensaje = 'Ollama respondió sin modelos; se usan modelos por defecto.';
            this.modelosDisponibles = [...this.fallbackModelos];
            return;
          }

          this.modelosDisponibles = depurados;
          const modeloActual = this.form.controls.modelo_llm.value;
          if (!depurados.includes(modeloActual)) {
            this.form.patchValue({ modelo_llm: depurados[0] });
          }
        },
        error: () => {
          this.errorMensaje = 'No se pudo obtener la lista de modelos desde Ollama; se usan modelos por defecto.';
          this.modelosDisponibles = [...this.fallbackModelos];
        }
      });
  }

  analizar(): void {
    if (this.form.invalid || this.cargando) {
      this.form.markAllAsTouched();
      return;
    }

    this.cargando = true;
    this.errorMensaje = '';

    this.api.analyze(this.form.getRawValue())
      .pipe(finalize(() => {
        this.cargando = false;
      }))
      .subscribe({
        next: (resultado) => {
          this.resultado = resultado;
        },
        error: (error) => {
          this.errorMensaje = error?.error?.detail ?? 'No se pudo conectar con el backend.';
        }
      });
  }

  limpiar(): void {
    this.resultado = null;
    this.errorMensaje = '';
    this.form.reset({
      entrada: '2x - 3 = x + 1',
      modelo_llm: this.modelosDisponibles[0] ?? 'llama3.2:3b'
    });
  }
}
