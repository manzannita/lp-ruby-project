# =============================================================================
# ANALIZADOR SEMÁNTICO — Ruby (subconjunto)
# Recorre el AST producido por parser.analizar() y verifica reglas semánticas.
# Cada integrante implementa sus reglas dentro de su bloque APORTE INTEGRANTE.
# =============================================================================
import sys
import os
from datetime import datetime

from parser import analizar as _analizar_sintactico


# ── Categorías de error semántico (para clasificar en la GUI y el log) ───────
CAT_IDENTIFICADORES = 'Identificadores'
CAT_OPERACIONES     = 'Operaciones'
CAT_CONTROL         = 'Estructuras de control'
CAT_RETORNO         = 'Retorno de funciones'


# =============================================================================
# TABLA DE SÍMBOLOS  (parte de la estructura base — APORTE INTEGRANTE 1)
# Maneja ámbitos para variables locales y tablas globales para constantes,
# variables globales/de instancia y funciones. Modela el alcance de Ruby:
# los métodos NO ven las variables locales externas, pero constantes,
# globales y funciones son visibles desde cualquier punto.
# =============================================================================
class TablaSimbolos:
    def __init__(self):
        self.ambitos     = [{}]   # pila de ámbitos de variables locales; [0] = global
        self.constantes  = {}     # nombre -> {'tipo'}
        self.globales    = {}     # $var
        self.instancias  = {}     # @var
        self.funciones   = {}     # nombre -> {'aridad_min', 'aridad_max'}

    # ── ámbitos de locales ───────────────────────────────────────────────
    def abrir_ambito(self):
        self.ambitos.append({})

    def cerrar_ambito(self):
        if len(self.ambitos) > 1:
            self.ambitos.pop()

    def declarar_local(self, nombre, tipo=None):
        self.ambitos[-1][nombre] = {'tipo': tipo}

    def existe_local(self, nombre):
        # Alcance de método: solo el ámbito actual (Ruby no encadena locales).
        return nombre in self.ambitos[-1]

    # ── constantes / globales / instancia ────────────────────────────────
    def declarar_constante(self, nombre, tipo=None):
        self.constantes[nombre] = {'tipo': tipo}

    def existe_constante(self, nombre):
        return nombre in self.constantes

    def declarar_global(self, nombre, tipo=None):
        self.globales[nombre] = {'tipo': tipo}

    def declarar_instancia(self, nombre, tipo=None):
        self.instancias[nombre] = {'tipo': tipo}

    # ── funciones ─────────────────────────────────────────────────────────
    def registrar_funcion(self, nombre, aridad_min, aridad_max):
        self.funciones[nombre] = {'aridad_min': aridad_min, 'aridad_max': aridad_max}

    def existe_funcion(self, nombre):
        return nombre in self.funciones

    def buscar(self, nombre):
        """Busca un símbolo por nombre (usado para inferencia de tipos)."""
        if nombre in self.ambitos[-1]:
            return self.ambitos[-1][nombre]
        for tabla in (self.constantes, self.globales, self.instancias):
            if nombre in tabla:
                return tabla[nombre]
        return None


