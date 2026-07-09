# Analizador de Ruby — Lenguajes de Programación

Proyecto grupal de la materia de Lenguajes de Programación de la Escuela Superior Politécnica del Litoral (ESPOL). El objetivo es construir un **analizador léxico, sintáctico y semántico** para un subconjunto representativo del lenguaje **Ruby**, usando la librería PLY (Python Lex-Yacc), con una interfaz gráfica para ingresar código y visualizar resultados.

## ¿Qué hace?

El proyecto implementa las tres fases clásicas del análisis de un lenguaje:

1. **Léxico** (`lexer.py`) — divide el código fuente en tokens (variables, tipos, operadores, palabras reservadas, delimitadores, comentarios) y reporta caracteres inválidos con su línea.
2. **Sintáctico** (`parser.py`) — verifica que la secuencia de tokens respete la gramática de Ruby (asignaciones, expresiones, estructuras de control, funciones, estructuras de datos) y reporta errores de sintaxis con el token y la posición.
3. **Semántico** (`semantico.py`) — recorre el árbol de análisis (AST) y verifica reglas de sentido: identificadores declarados, constantes inmutables, compatibilidad de tipos, condiciones booleanas, `break`/`next` dentro de bucles y aridad de funciones. Clasifica cada error por categoría.

Todo se integra en una interfaz gráfica (`main.py`, Tkinter) con una pestaña por fase.

## Estructura del repositorio

```
lp-ruby-project/
├── lexer.py           # Analizador léxico (PLY lex)
├── parser.py          # Analizador sintáctico (PLY yacc) — produce el AST
├── semantico.py       # Analizador semántico (recorrido del AST)
├── main.py            # Interfaz gráfica (Tkinter) con las 3 pestañas
├── algoritmos/        # Programas Ruby de prueba por integrante
└── logs/              # Logs de salida generados por cada fase
```

Cada archivo está dividido en bloques `APORTE INTEGRANTE 1/2/3`, de modo que cada integrante trabaja su parte sin pisar la de los demás. El analizador semántico usa un patrón de *hooks*: la estructura base (Integrante 1) hace el recorrido del AST e invoca métodos `regla_*` que los Integrantes 2 y 3 implementan en su propio bloque.

## Integrantes y responsabilidades

**Annabella Sánchez (Integrante 1)** — Variables (locales, globales, de instancia y constantes) y tipos primitivos; estructura `Array`; control `if/elsif/else`; función con retorno. Estructura base del parser y del analizador semántico. *Reglas semánticas:* identificador declarado antes de usarse y constante inmutable.

**Cristian Intriago (Integrante 2)** — Operadores aritméticos, de asignación compuesta, de comparación y lógicos; estructura `Hash`; control `while`; función con número variable de argumentos. *Reglas semánticas:* compatibilidad de tipos en operaciones aritméticas y condición booleana en `if`/`while`.

**Valentina Falconi (Integrante 3)** — Delimitadores, operadores de rango (`..`, `...`) y comentarios; iteración `each`/`for`; función con parámetro opcional; entrada/salida (`puts`/`print`/`gets`). *Reglas semánticas:* `break`/`next` solo dentro de un bucle y aridad de funciones (el número de argumentos de la llamada debe coincidir con la definición).

## Requisitos

- Python 3
- PLY (`pip install ply`)

## Cómo ejecutar

### Interfaz gráfica (recomendado)

```bash
python main.py
```

Abre una ventana con tres pestañas (Léxico, Sintáctico, Semántico). En cada una se puede escribir o cargar un `.rb`, analizar y ver los resultados; el botón **💾 Exportar log** de la barra inferior guarda el log de la **pestaña activa** en `logs/`.

### Línea de comandos (por fase)

```bash
python lexer.py     algoritmos/algoritmo1.rb   # tokens + log léxico
python parser.py    algoritmos/algoritmo1.rb   # validación sintáctica
python semantico.py algoritmos/algoritmo1.rb   # validación semántica
```

## Formato de archivos

**Algoritmo de prueba** — en la carpeta `algoritmos/`:
```
algoritmos/algoritmoN.rb        (N = número de integrante: 1, 2 o 3)
```

**Logs** — en la carpeta `logs/`, con el nombre del integrante y la fecha/hora de ejecución:
```
logs/lexico-NombreApellido-DD-MM-YYYY-HHhMM.txt
logs/sintactico-NombreApellido-DD-MM-YYYY-HHhMM.txt
logs/semantico-NombreApellido-DD-MM-YYYY-HHhMM.txt
```

## Estado del proyecto

- ✅ **Léxico** — completo (tokens de los tres integrantes y palabras reservadas).
- ✅ **Sintáctico** — completo; los tres algoritmos de prueba parsean.
- ✅ **Semántico** — completo; las seis reglas (dos por integrante) implementadas y los tres algoritmos pasan sin errores.
- ✅ **Interfaz gráfica** — las tres pestañas operativas con exportación de logs.
