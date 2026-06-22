import ply.lex as lex
import sys
import os
from datetime import datetime

# =============================================================================
# TOKENS — lista completa (cada integrante agrega los suyos)
# =============================================================================
reserved = {
    'if': 'IF', 'elsif': 'ELSIF', 'else': 'ELSE', 'end': 'END',
    'while': 'WHILE', 'for': 'FOR', 'in': 'IN', 'do': 'DO',
    'def': 'DEF', 'return': 'RETURN', 'class': 'CLASS', 'module': 'MODULE',
    'true': 'BOOLEAN', 'false': 'BOOLEAN', 'nil': 'NIL',
    'and': 'AND_OP', 'or': 'OR_OP', 'not': 'NOT_OP',
    'each': 'EACH',
}

tokens = [
    # ── APORTE INTEGRANTE 1 ── Annabella Sánchez ──────────────────────────
    'ID_LOCAL', 'ID_CONSTANTE', 'ID_INSTANCIA', 'ID_GLOBAL',
    'INTEGER', 'FLOAT', 'STRING', 'SYMBOL',
    'PIPE', 'QUESTION', 'NOT_OP2',

    # ── APORTE INTEGRANTE 2 ── Cristian Intriago ──────────────────────────
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULO', 'POWER',
    'ASSIGN', 'PLUS_ASSIGN', 'MINUS_ASSIGN', 'TIMES_ASSIGN', 'DIVIDE_ASSIGN',
    'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE',
    'AND_OP2', 'OR_OP2',

    # ── APORTE INTEGRANTE 3 ── Valentina Falconi ──────────────────────────
    # (pendiente)

] + list(set(reserved.values()))


# =============================================================================
# INICIO APORTE INTEGRANTE 1 — Annabella Sánchez
# Variables, identificadores y tipos primitivos
# =============================================================================

def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING(t):
    r'(\"([^\"\\]|\\.)*\"|\'([^\'\\]|\\.)*\')'
    return t

def t_SYMBOL(t):
    r':[a-z_][a-zA-Z0-9_]*'
    return t

def t_ID_GLOBAL(t):
    r'\$[a-zA-Z_][a-zA-Z0-9_]*'
    return t

def t_ID_INSTANCIA(t):
    r'@[a-zA-Z_][a-zA-Z0-9_]*'
    return t

def t_ID_CONSTANTE(t):
    r'[A-Z][A-Z0-9_]*'
    return t

def t_ID_LOCAL_Q(t):
    r'[a-z_][a-zA-Z0-9_]*[?!]'
    t.type = 'ID_LOCAL'
    return t

def t_ID_LOCAL(t):
    r'[a-z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID_LOCAL')
    return t

t_PIPE     = r'\|'
t_QUESTION = r'\?'
t_NOT_OP2  = r'!'

# =============================================================================
# FIN APORTE INTEGRANTE 1 — Annabella Sánchez
# =============================================================================


# =============================================================================
# INICIO APORTE INTEGRANTE 2 — Cristian Intriago
# Operadores aritméticos, de asignación, comparación y lógicos
# =============================================================================

t_POWER         = r'\*\*'
t_PLUS_ASSIGN   = r'\+='
t_MINUS_ASSIGN  = r'-='
t_TIMES_ASSIGN  = r'\*='
t_DIVIDE_ASSIGN = r'/='
t_EQ            = r'=='
t_NEQ           = r'!='
t_LE            = r'<='
t_GE            = r'>='
t_AND_OP2       = r'&&'
t_OR_OP2        = r'\|\|'

t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_MODULO  = r'%'
t_ASSIGN  = r'='
t_LT      = r'<'
t_GT      = r'>'

# =============================================================================
# FIN APORTE INTEGRANTE 2 — Cristian Intriago
# =============================================================================


# =============================================================================
# INICIO APORTE INTEGRANTE 3 — Valentina Falconi
# Delimitadores, comentarios, rangos y newline
# =============================================================================

# (pendiente — Valentina agrega aquí sus tokens)

# =============================================================================
# FIN APORTE INTEGRANTE 3 — Valentina Falconi
# =============================================================================


# =============================================================================
# REGLAS COMUNES — no modificar
# =============================================================================
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t\r'

def t_error(t):
    msg = f"Carácter ilegal '{t.value[0]}' en línea {t.lexer.lineno}"
    print(f"[ERROR] {msg}")
    if not hasattr(t.lexer, 'errores'):
        t.lexer.errores = []
    t.lexer.errores.append({
        'mensaje': msg,
        'linea': t.lexer.lineno,
        'char': t.value[0],
    })
    t.lexer.skip(1)


# =============================================================================
# INSTANCIA DEL LEXER
# =============================================================================
lexer = lex.lex()
lexer.errores = []


# =============================================================================
# FUNCIÓN PÚBLICA PARA LA INTERFAZ GRÁFICA
# Retorna lista de dicts: {tipo, valor, linea, pos}
# =============================================================================
def analizar(codigo, nombre_dev=""):
    lexer.errores = []
    lexer.lineno = 1
    lexer.input(codigo)
    tokens_list = []
    for tok in lexer:
        tokens_list.append({
            'tipo': tok.type,
            'valor': str(tok.value),
            'linea': tok.lineno,
            'pos': tok.lexpos,
        })
    return tokens_list


def tokenize_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    return analizar(source)


_author_names = {
    'algoritmo1': 'AnnabellaSanchez',
    'algoritmo2': 'CristianIntriago',
    'algoritmo3': 'ValentinaFalconi',
}

def generate_log(filepath, nombre_dev=""):
    tokens_list = tokenize_file(filepath)
    now = datetime.now().strftime('%d-%m-%Y-%Hh%M')
    base = os.path.splitext(os.path.basename(filepath))[0]
    author = nombre_dev or _author_names.get(base, 'Desconocido')
    os.makedirs('logs', exist_ok=True)
    log_name = f'logs/lexico-{author}-{now}.txt'

    with open(log_name, 'w', encoding='utf-8') as f:
        f.write(f'Archivo fuente : {filepath}\n')
        f.write(f'Desarrollador  : {author}\n')
        f.write(f'Fecha/Hora     : {now}\n')
        f.write(f'Total tokens   : {len(tokens_list)}\n')
        f.write(f'Total errores  : {len(lexer.errores)}\n')
        f.write('=' * 60 + '\n')
        f.write(f'{"#":<6}{"TIPO":<20}{"VALOR":<30}{"LINEA"}\n')
        f.write('=' * 60 + '\n')
        for i, tok in enumerate(tokens_list, 1):
            f.write(f'{i:<6}{tok["tipo"]:<20}{tok["valor"]:<30}{tok["linea"]}\n')
        if lexer.errores:
            f.write('\n' + '=' * 60 + '\n')
            f.write('ERRORES LÉXICOS\n')
            f.write('=' * 60 + '\n')
            for err in lexer.errores:
                f.write(f'  Línea {err["linea"]}: {err["mensaje"]}\n')

    print(f'Log generado: {log_name}')
    return log_name


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python lexer.py <archivo.rb>')
        sys.exit(1)
    generate_log(sys.argv[1])