# =============================================================================
# ANALIZADOR SEMÁNTICO
# =============================================================================
class AnalizadorSemantico:

    # =========================================================================
    # INICIO APORTE INTEGRANTE 1 — Annabella Sánchez
    # Estructura base: recorrido del AST (visitantes), tabla de símbolos,
    # registro/clasificación de errores e inferencia de tipos.
    # Reglas propias: identificador declarado antes de usarse y
    # constante inmutable.
    # =========================================================================

    # Métodos "builtin" de Ruby que no requieren declaración previa. Evita
    # falsos positivos al llamar métodos del lenguaje o de entrada/salida.
    BUILTINS = {
        'puts', 'print', 'gets', 'p', 'require',
        'to_f', 'to_i', 'to_s', 'to_sym', 'to_a', 'chomp', 'chars',
        'sum', 'length', 'size', 'push', 'pop', 'shift', 'first', 'last',
        'nil?', 'empty?', 'include?', 'key?', 'keys', 'values',
        'map', 'each', 'select', 'reject', 'reduce', 'sort', 'reverse',
        'abs', 'round', 'ceil', 'floor', 'upcase', 'downcase', 'min', 'max',
    }

    def __init__(self):
        self.errores = []
        self.tabla = TablaSimbolos()
        self._profundidad_bucle = 0   # >0 mientras se recorre el cuerpo de un bucle

    # ── Registro de errores clasificados ─────────────────────────────────
    def error(self, categoria, mensaje, linea=0, columna=0):
        self.errores.append({
            'categoria': categoria,
            'mensaje': mensaje,
            'linea': linea,
            'columna': columna,
        })

    # ── Punto de entrada del recorrido ────────────────────────────────────
    def analizar(self, arbol):
        if not arbol or arbol[0] != 'programa':
            return
        # Primera pasada: registrar todas las funciones (permite llamadas
        # antes de la definición textual, como en Ruby).
        self._recolectar_funciones(arbol[1])
        # Segunda pasada: recorrido en orden verificando las reglas.
        for sentencia in arbol[1]:
            self.visitar(sentencia)

    # ── Recolección de definiciones de función (nombre + aridad) ──────────
    def _recolectar_funciones(self, nodo):
        if isinstance(nodo, tuple):
            if nodo and nodo[0] == 'def':
                amin, amax = self._aridad(nodo[2])
                self.tabla.registrar_funcion(nodo[1], amin, amax)
            for hijo in nodo[1:]:
                self._recolectar_funciones(hijo)
        elif isinstance(nodo, list):
            for hijo in nodo:
                self._recolectar_funciones(hijo)

    @staticmethod
    def _aridad(params):
        """Devuelve (mínimo, máximo) de argumentos aceptados por la función.
        Máximo es float('inf') si hay parámetro splat (*args)."""
        minimo = 0
        maximo = 0
        hay_splat = False
        for p in params:
            if isinstance(p, str):
                minimo += 1
                maximo += 1
            elif isinstance(p, tuple):
                if p[0] == 'param_splat':
                    hay_splat = True
                elif p[0] == 'param_opcional':
                    maximo += 1
        return minimo, (float('inf') if hay_splat else maximo)

    # ── Despacho del visitante por tipo de nodo ───────────────────────────
    def visitar(self, nodo):
        if not isinstance(nodo, tuple) or not nodo:
            return
        metodo = getattr(self, '_v_' + str(nodo[0]), None)
        if metodo:
            metodo(nodo)

    def _visitar_lista(self, sentencias):
        for s in sentencias:
            self.visitar(s)

    # ── Utilidades base ───────────────────────────────────────────────────
    def _linea(self, nodo):
        """Busca recursivamente la primera línea disponible en un subárbol.
        Los nodos hoja (var, literal) y varios nodos de sentencia llevan su
        línea como último elemento entero."""
        if isinstance(nodo, tuple):
            if len(nodo) >= 2 and isinstance(nodo[-1], int) \
                    and nodo[0] in ('var', 'literal', 'llamada', 'break', 'next'):
                return nodo[-1]
            for hijo in nodo[1:]:
                l = self._linea(hijo)
                if l:
                    return l
        elif isinstance(nodo, list):
            for hijo in nodo:
                l = self._linea(hijo)
                if l:
                    return l
        return 0

    @staticmethod
    def _clase_identificador(nombre):
        if nombre.startswith('@'):
            return 'instancia'
        if nombre.startswith('$'):
            return 'global'
        if nombre[:1].isupper():
            return 'constante'
        return 'local'

    def _inferir_tipo(self, nodo):
        """Inferencia de tipo básica (usada por la regla de tipos del
        Integrante 2). Devuelve un nombre de tipo o None si es desconocido."""
        if not isinstance(nodo, tuple) or not nodo:
            return None
        t = nodo[0]
        if t == 'literal':
            v = nodo[1]
            if isinstance(v, bool):
                return 'Boolean'
            if isinstance(v, int):
                return 'Integer'
            if isinstance(v, float):
                return 'Float'
            if isinstance(v, str):
                if v in ('true', 'false'):
                    return 'Boolean'
                if v == 'nil':
                    return 'Nil'
                if v.startswith(':'):
                    return 'Symbol'
                return 'String'
        elif t == 'array':
            return 'Array'
        elif t == 'hash':
            return 'Hash'
        elif t in ('rango_inclusivo', 'rango_exclusivo'):
            return 'Range'
        elif t == 'var':
            info = self.tabla.buscar(nodo[1])
            return info.get('tipo') if info else None
        elif t == 'binop':
            op = nodo[1]
            if op in ('==', '!=', '<', '>', '<=', '>=', '&&', '||'):
                return 'Boolean'
            ti = self._inferir_tipo(nodo[2])
            td = self._inferir_tipo(nodo[3])
            if ti in ('Integer', 'Float') and td in ('Integer', 'Float'):
                return 'Float' if 'Float' in (ti, td) else 'Integer'
            if op in ('+', '*') and ti == td and ti in ('String', 'Array'):
                return ti
        elif t == 'not':
            return 'Boolean'
        return None

    def _declarar_objetivo(self, objetivo, tipo=None):
        """Declara el destino de una asignación en la tabla de símbolos
        (guardando el tipo inferido) y aplica la regla de constante inmutable."""
        if not (isinstance(objetivo, tuple) and objetivo and objetivo[0] == 'var'):
            return
        nombre = objetivo[1]
        linea = objetivo[2] if len(objetivo) >= 3 else 0
        clase = self._clase_identificador(nombre)

        if clase == 'constante':
            # ── REGLA (#26): una constante no puede reasignarse ───────────
            if self.tabla.existe_constante(nombre):
                self.error(CAT_IDENTIFICADORES,
                           f"La constante '{nombre}' ya fue definida y no puede "
                           f"reasignarse", linea)
            else:
                self.tabla.declarar_constante(nombre, tipo)
        elif clase == 'local':
            self.tabla.declarar_local(nombre, tipo)
        elif clase == 'global':
            self.tabla.declarar_global(nombre, tipo)
        elif clase == 'instancia':
            self.tabla.declarar_instancia(nombre, tipo)

    # ── Visitantes: asignaciones ──────────────────────────────────────────
    def _v_asignacion(self, nodo):
        # ('asignacion', ('var', nombre, ln), expr)
        self.visitar(nodo[2])            # el lado derecho se evalúa primero
        self._declarar_objetivo(nodo[1], self._inferir_tipo(nodo[2]))

    def _v_asignacion_operador(self, nodo):
        # ('asignacion_operador', op, ('var', nombre, ln), expr)  ->  x += 1
        self.visitar(nodo[3])
        self._v_var(nodo[2])             # x se usa: debe estar declarada
        self._declarar_objetivo(nodo[2])

    def _v_asignacion_multiple(self, nodo):
        # ('asignacion_multiple', [lhs...], [expr...])
        for expr in nodo[2]:
            self.visitar(expr)
        for objetivo in nodo[1]:
            self._declarar_objetivo(objetivo)

    # ── Visitantes: uso de identificadores ────────────────────────────────
    def _v_var(self, nodo):
        # ('var', nombre, ln)  — uso de una variable/constante
        nombre = nodo[1]
        linea = nodo[2] if len(nodo) >= 3 else 0
        clase = self._clase_identificador(nombre)
        # ── REGLA (#26): identificador declarado antes de usarse ──────────
        if clase == 'local' and not self.tabla.existe_local(nombre):
            self.error(CAT_IDENTIFICADORES,
                       f"Identificador no definido: la variable local '{nombre}' "
                       f"se usa antes de ser declarada", linea)
        elif clase == 'constante' and not self.tabla.existe_constante(nombre):
            self.error(CAT_IDENTIFICADORES,
                       f"Identificador no definido: la constante '{nombre}' "
                       f"no ha sido declarada", linea)
        # Variables globales ($) y de instancia (@) valen nil si no se
        # asignaron: leerlas no es un error en Ruby, no se reportan.

    # ── Visitantes: llamadas a funciones/métodos ──────────────────────────
    def _v_llamada(self, nodo):
        # ('llamada', nombre, [args], ln)
        nombre = nodo[1]
        args = nodo[2]
        linea = nodo[3] if len(nodo) >= 4 else 0
        for a in args:
            self.visitar(a)
        # ── REGLA (#26): función declarada antes de usarse ────────────────
        if not self.tabla.existe_funcion(nombre) and nombre not in self.BUILTINS:
            self.error(CAT_IDENTIFICADORES,
                       f"Identificador no definido: la función '{nombre}' "
                       f"no ha sido declarada", linea)
        # Hook para la regla de aridad (Integrante 3).
        self.regla_aridad(nombre, args, linea)

    def _v_comando(self, nodo):
        # ('comando', nombre, expr)  — llamada sin paréntesis: "nombre arg"
        self.visitar(nodo[2])
        nombre = nodo[1]
        if not self.tabla.existe_funcion(nombre) and nombre not in self.BUILTINS:
            self.error(CAT_IDENTIFICADORES,
                       f"Identificador no definido: '{nombre}' no ha sido declarada",
                       self._linea(nodo[2]))

    def _v_llamada_metodo(self, nodo):
        # ('llamada_metodo', objeto, metodo[, args])  — nota.to_f, resultado.push(v)
        # El objeto es una expresión: al visitarla se verifican sus identificadores.
        self.visitar(nodo[1])
        if len(nodo) >= 4:
            self._visitar_lista(nodo[3])

    def _v_indexar(self, nodo):
        # ('indexar', objeto, indice)  — datos["a"], persona[:clave]
        self.visitar(nodo[1])
        self.visitar(nodo[2])

    def _v_gets(self, nodo):
        # ('gets',)  — lectura de entrada; no hay identificadores que verificar.
        pass

    def _v_imprimir(self, nodo):
        # ('imprimir', 'puts'|'print', [args])
        self._visitar_lista(nodo[2])

    # ── Visitantes: definición de función ─────────────────────────────────
    def _v_def(self, nodo):
        # ('def', nombre, params, cuerpo)
        params = nodo[2]
        cuerpo = nodo[3]
        self.tabla.abrir_ambito()
        for p in params:
            if isinstance(p, str):
                self.tabla.declarar_local(p)
            elif isinstance(p, tuple):
                if p[0] == 'param_splat':
                    self.tabla.declarar_local(p[1])
                elif p[0] == 'param_opcional':
                    self.visitar(p[2])          # el valor por defecto se evalúa
                    self.tabla.declarar_local(p[1])
        self._visitar_lista(cuerpo)
        self.tabla.cerrar_ambito()

    def _v_return(self, nodo):
        # ('return', expr | None)
        if len(nodo) >= 2 and nodo[1] is not None:
            self.visitar(nodo[1])

    # ── Visitantes: estructuras de control ────────────────────────────────
    def _v_if(self, nodo):
        # ('if', cond, cuerpo, [('elsif', cond, cuerpo)...], ('else', cuerpo)|None)
        self.visitar(nodo[1])
        self.regla_condicion(nodo[1], 'if')     # hook Integrante 2
        self._visitar_lista(nodo[2])
        for rama in nodo[3]:
            self.visitar(rama[1])
            self.regla_condicion(rama[1], 'elsif')
            self._visitar_lista(rama[2])
        if nodo[4]:
            self._visitar_lista(nodo[4][1])

    def _v_mientras(self, nodo):
        # ('mientras', cond, cuerpo)
        self.visitar(nodo[1])
        self.regla_condicion(nodo[1], 'while')  # hook Integrante 2
        self._profundidad_bucle += 1
        self._visitar_lista(nodo[2])
        self._profundidad_bucle -= 1

    def _v_para(self, nodo):
        # ('para', var, iterable, cuerpo)  — for var in iterable
        self.visitar(nodo[2])
        self.tabla.declarar_local(nodo[1])
        self._profundidad_bucle += 1
        self._visitar_lista(nodo[3])
        self._profundidad_bucle -= 1

    def _v_cada(self, nodo):
        # ('cada', expr, var, cuerpo)  — expr.each do |var| ... end
        self.visitar(nodo[1])
        self.tabla.declarar_local(nodo[2])
        self._profundidad_bucle += 1
        self._visitar_lista(nodo[3])
        self._profundidad_bucle -= 1

    # ── Visitantes: expresiones compuestas (solo recorren sus hijos) ──────
    def _v_binop(self, nodo):
        # ('binop', op, izq, der)
        self.visitar(nodo[2])
        self.visitar(nodo[3])
        self.regla_tipos_binop(nodo)            # hook Integrante 2

    def _v_not(self, nodo):
        self.visitar(nodo[1])

    def _v_array(self, nodo):
        self._visitar_lista(nodo[1])

    def _v_hash(self, nodo):
        for clave, valor in nodo[1]:
            self.visitar(clave)
            self.visitar(valor)

    def _v_rango_inclusivo(self, nodo):
        self.visitar(nodo[1])
        self.visitar(nodo[2])

    def _v_rango_exclusivo(self, nodo):
        self.visitar(nodo[1])
        self.visitar(nodo[2])

    def _v_literal(self, nodo):
        pass

    # ── Sentencias de control de flujo break / next ───────────────────────
    # (El parser aún no las produce como nodo; cuando lo haga, estos
    #  visitantes delegan la verificación en la regla del Integrante 3.)
    def _v_break(self, nodo):
        self.regla_break_next('break', self._linea(nodo))

    def _v_next(self, nodo):
        self.regla_break_next('next', self._linea(nodo))

    # ── HOOKS de reglas de otros integrantes ──────────────────────────────
    # La estructura base los invoca durante el recorrido. Aquí son stubs
    # (no hacen nada); cada integrante los reemplaza en su bloque.
    def regla_condicion(self, cond, contexto):
        """Integrante 2: la condición de if/while debe ser booleana."""
        pass

    def regla_tipos_binop(self, nodo):
        """Integrante 2: compatibilidad de tipos en operaciones aritméticas."""
        pass

    def regla_aridad(self, nombre, args, linea):
        """Integrante 3: la aridad de la llamada debe coincidir con la def."""
        pass

    def regla_break_next(self, palabra, linea):
        """Integrante 3: break/next solo dentro de un bucle."""
        pass

    # =========================================================================
    # FIN APORTE INTEGRANTE 1 — Annabella Sánchez
    # =========================================================================


    # =========================================================================
    # INICIO APORTE INTEGRANTE 2 — Cristian Intriago
    # Reglas semánticas: compatibilidad de tipos en operaciones aritméticas
    # y condición booleana en if/while. (Issue #27)
    # =========================================================================
    _OP_ARITMETICOS  = {'+', '-', '*', '/', '%', '**'}
    _OP_BOOLEANOS    = {'==', '!=', '<', '>', '<=', '>=', '&&', '||'}
    _TIPOS_NUMERICOS = {'Integer', 'Float'}

    def regla_tipos_binop(self, nodo):
        # ('binop', op, izq, der)
        # ── REGLA (#27): no se permiten operaciones aritméticas entre tipos
        #    incompatibles (p. ej. Integer + String) sin conversión explícita.
        op = nodo[1]
        if op not in self._OP_ARITMETICOS:
            return
        ti = self._inferir_tipo(nodo[2])
        td = self._inferir_tipo(nodo[3])
        # Si algún tipo es desconocido no se puede verificar sin arriesgar
        # falsos positivos (variables sin tipo, retornos de método, etc.).
        if ti is None or td is None:
            return
        if ti in self._TIPOS_NUMERICOS and td in self._TIPOS_NUMERICOS:
            return
        # + y * concatenan/repiten String y Array del mismo tipo.
        if op in ('+', '*') and ti == td and ti in ('String', 'Array'):
            return
        self.error(CAT_OPERACIONES,
                   f"Operación aritmética entre tipos incompatibles: "
                   f"'{ti} {op} {td}' requiere conversión explícita",
                   self._linea(nodo))

    def regla_condicion(self, cond, contexto):
        # ── REGLA (#27): la condición de un if/while debe evaluar a un valor
        #    booleano o evaluable como tal.
        if not self._condicion_evaluable(cond):
            self.error(CAT_CONTROL,
                       f"La condición de '{contexto}' debería ser una expresión "
                       f"booleana (comparación o valor lógico)",
                       self._linea(cond))

    def _condicion_evaluable(self, cond):
        """True si la condición produce (o puede producir) un booleano."""
        if not isinstance(cond, tuple) or not cond:
            return True
        t = cond[0]
        if t == 'binop':
            return cond[1] in self._OP_BOOLEANOS
        if t == 'not':
            return True
        if t == 'literal':
            return self._inferir_tipo(cond) == 'Boolean'
        # Literales de colección/rango no son condiciones booleanas válidas.
        if t in ('array', 'hash', 'rango_inclusivo', 'rango_exclusivo'):
            return False
        # Variables, llamadas, métodos, indexación: su valor puede evaluarse
        # como booleano (truthy/falsy). Se aceptan para no generar falsos
        # positivos sobre expresiones de tipo desconocido.
        return True

    # Clasificación de operadores binarios producidos por el parser.
    OPS_ARITMETICOS  = {'+', '-', '*', '/', '%', '**'}
    OPS_COMPARACION  = {'==', '!=', '<', '>', '<=', '>=', '<=>'}
    OPS_LOGICOS      = {'&&', '||', 'and', 'or'}

    def _tipo_expresion(self, nodo):
        """Extiende la inferencia base a expresiones compuestas: comparaciones,
        lógicos y 'not' producen Boolean; los aritméticos, un tipo numérico o
        el de sus operandos. Devuelve None si el tipo es desconocido."""
        if not isinstance(nodo, tuple) or not nodo:
            return None
        if nodo[0] == 'not':
            return 'Boolean'
        if nodo[0] == 'binop':
            op = nodo[1]
            if op in self.OPS_COMPARACION or op in self.OPS_LOGICOS:
                return 'Boolean'
            if op in self.OPS_ARITMETICOS:
                ti = self._tipo_expresion(nodo[2])
                td = self._tipo_expresion(nodo[3])
                if 'Float' in (ti, td):
                    return 'Float'
                if ti == td:
                    return ti          # Integer, String (concatenación), etc.
                return None
            return None
        return self._inferir_tipo(nodo)

    def regla_tipos_binop(self, nodo):
        # ── REGLA (#27): compatibilidad de tipos en operaciones aritméticas ──
        # No se permiten operaciones como Integer + String sin conversión
        # explícita. Solo se reporta cuando AMBOS tipos se conocen: si alguno
        # es desconocido (variables sin tipo inferido) no se asume error,
        # para evitar falsos positivos.
        op = nodo[1]
        if op not in self.OPS_ARITMETICOS:
            return
        ti = self._tipo_expresion(nodo[2])
        td = self._tipo_expresion(nodo[3])
        if ti is None or td is None:
            return

        numericos = ('Integer', 'Float')
        compatible = ti in numericos and td in numericos
        if op == '+':
            # Ruby permite concatenar String + String y Array + Array.
            compatible = compatible or (ti == td and ti in ('String', 'Array'))
        elif op == '*':
            # Ruby permite repetición: "ab" * 3, [1] * 3.
            compatible = compatible or (ti in ('String', 'Array') and td == 'Integer')

        if not compatible:
            self.error(CAT_OPERACIONES,
                       f"Tipos incompatibles en operación aritmética: "
                       f"{ti} {op} {td} no está permitido sin conversión explícita",
                       self._linea(nodo))

    def regla_condicion(self, cond, contexto):
        # ── REGLA (#27): la condición de if/while debe ser booleana ──────────
        # Se acepta todo lo que evalúa (o puede evaluar) a booleano:
        # comparaciones, lógicos, negaciones, true/false/nil y expresiones de
        # tipo desconocido (variables, llamadas). Se reporta cuando el tipo se
        # conoce y NO es booleano, como en «if 5» o «while "texto"».
        tipo = self._tipo_expresion(cond)
        if tipo is not None and tipo not in ('Boolean', 'Nil'):
            self.error(CAT_CONTROL,
                       f"La condición del '{contexto}' debe evaluar a un valor "
                       f"booleano, pero es de tipo {tipo}",
                       self._linea(cond))

    # =========================================================================
    # FIN APORTE INTEGRANTE 2 — Cristian Intriago
    # =========================================================================


    # =========================================================================
    # INICIO APORTE INTEGRANTE 3 — Valentina Falconi
    # Reglas semánticas: break/next dentro de bucle y aridad de funciones.
    # Reemplazar los hooks:
    #   def regla_break_next(self, palabra, linea): ...  (usar self._profundidad_bucle)
    #   def regla_aridad(self, nombre, args, linea): ...  (usar self.tabla.funciones)
    # (Issue #28)
    # =========================================================================
    def regla_break_next(self, palabra, linea):
        # ── REGLA (#28): break/next solo dentro de un bucle ──────────────────
        if self._profundidad_bucle == 0:
            self.error(
                CAT_CONTROL,
                f"'{palabra}' fuera de un bucle: solo puede usarse dentro "
                f"de while, for o each",
                linea
            )

    def regla_aridad(self, nombre, args, linea):
        # ── REGLA (#28): aridad de la llamada debe coincidir con la def ───────
        if not self.tabla.existe_funcion(nombre):
            return
        info = self.tabla.funciones[nombre]
        n = len(args)
        amin = info['aridad_min']
        amax = info['aridad_max']
        if amax == float('inf'):
            if n < amin:
                self.error(
                    CAT_RETORNO,
                    f"La función '{nombre}' espera al menos {amin} argumento(s) "
                    f"pero se llamó con {n}",
                    linea
                )
        else:
            if n < amin or n > amax:
                rango = f"{amin}" if amin == amax else f"{amin}–{amax}"
                self.error(
                    CAT_RETORNO,
                    f"La función '{nombre}' espera {rango} argumento(s) "
                    f"pero se llamó con {n}",
                    linea
                )
    # =========================================================================
    # FIN APORTE INTEGRANTE 3 — Valentina Falconi
    # =========================================================================


