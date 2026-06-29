# #=============================================================================
# ANALIZADOR SINTÁCTICO — Ruby (subconjunto) · PLY (yacc)
# Cada integrante implementa sus reglas dentro de su bloque APORTE INTEGRANTE.
# =============================================================================
import ply.yacc as yacc
import sys
import os
from datetime import datetime

from lexer import tokens, lexer  # tokens y lexer de la fase léxica


# =============================================================================
# WRAPPER DEL LEXER — descarta comentarios para el parser
# (no modifica la fase léxica; los comentarios siguen apareciendo en su tabla)
# =============================================================================
class _LexerSintactico:
    """Envuelve el lexer y omite los tokens de comentario, que no forman
    parte de la gramática. Conserva NEWLINE y SEMICOLON como separadores."""
    _OMITIR = {'COMMENT_SINGLE', 'COMMENT_MULTI'}

    def __init__(self, base):
        self.base = base

    def input(self, data):
        self.base.input(data)

    def token(self):
        tok = self.base.token()
        while tok is not None and tok.type in self._OMITIR:
            tok = self.base.token()
        return tok

    def __getattr__(self, name):
        return getattr(self.base, name)


# =============================================================================
# REGISTRO DE ERRORES SINTÁCTICOS
# =============================================================================
errores_sintacticos = []
_codigo_fuente = ""


def _columna(lexpos):
    """Calcula la columna (1-based) a partir de la posición absoluta."""
    if lexpos is None:
        return 0
    inicio = _codigo_fuente.rfind('\n', 0, lexpos)
    return lexpos - inicio


# =============================================================================
# INICIO APORTE INTEGRANTE 1 — Annabella Sánchez
# Estructura base del parser, precedencia, manejo de errores,
# asignación simple, if/elsif/else, Array y función con retorno.
# =============================================================================

# ── Precedencia de operadores (base para todos los integrantes) ──────────────
# Va de menor (arriba) a mayor (abajo) prioridad. Los integrantes 2 y 3 usan
# estos niveles al definir sus reglas de expresiones aritméticas, booleanas
# y de rango.
precedence = (
    ('left', 'OR_OP'),
    ('left', 'AND_OP'),
    ('right', 'NOT_OP'),
    ('nonassoc', 'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE'),
    ('left', 'DOTDOT', 'DOTDOTDOT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MODULO'),
    ('right', 'POWER'),
)

start = 'programa'


# ── Regla inicial y estructura del programa ──────────────────────────────────
def p_programa(p):
    'programa : cuerpo'
    p[0] = ('programa', p[1])


# Un cuerpo es una secuencia de sentencias rodeada opcionalmente por
# separadores (saltos de línea o ';'). Se reutiliza en if, while, def, etc.
def p_cuerpo_vacio(p):
    'cuerpo : sep_opt'
    p[0] = []


def p_cuerpo_sentencias(p):
    'cuerpo : sep_opt sentencias sep_opt'
    p[0] = p[2]


def p_sentencias_lista(p):
    'sentencias : sentencias sep sentencia'
    p[0] = p[1] + [p[3]]


def p_sentencias_una(p):
    'sentencias : sentencia'
    p[0] = [p[1]]


# ── Separadores de sentencias: NEWLINE o ';' (uno o más) ─────────────────────
def p_sep(p):
    '''sep : sep NEWLINE
           | sep SEMICOLON
           | NEWLINE
           | SEMICOLON'''
    pass


def p_sep_opt(p):
    '''sep_opt : sep
               | empty'''
    pass


def p_empty(p):
    'empty :'
    pass


# ── Sentencia base: una expresión suelta ─────────────────────────────────────
# Cada construcción agrega su propia alternativa a 'sentencia' (en este bloque
# y en los de los integrantes 2 y 3), sin tener que tocar esta regla.
def p_sentencia_expresion(p):
    'sentencia : expresion'
    p[0] = p[1]


