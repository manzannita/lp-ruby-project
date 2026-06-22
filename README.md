# Proyecto Léxico Ruby — Lenguajes de Programación

Este proyecto corresponde a un trabajo grupal de la materia de Lenguajes de Programación de la Escuela Superior Politécnica del Litoral (ESPOL). El objetivo principal es construir un analizador léxico para el lenguaje Ruby utilizando la librería PLY (Python Lex-Yacc).

## ¿Qué estamos haciendo?

Estamos implementando un lexer capaz de reconocer y clasificar los distintos elementos del lenguaje Ruby: variables, tipos de datos, operadores, palabras reservadas, delimitadores y comentarios. Cada token identificado representa la unidad mínima con significado dentro del código fuente.

## Estructura del proyecto

El trabajo está dividido en aportes individuales dentro de un único archivo `lexer.py`. Cada integrante es responsable de implementar un conjunto específico de tokens, y de crear un algoritmo de prueba en Ruby que ejercite dichos tokens. El lexer se ejecuta sobre cada algoritmo y genera un log con la lista completa de tokens reconocidos.

## Integrantes y responsabilidades

**Annabella Sánchez** trabaja en el reconocimiento de variables (locales, globales, de instancia y constantes) y los tipos primitivos del lenguaje: enteros, flotantes, strings, booleanos, nil y símbolos. También maneja la tokenización de estructuras Array.

**Cristian Intriago** implementa los operadores aritméticos, de asignación compuesta, de comparación y lógicos, cubriendo las expresiones más comunes en cualquier programa Ruby.

**Valentina Falconi** se encarga de los delimitadores (paréntesis, corchetes, llaves, puntos, etc.), los operadores de rango (`..` y `...`), y el tratamiento de comentarios de línea y multilínea.

## Organización del repositorio

```
lp-ruby-project/
├── lexer.py           # Analizador léxico principal
├── algoritmos/        # Programas Ruby de prueba por integrante
└── logs/              # Logs de salida generados por el lexer
```

## Formato de archivos

Cada integrante debe respetar el siguiente formato al nombrar y ubicar sus archivos.

**Algoritmo de prueba** — guardar en la carpeta `algoritmos/`:
```
algoritmos/algoritmoN.rb
```
Donde `N` es el número de integrante (1, 2 o 3). Ejemplo: `algoritmos/algoritmo2.rb`.

**Log léxico** — guardar en la carpeta `logs/`:
```
logs/lexico-NombreApellido-DD-MM-YYYY-HHhMM.txt
```
Donde `NombreApellido` es el nombre del integrante sin espacios ni tildes, y la fecha/hora corresponde al momento de ejecución del lexer. Ejemplos:
```
logs/lexico-AnnabellaSanchez-22-06-2026-14h30.txt
logs/lexico-CristianIntriago-22-06-2026-15h00.txt
logs/lexico-ValentinaFalconi-22-06-2026-15h30.txt
```

## Cómo ejecutar

Requiere Python 3 y la librería PLY:

```bash
pip install ply
python lexer.py algoritmos/algoritmo1.rb
```

El log se genera automáticamente en la carpeta `logs/` con el nombre del integrante y la fecha/hora de ejecución.
