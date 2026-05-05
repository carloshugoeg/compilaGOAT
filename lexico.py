
PALABRAS_RESERVADAS = {
    "int":     "PALABRA_INT",
    "float":   "PALABRA_FLOAT",
    "string":  "PALABRA_STRING",
    "if":      "PALABRA_IF",
    "else":    "PALABRA_ELSE",
    "while":   "PALABRA_WHILE",
    "for":     "PALABRA_FOR",
    "return":  "PALABRA_RETURN",
    "print":   "PALABRA_PRINT",
    "println": "PALABRA_PRINTLN",
    "printf":  "PALABRA_PRINTF",
}

OPERADORES_DOBLES = {
    "==": "IGUAL_IGUAL",
    "!=": "DIFERENTE",
    "<=": "MENOR_IGUAL",
    ">=": "MAYOR_IGUAL",
    "&&": "Y_LOGICO",
    "||": "O_LOGICO",
}

OPERADORES_SIMPLES = {
    "+": "MAS",
    "-": "MENOS",
    "*": "MULTIPLICACION",
    "/": "DIVISION",
    "%": "MODULO",
    "=": "ASIGNACION",
    "<": "MENOR",
    ">": "MAYOR",
    "!": "NEGACION",
}

DELIMITADORES = {
    "(": "PARENTESIS_IZQ",
    ")": "PARENTESIS_DER",
    "{": "LLAVE_IZQ",
    "}": "LLAVE_DER",
    ";": "PUNTO_Y_COMA",
    ",": "COMA",
}


def _crear_token(tipo, valor, linea, columna):
    return {"tipo": tipo, "valor": valor, "linea": linea, "columna": columna}


def analizar(codigo_fuente):
    """Analiza el codigo fuente y retorna una lista de tokens."""
    tokens = []
    posicion = 0
    linea = 1
    columna = 1
    longitud = len(codigo_fuente)

    while posicion < longitud:
        caracter = codigo_fuente[posicion]

        # Saltos de linea
        if caracter == "\n":
            linea += 1
            columna = 1
            posicion += 1
            continue

        # Espacios en blanco
        if caracter in " \t\r":
            posicion += 1
            columna += 1
            continue

        # Comentarios de linea //
        if caracter == "/" and posicion + 1 < longitud and codigo_fuente[posicion + 1] == "/":
            posicion += 2
            while posicion < longitud and codigo_fuente[posicion] != "\n":
                posicion += 1
            continue

        # Comentarios de bloque /* ... */
        if caracter == "/" and posicion + 1 < longitud and codigo_fuente[posicion + 1] == "*":
            posicion += 2
            columna += 2
            while posicion + 1 < longitud:
                if codigo_fuente[posicion] == "\n":
                    linea += 1
                    columna = 1
                elif codigo_fuente[posicion] == "*" and codigo_fuente[posicion + 1] == "/":
                    posicion += 2
                    columna += 2
                    break
                else:
                    columna += 1
                posicion += 1
            continue

        # Cadenas entre comillas dobles
        if caracter == '"':
            col_inicio = columna
            posicion += 1
            columna += 1
            valor_cadena = ""
            while posicion < longitud and codigo_fuente[posicion] != '"':
                if codigo_fuente[posicion] == "\\":
                    posicion += 1
                    columna += 1
                    if posicion < longitud:
                        escape = codigo_fuente[posicion]
                        if escape == "n":
                            valor_cadena += "\n"
                        elif escape == "t":
                            valor_cadena += "\t"
                        elif escape == "\\":
                            valor_cadena += "\\"
                        elif escape == '"':
                            valor_cadena += '"'
                        else:
                            valor_cadena += escape
                else:
                    valor_cadena += codigo_fuente[posicion]
                posicion += 1
                columna += 1
            posicion += 1  # cerrar comilla
            columna += 1
            tokens.append(_crear_token("CADENA", valor_cadena, linea, col_inicio))
            continue

        # Numeros (enteros y flotantes)
        if caracter.isdigit():
            col_inicio = columna
            numero = ""
            es_flotante = False
            while posicion < longitud and (codigo_fuente[posicion].isdigit() or codigo_fuente[posicion] == "."):
                if codigo_fuente[posicion] == ".":
                    es_flotante = True
                numero += codigo_fuente[posicion]
                posicion += 1
                columna += 1
            if es_flotante:
                tokens.append(_crear_token("NUMERO_FLOTANTE", float(numero), linea, col_inicio))
            else:
                tokens.append(_crear_token("NUMERO_ENTERO", int(numero), linea, col_inicio))
            continue

        # Identificadores y palabras reservadas
        if caracter.isalpha() or caracter == "_":
            col_inicio = columna
            identificador = ""
            while posicion < longitud and (codigo_fuente[posicion].isalnum() or codigo_fuente[posicion] == "_"):
                identificador += codigo_fuente[posicion]
                posicion += 1
                columna += 1
            if identificador in PALABRAS_RESERVADAS:
                tokens.append(_crear_token(PALABRAS_RESERVADAS[identificador], identificador, linea, col_inicio))
            else:
                tokens.append(_crear_token("IDENTIFICADOR", identificador, linea, col_inicio))
            continue

        # Operadores dobles
        if posicion + 1 < longitud:
            doble = codigo_fuente[posicion:posicion + 2]
            if doble in OPERADORES_DOBLES:
                tokens.append(_crear_token(OPERADORES_DOBLES[doble], doble, linea, columna))
                posicion += 2
                columna += 2
                continue

        # Operadores simples
        if caracter in OPERADORES_SIMPLES:
            tokens.append(_crear_token(OPERADORES_SIMPLES[caracter], caracter, linea, columna))
            posicion += 1
            columna += 1
            continue

        # Delimitadores
        if caracter in DELIMITADORES:
            tokens.append(_crear_token(DELIMITADORES[caracter], caracter, linea, columna))
            posicion += 1
            columna += 1
            continue

        # Caracter no reconocido
        raise SyntaxError(f"Caracter no reconocido '{caracter}' en linea {linea}, columna {columna}")

    tokens.append(_crear_token("FIN", None, linea, columna))
    return tokens