# ── Asignación simple:  x = expr  (issue #15) ────────────────────────────────
def p_sentencia_asignacion(p):
    'sentencia : asignacion_simple'
    p[0] = p[1]


def p_asignacion_simple(p):
    'asignacion_simple : lhs ASSIGN expresion'
    p[0] = ('asignacion', p[1], p[3])


def p_lhs(p):
    '''lhs : ID_LOCAL
           | ID_CONSTANTE
           | ID_INSTANCIA
           | ID_GLOBAL'''
    p[0] = ('var', p[1])


# ── Condicional if / elsif / else / end  (issue #15) ─────────────────────────
def p_sentencia_condicional(p):
    'sentencia : condicional'
    p[0] = p[1]


def p_condicional(p):
    'condicional : IF expresion cuerpo lista_elsif parte_else END'
    p[0] = ('if', p[2], p[3], p[4], p[5])


def p_lista_elsif(p):
    'lista_elsif : lista_elsif ELSIF expresion cuerpo'
    p[0] = p[1] + [('elsif', p[3], p[4])]


def p_lista_elsif_vacia(p):
    'lista_elsif : empty'
    p[0] = []


def p_parte_else(p):
    'parte_else : ELSE cuerpo'
    p[0] = ('else', p[2])


def p_parte_else_vacia(p):
    'parte_else : empty'
    p[0] = None


# ── Definición de función con retorno  (issue #16) ───────────────────────────
def p_sentencia_definicion(p):
    'sentencia : definicion_funcion'
    p[0] = p[1]


def p_definicion_funcion(p):
    'definicion_funcion : DEF ID_LOCAL parametros cuerpo END'
    p[0] = ('def', p[2], p[3], p[4])


def p_parametros_con_parentesis(p):
    '''parametros : LPAREN lista_parametros RPAREN
                  | LPAREN RPAREN'''
    p[0] = p[2] if len(p) == 4 else []


def p_parametros_sin_parentesis(p):
    'parametros : empty'
    p[0] = []


# Lista de parámetros posicionales simples. Los integrantes 2 (*args) y 3
# (parámetro opcional con valor por defecto) extienden 'lista_parametros'.
def p_lista_parametros(p):
    '''lista_parametros : lista_parametros COMMA ID_LOCAL
                        | ID_LOCAL'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


# ── Sentencia return  (issue #16) ────────────────────────────────────────────
def p_sentencia_retorno(p):
    'sentencia : retorno'
    p[0] = p[1]


def p_retorno(p):
    '''retorno : RETURN expresion
               | RETURN'''
    p[0] = ('return', p[2] if len(p) == 3 else None)


# ── Expresiones base / primarios (andamiaje para todos los integrantes) ──────
# El Integrante 2 amplía 'expresion' con operadores aritméticos/booleanos y el
# Integrante 3 con rangos; todos se apoyan en estos primarios.
def p_expresion_primario(p):
    'expresion : primario'
    p[0] = p[1]


def p_primario_literal(p):
    '''primario : INTEGER
                | FLOAT
                | STRING
                | SYMBOL
                | BOOLEAN
                | NIL'''
    p[0] = ('literal', p[1])


def p_primario_identificador(p):
    '''primario : ID_LOCAL
                | ID_CONSTANTE
                | ID_INSTANCIA
                | ID_GLOBAL'''
    p[0] = ('var', p[1])


def p_primario_agrupado(p):
    'primario : LPAREN expresion RPAREN'
    p[0] = p[2]


def p_primario_llamada(p):
    'primario : llamada_funcion'
    p[0] = p[1]


# ── Literal Array  (issue #16) ───────────────────────────────────────────────
def p_primario_arreglo(p):
    'primario : arreglo'
    p[0] = p[1]


def p_arreglo(p):
    '''arreglo : LBRACKET RBRACKET
               | LBRACKET lista_expresiones RBRACKET'''
    p[0] = ('array', [] if len(p) == 3 else p[2])


# ── Llamada a función con paréntesis:  nombre(args) ──────────────────────────
def p_llamada_funcion(p):
    '''llamada_funcion : ID_LOCAL LPAREN RPAREN
                       | ID_LOCAL LPAREN lista_expresiones RPAREN'''
    p[0] = ('llamada', p[1], [] if len(p) == 4 else p[3])


# Lista de expresiones separadas por coma (argumentos de llamada, elementos de
# Array, etc.). Es andamiaje base reutilizado por varias reglas.
def p_lista_expresiones(p):
    '''lista_expresiones : lista_expresiones COMMA expresion
                         | expresion'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