# =============================================================================
# FUNCIÓN PÚBLICA PARA LA INTERFAZ GRÁFICA
# Retorna dict: {ok, errores, errores_sintacticos, arbol, tabla_simbolos}
# =============================================================================
def analizar(codigo):
    sint = _analizar_sintactico(codigo)
    if not sint['ok']:
        # El análisis semántico requiere un AST válido: si hay errores de
        # sintaxis, se reportan esos primero.
        return {
            'ok': False,
            'errores': [],
            'errores_sintacticos': sint['errores'],
            'arbol': sint['arbol'],
            'tabla_simbolos': None,
        }

    an = AnalizadorSemantico()
    an.analizar(sint['arbol'])
    return {
        'ok': len(an.errores) == 0,
        'errores': an.errores,
        'errores_sintacticos': [],
        'arbol': sint['arbol'],
        'tabla_simbolos': an.tabla,
    }


def analizar_archivo(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    return analizar(source)


def construir_log(resultado, author, fuente):
    """Construye el texto del log de análisis semántico (reutilizado por la
    GUI y por generate_log)."""
    now = datetime.now().strftime('%d-%m-%Y-%Hh%M')
    lineas = [
        f'Archivo fuente : {fuente}',
        f'Desarrollador  : {author}',
        f'Fecha/Hora     : {now}',
    ]
    if resultado['errores_sintacticos']:
        lineas.append('Resultado      : NO ANALIZADO (errores sintácticos previos)')
        lineas.append('=' * 60)
        lineas.append('ERRORES SINTÁCTICOS (corregir antes del análisis semántico)')
        lineas.append('=' * 60)
        for err in resultado['errores_sintacticos']:
            lineas.append(f'  Línea {err["linea"]}, Col {err["columna"]}: {err["mensaje"]}')
    else:
        estado = 'VÁLIDO' if resultado['ok'] else 'CON ERRORES'
        lineas.append(f'Resultado      : {estado}')
        lineas.append(f'Total errores  : {len(resultado["errores"])}')
        lineas.append('=' * 60)
        if resultado['errores']:
            lineas.append('ERRORES SEMÁNTICOS')
            lineas.append('=' * 60)
            for err in resultado['errores']:
                lineas.append(f'  [{err["categoria"]}] Línea {err["linea"]}: '
                              f'{err["mensaje"]}')
        else:
            lineas.append('Análisis semántico completado sin errores.')
    return '\n'.join(lineas) + '\n'


def generate_log(filepath, nombre_dev=""):
    resultado = analizar_archivo(filepath)
    author = nombre_dev or 'Desconocido'
    now = datetime.now().strftime('%d-%m-%Y-%Hh%M')
    os.makedirs('logs', exist_ok=True)
    log_name = f'logs/semantico-{author}-{now}.txt'
    with open(log_name, 'w', encoding='utf-8') as f:
        f.write(construir_log(resultado, author, filepath))
    print(f'Log generado: {log_name}')
    return log_name


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python semantico.py <archivo.rb>')
        sys.exit(1)
    res = analizar_archivo(sys.argv[1])
    if res['errores_sintacticos']:
        print(f'✘ {len(res["errores_sintacticos"])} error(es) de sintaxis '
              f'(no se hizo análisis semántico).')
    elif res['ok']:
        print('✔ Análisis semántico correcto.')
    else:
        print(f'✘ {len(res["errores"])} error(es) semántico(s):')
        for e in res['errores']:
            print(f'   [{e["categoria"]}] Línea {e["linea"]}: {e["mensaje"]}')