# ── Manejo de errores de sintaxis (issue #14) ────────────────────────────────
def p_error(p):
    if p is None:
        msg = "Error de sintaxis: fin de archivo inesperado (¿falta 'end'?)"
        errores_sintacticos.append({
            'mensaje': msg, 'linea': 0, 'columna': 0, 'token': 'EOF',
        })
        print(f"[ERROR SINTÁCTICO] {msg}")
        return

    col = _columna(p.lexpos)
    msg = (f"Token inesperado '{p.value}' (tipo {p.type}) "
           f"en línea {p.lineno}, columna {col}")
    errores_sintacticos.append({
        'mensaje': msg, 'linea': p.lineno, 'columna': col, 'token': str(p.value),
    })
    print(f"[ERROR SINTÁCTICO] {msg}")
    # Recuperación simple: descartar tokens hasta un separador para seguir.
    while True:
        tok = parser.token()
        if not tok or tok.type in ('NEWLINE', 'SEMICOLON'):
            break
    parser.errok()

# =============================================================================
# FIN APORTE INTEGRANTE 1 — Annabella Sánchez
# =============================================================================


# =============================================================================
# INICIO APORTE INTEGRANTE 2 — Cristian Intriago
# Expresiones aritméticas con precedencia, expresiones booleanas,
# asignación con operador, Hash, while y función con n argumentos.
# (Agregar aquí las reglas que amplían 'expresion', 'sentencia' y
#  'lista_parametros'.)
# =============================================================================

#issue #17: Expresiones aritméticas con precedencia de operadores
# ── Operadores binarios: + - * / % ** ────────────────────────────────────────
# La precedencia y asociatividad se toman de la tabla 'precedence' definida en
# el bloque del Integrante 1: ** (mayor) > * / % > + - (menor). El paréntesis
# para alterar el orden ya está cubierto por 'primario : LPAREN expresion RPAREN'.
def p_expresion_aritmetica_binaria(p):
    '''expresion : expresion PLUS expresion
                 | expresion MINUS expresion
                 | expresion TIMES expresion
                 | expresion DIVIDE expresion
                 | expresion MODULO expresion
                 | expresion POWER expresion'''
    p[0] = ('binop', p[2], p[1], p[3])

#issue #18: Expresiones booleanas y asignación con operador
# ── Comparación: == != < > <= >= ─────────────────────────────────────────────
def p_expresion_comparacion(p):
    '''expresion : expresion EQ expresion
                 | expresion NEQ expresion
                 | expresion LT expresion
                 | expresion GT expresion
                 | expresion LE expresion
                 | expresion GE expresion'''
    p[0] = ('binop', p[2], p[1], p[3])


# ── Lógicos: && || ! y and or not (mismos tokens en el lexer) ────────────────
def p_expresion_logica_binaria(p):
    '''expresion : expresion AND_OP expresion
                 | expresion OR_OP expresion'''
    p[0] = ('binop', p[2], p[1], p[3])


def p_expresion_logica_negacion(p):
    'expresion : NOT_OP expresion'
    p[0] = ('not', p[2])


# ── Asignación con operador: x += 1, x -= 1, x *= 2, x /= 2 ──────────────────
def p_sentencia_asignacion_operador(p):
    'sentencia : asignacion_operador'
    p[0] = p[1]


def p_asignacion_operador(p):
    '''asignacion_operador : lhs PLUS_ASSIGN expresion
                           | lhs MINUS_ASSIGN expresion
                           | lhs TIMES_ASSIGN expresion
                           | lhs DIVIDE_ASSIGN expresion'''
    p[0] = ('asignacion_operador', p[2], p[1], p[3])

#issue #19: Hash, bucle while y función con n argumentos
# ── Literal Hash: { "nombre" => "Ana" } (incluye hash vacío {}) ──────────────
def p_primario_hash(p):
    'primario : hash'
    p[0] = p[1]


def p_hash(p):
    '''hash : LBRACE RBRACE
            | LBRACE lista_pares RBRACE'''
    p[0] = ('hash', [] if len(p) == 3 else p[2])


def p_lista_pares(p):
    '''lista_pares : lista_pares COMMA par
                   | par'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


def p_par(p):
    'par : expresion ARROW expresion'
    p[0] = (p[1], p[3])


# ── Bucle while: while cond ... end ──────────────────────────────────────────
def p_sentencia_while(p):
    'sentencia : WHILE expresion cuerpo END'
    p[0] = ('mientras', p[2], p[3])


# ── Función con número variable de argumentos: def suma(*numeros) ───────────
def p_lista_parametros_splat(p):
    '''lista_parametros : TIMES ID_LOCAL
                        | lista_parametros COMMA TIMES ID_LOCAL'''
    if len(p) == 3:
        p[0] = [('param_splat', p[2])]
    else:
        p[0] = p[1] + [('param_splat', p[4])]

# =============================================================================
# FIN APORTE INTEGRANTE 2 — Cristian Intriago
# =============================================================================


# =============================================================================
# INICIO APORTE INTEGRANTE 3 — Valentina Falconi
# Asignación múltiple, Range, control each/for, función con parámetro
# opcional, e impresión/solicitud de datos (puts/print/gets).
# (Agregar aquí las reglas que amplían 'expresion', 'sentencia' y
#  'lista_parametros'.)
# =============================================================================

#issue #20: Asignación múltiple y Rango
# ── Literal Range: 1..10 y 1...10 ────────────────────────────────────────────
def p_expresion_rango_inclusivo(p):
    'expresion : expresion DOTDOT expresion'
    p[0] = ('rango_inclusivo', p[1], p[3])

def p_expresion_rango_exclusivo(p):
    'expresion : expresion DOTDOTDOT expresion'
    p[0] = ('rango_exclusivo', p[1], p[3])

# ── Asignación múltiple: a, b = 1, 2 ─────────────────────────────────────────
def p_sentencia_asignacion_multiple(p):
    'sentencia : lista_lhs ASSIGN lista_expresiones'
    p[0] = ('asignacion_multiple', p[1], p[3])

def p_lista_lhs_base(p):
    'lista_lhs : lhs COMMA lhs'
    p[0] = [p[1], p[3]]

def p_lista_lhs_extendida(p):
    'lista_lhs : lista_lhs COMMA lhs'
    p[0] = p[1] + [p[3]]

#issue #21: Bucle for y Iteración each
# ── Bucle for: for n in 1..10 ... end ────────────────────────────────────────
def p_sentencia_for(p):
    'sentencia : FOR ID_LOCAL IN expresion cuerpo END'
    p[0] = ('para', p[2], p[4], p[5])

# ── Iteración each: arreglo.each do |n| ... end ──────────────────────────────
def p_sentencia_each(p):
    'sentencia : expresion DOT EACH DO PIPE ID_LOCAL PIPE cuerpo END'
    p[0] = ('cada', p[1], p[6], p[8])

# ── Parámetro opcional con valor por defecto ─────────────────────────────────
def p_lista_parametros_opcional_unico(p):
    'lista_parametros : ID_LOCAL ASSIGN expresion'
    p[0] = [('param_opcional', p[1], p[3])]

def p_lista_parametros_opcional_extendida(p):
    'lista_parametros : lista_parametros COMMA ID_LOCAL ASSIGN expresion'
    p[0] = p[1] + [('param_opcional', p[3], p[5])]

#issue #22: impresión y solicitud de datos
# ── Llamada a método encadenado: gets.chomp ───────────────────────────────────
def p_primario_llamada_metodo(p):
    'primario : ID_LOCAL DOT ID_LOCAL'
    p[0] = ('llamada_metodo', p[1], p[3])

# ── Impresión sin paréntesis: puts "Hola", print "texto" ─────────────────────
def p_sentencia_comando(p):
    'sentencia : ID_LOCAL expresion'
    p[0] = ('comando', p[1], p[2])

# =============================================================================
# FIN APORTE INTEGRANTE 3 — Valentina Falconi
# =============================================================================


# =============================================================================
# CONSTRUCCIÓN DEL PARSER — no modificar
# =============================================================================
class _LoggerFiltrado(yacc.PlyLogger):
    """Oculta los avisos de 'token definido pero no usado' (esperados mientras
    los integrantes 2 y 3 aún no agregan sus reglas) pero conserva los avisos
    de conflictos y demás mensajes importantes."""
    def warning(self, msg, *args, **kwargs):
        texto = msg % args if args else msg
        if 'not used' in texto or 'unused token' in texto:
            return
        super().warning(msg, *args, **kwargs)


parser = yacc.yacc(debug=False, write_tables=False,
                   errorlog=_LoggerFiltrado(sys.stderr))
_lexer_sintactico = _LexerSintactico(lexer)


# =============================================================================
# FUNCIÓN PÚBLICA PARA LA INTERFAZ GRÁFICA
# Retorna dict: {ok, arbol, errores}
# =============================================================================
def analizar(codigo):
    global _codigo_fuente, errores_sintacticos
    _codigo_fuente = codigo
    errores_sintacticos = []
    lexer.lineno = 1
    if hasattr(lexer, 'errores'):
        lexer.errores = []
    arbol = parser.parse(codigo, lexer=_lexer_sintactico)
    return {
        'ok': len(errores_sintacticos) == 0,
        'arbol': arbol,
        'errores': errores_sintacticos,
    }


def parsear_archivo(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    return analizar(source)


def generate_log(filepath, nombre_dev=""):
    resultado = parsear_archivo(filepath)
    now = datetime.now().strftime('%d-%m-%Y-%Hh%M')
    base = os.path.splitext(os.path.basename(filepath))[0]
    author = nombre_dev or 'Desconocido'
    os.makedirs('logs', exist_ok=True)
    log_name = f'logs/sintactico-{author}-{now}.txt'

    with open(log_name, 'w', encoding='utf-8') as f:
        f.write(f'Archivo fuente : {filepath}\n')
        f.write(f'Desarrollador  : {author}\n')
        f.write(f'Fecha/Hora     : {now}\n')
        f.write(f'Resultado      : {"VÁLIDO" if resultado["ok"] else "CON ERRORES"}\n')
        f.write(f'Total errores  : {len(resultado["errores"])}\n')
        f.write('=' * 60 + '\n')
        if resultado['errores']:
            f.write('ERRORES SINTÁCTICOS\n')
            f.write('=' * 60 + '\n')
            for err in resultado['errores']:
                f.write(f'  Línea {err["linea"]}, Col {err["columna"]}: {err["mensaje"]}\n')
        else:
            f.write('Análisis sintáctico completado sin errores.\n')

    print(f'Log generado: {log_name}')
    return log_name


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python parser.py <archivo.rb>')
        sys.exit(1)
    res = parsear_archivo(sys.argv[1])
    if res['ok']:
        print('✔ Análisis sintáctico correcto.')
    else:
        print(f'✘ {len(res["errores"])} error(es) de sintaxis.')
