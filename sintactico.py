# sintactico.py - Analizador sintactico (parser recursivo descendente) para compilaGOAT


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0

    def _token_actual(self):
        return self.tokens[self.posicion]

    def _consumir(self, tipo_esperado):
        token = self._token_actual()
        if token["tipo"] != tipo_esperado:
            raise SyntaxError(
                f"Se esperaba '{tipo_esperado}' pero se encontro '{token['tipo']}' "
                f"(valor: '{token['valor']}') en linea {token['linea']}, columna {token['columna']}"
            )
        self.posicion += 1
        return token

    def _verificar(self, tipo):
        return self._token_actual()["tipo"] == tipo

    def _verificar_tipo_dato(self):
        return self._token_actual()["tipo"] in ("PALABRA_INT", "PALABRA_FLOAT", "PALABRA_STRING")

    # --- Programa ---

    def _parsear_programa(self):
        funciones = []
        main = None

        while not self._verificar("FIN"):
            if self._verificar_tipo_dato() or self._verificar("IDENTIFICADOR"):
                # Mirar adelante para distinguir funcion de declaracion global
                if self._es_funcion():
                    funcion = self._parsear_funcion()
                    if funcion["nombre"] == "main":
                        main = funcion
                    else:
                        funciones.append(funcion)
                else:
                    break
            else:
                break

        if main is None:
            # Si no hay main explicito, crear uno vacio
            main = {"tipo": "funcion", "nombre": "main", "tipo_retorno": "int",
                    "parametros": [], "cuerpo": []}

        return {"tipo": "programa", "nombre": "compilaGOAT", "funciones": funciones, "main": main}

    def _es_funcion(self):
        """Mira adelante para determinar si es una declaracion de funcion."""
        pos_guardada = self.posicion
        # tipo_retorno o nombre_funcion
        self.posicion += 1
        # Despues del tipo, debe haber un identificador (nombre de funcion)
        if self._verificar("IDENTIFICADOR"):
            self.posicion += 1
            # Despues del nombre, debe haber parentesis
            resultado = self._verificar("PARENTESIS_IZQ")
        else:
            resultado = False
        self.posicion = pos_guardada
        return resultado

    def _parsear_funcion(self):
        tipo_retorno = self._consumir(self._token_actual()["tipo"])["valor"]
        nombre = self._consumir("IDENTIFICADOR")["valor"]
        self._consumir("PARENTESIS_IZQ")

        parametros = []
        if not self._verificar("PARENTESIS_DER"):
            parametros.append(self._parsear_parametro())
            while self._verificar("COMA"):
                self._consumir("COMA")
                parametros.append(self._parsear_parametro())

        self._consumir("PARENTESIS_DER")
        self._consumir("LLAVE_IZQ")

        cuerpo = self._parsear_bloque()

        self._consumir("LLAVE_DER")

        return {
            "tipo": "funcion",
            "nombre": nombre,
            "tipo_retorno": tipo_retorno,
            "parametros": parametros,
            "cuerpo": cuerpo,
        }

    def _parsear_parametro(self):
        tipo_dato = self._consumir(self._token_actual()["tipo"])["valor"]
        nombre = self._consumir("IDENTIFICADOR")["valor"]
        return {"nombre": nombre, "tipo_dato": tipo_dato}

    # --- Bloque e instrucciones ---

    def _parsear_bloque(self):
        instrucciones = []
        while not self._verificar("LLAVE_DER") and not self._verificar("FIN"):
            instrucciones.append(self._parsear_instruccion())
        return instrucciones

    def _parsear_instruccion(self):
        token = self._token_actual()

        if token["tipo"] == "PALABRA_PRINT":
            return self._parsear_print()
        elif token["tipo"] == "PALABRA_PRINTLN":
            return self._parsear_println()
        elif token["tipo"] == "PALABRA_IF":
            return self._parsear_si()
        elif token["tipo"] == "PALABRA_WHILE":
            return self._parsear_mientras()
        elif token["tipo"] == "PALABRA_FOR":
            return self._parsear_para()
        elif token["tipo"] == "PALABRA_RETURN":
            return self._parsear_return()
        elif self._verificar_tipo_dato():
            return self._parsear_declaracion()
        elif token["tipo"] == "IDENTIFICADOR":
            return self._parsear_asignacion_o_llamada()
        else:
            raise SyntaxError(
                f"Instruccion inesperada '{token['valor']}' en linea {token['linea']}, columna {token['columna']}"
            )

    def _parsear_print(self):
        self._consumir("PALABRA_PRINT")
        self._consumir("PARENTESIS_IZQ")
        expresion = self._parsear_expresion()
        self._consumir("PARENTESIS_DER")
        self._consumir("PUNTO_Y_COMA")
        return {"tipo": "print", "expresion": expresion}

    def _parsear_println(self):
        self._consumir("PALABRA_PRINTLN")
        self._consumir("PARENTESIS_IZQ")
        expresion = self._parsear_expresion()
        self._consumir("PARENTESIS_DER")
        self._consumir("PUNTO_Y_COMA")
        return {"tipo": "println", "expresion": expresion}

    def _parsear_si(self):
        self._consumir("PALABRA_IF")
        self._consumir("PARENTESIS_IZQ")
        condicion = self._parsear_expresion()
        self._consumir("PARENTESIS_DER")
        self._consumir("LLAVE_IZQ")
        cuerpo_verdadero = self._parsear_bloque()
        self._consumir("LLAVE_DER")

        cuerpo_falso = None
        if self._verificar("PALABRA_ELSE"):
            self._consumir("PALABRA_ELSE")
            self._consumir("LLAVE_IZQ")
            cuerpo_falso = self._parsear_bloque()
            self._consumir("LLAVE_DER")

        return {"tipo": "si", "condicion": condicion,
                "cuerpo_verdadero": cuerpo_verdadero, "cuerpo_falso": cuerpo_falso}

    def _parsear_mientras(self):
        self._consumir("PALABRA_WHILE")
        self._consumir("PARENTESIS_IZQ")
        condicion = self._parsear_expresion()
        self._consumir("PARENTESIS_DER")
        self._consumir("LLAVE_IZQ")
        cuerpo = self._parsear_bloque()
        self._consumir("LLAVE_DER")
        return {"tipo": "mientras", "condicion": condicion, "cuerpo": cuerpo}

    def _parsear_para(self):
        self._consumir("PALABRA_FOR")
        self._consumir("PARENTESIS_IZQ")
        inicializacion = self._parsear_declaracion_o_asignacion_para()
        condicion = self._parsear_expresion()
        self._consumir("PUNTO_Y_COMA")
        incremento = self._parsear_asignacion_sin_punto_y_coma()
        self._consumir("PARENTESIS_DER")
        self._consumir("LLAVE_IZQ")
        cuerpo = self._parsear_bloque()
        self._consumir("LLAVE_DER")
        return {"tipo": "para", "inicializacion": inicializacion,
                "condicion": condicion, "incremento": incremento, "cuerpo": cuerpo}

    def _parsear_declaracion_o_asignacion_para(self):
        """Parsea init del for: puede ser declaracion o asignacion, termina en ;"""
        if self._verificar_tipo_dato():
            return self._parsear_declaracion()
        else:
            nombre = self._consumir("IDENTIFICADOR")["valor"]
            self._consumir("ASIGNACION")
            expresion = self._parsear_expresion()
            self._consumir("PUNTO_Y_COMA")
            return {"tipo": "asignacion", "nombre": nombre, "expresion": expresion}

    def _parsear_asignacion_sin_punto_y_coma(self):
        """Parsea asignacion sin consumir punto y coma (para incremento del for)."""
        nombre = self._consumir("IDENTIFICADOR")["valor"]
        self._consumir("ASIGNACION")
        expresion = self._parsear_expresion()
        return {"tipo": "asignacion", "nombre": nombre, "expresion": expresion}

    def _parsear_return(self):
        self._consumir("PALABRA_RETURN")
        expresion = None
        if not self._verificar("PUNTO_Y_COMA"):
            expresion = self._parsear_expresion()
        self._consumir("PUNTO_Y_COMA")
        return {"tipo": "return", "expresion": expresion}

    def _parsear_declaracion(self):
        tipo_dato = self._consumir(self._token_actual()["tipo"])["valor"]
        nombre = self._consumir("IDENTIFICADOR")["valor"]
        expresion = None
        if self._verificar("ASIGNACION"):
            self._consumir("ASIGNACION")
            expresion = self._parsear_expresion()
        self._consumir("PUNTO_Y_COMA")
        return {"tipo": "declaracion", "tipo_dato": tipo_dato, "nombre": nombre, "expresion": expresion}

    def _parsear_asignacion_o_llamada(self):
        nombre = self._consumir("IDENTIFICADOR")["valor"]

        if self._verificar("PARENTESIS_IZQ"):
            # Llamada a funcion como instruccion
            self._consumir("PARENTESIS_IZQ")
            argumentos = self._parsear_argumentos()
            self._consumir("PARENTESIS_DER")
            self._consumir("PUNTO_Y_COMA")
            return {"tipo": "llamada", "nombre": nombre, "argumentos": argumentos}

        # Asignacion
        self._consumir("ASIGNACION")
        expresion = self._parsear_expresion()
        self._consumir("PUNTO_Y_COMA")
        return {"tipo": "asignacion", "nombre": nombre, "expresion": expresion}

    def _parsear_argumentos(self):
        argumentos = []
        if not self._verificar("PARENTESIS_DER"):
            argumentos.append(self._parsear_expresion())
            while self._verificar("COMA"):
                self._consumir("COMA")
                argumentos.append(self._parsear_expresion())
        return argumentos

    # --- Expresiones con precedencia ---

    def _parsear_expresion(self):
        return self._parsear_o_logico()

    def _parsear_o_logico(self):
        izquierdo = self._parsear_y_logico()
        while self._verificar("O_LOGICO"):
            operador = self._consumir("O_LOGICO")["valor"]
            derecho = self._parsear_y_logico()
            izquierdo = {"tipo": "operacion_binaria", "operador": operador,
                         "izquierdo": izquierdo, "derecho": derecho}
        return izquierdo

    def _parsear_y_logico(self):
        izquierdo = self._parsear_igualdad()
        while self._verificar("Y_LOGICO"):
            operador = self._consumir("Y_LOGICO")["valor"]
            derecho = self._parsear_igualdad()
            izquierdo = {"tipo": "operacion_binaria", "operador": operador,
                         "izquierdo": izquierdo, "derecho": derecho}
        return izquierdo

    def _parsear_igualdad(self):
        izquierdo = self._parsear_comparacion()
        while self._verificar("IGUAL_IGUAL") or self._verificar("DIFERENTE"):
            operador = self._consumir(self._token_actual()["tipo"])["valor"]
            derecho = self._parsear_comparacion()
            izquierdo = {"tipo": "operacion_binaria", "operador": operador,
                         "izquierdo": izquierdo, "derecho": derecho}
        return izquierdo

    def _parsear_comparacion(self):
        izquierdo = self._parsear_suma()
        while self._token_actual()["tipo"] in ("MENOR", "MENOR_IGUAL", "MAYOR", "MAYOR_IGUAL"):
            operador = self._consumir(self._token_actual()["tipo"])["valor"]
            derecho = self._parsear_suma()
            izquierdo = {"tipo": "operacion_binaria", "operador": operador,
                         "izquierdo": izquierdo, "derecho": derecho}
        return izquierdo

    def _parsear_suma(self):
        izquierdo = self._parsear_multiplicacion()
        while self._verificar("MAS") or self._verificar("MENOS"):
            operador = self._consumir(self._token_actual()["tipo"])["valor"]
            derecho = self._parsear_multiplicacion()
            izquierdo = {"tipo": "operacion_binaria", "operador": operador,
                         "izquierdo": izquierdo, "derecho": derecho}
        return izquierdo

    def _parsear_multiplicacion(self):
        izquierdo = self._parsear_unario()
        while self._token_actual()["tipo"] in ("MULTIPLICACION", "DIVISION", "MODULO"):
            operador = self._consumir(self._token_actual()["tipo"])["valor"]
            derecho = self._parsear_unario()
            izquierdo = {"tipo": "operacion_binaria", "operador": operador,
                         "izquierdo": izquierdo, "derecho": derecho}
        return izquierdo

    def _parsear_unario(self):
        if self._verificar("NEGACION"):
            operador = self._consumir("NEGACION")["valor"]
            operando = self._parsear_unario()
            return {"tipo": "operacion_unaria", "operador": operador, "operando": operando}
        if self._verificar("MENOS"):
            operador = self._consumir("MENOS")["valor"]
            operando = self._parsear_unario()
            return {"tipo": "operacion_unaria", "operador": operador, "operando": operando}
        return self._parsear_primario()

    def _parsear_primario(self):
        token = self._token_actual()

        if token["tipo"] == "NUMERO_ENTERO":
            self._consumir("NUMERO_ENTERO")
            return {"tipo": "literal_entero", "valor": token["valor"]}

        if token["tipo"] == "NUMERO_FLOTANTE":
            self._consumir("NUMERO_FLOTANTE")
            return {"tipo": "literal_flotante", "valor": token["valor"]}

        if token["tipo"] == "CADENA":
            self._consumir("CADENA")
            return {"tipo": "literal_cadena", "valor": token["valor"]}

        if token["tipo"] == "IDENTIFICADOR":
            self._consumir("IDENTIFICADOR")
            nombre = token["valor"]
            # Verificar si es llamada a funcion
            if self._verificar("PARENTESIS_IZQ"):
                self._consumir("PARENTESIS_IZQ")
                argumentos = self._parsear_argumentos()
                self._consumir("PARENTESIS_DER")
                return {"tipo": "llamada_expr", "nombre": nombre, "argumentos": argumentos}
            return {"tipo": "identificador", "nombre": nombre}

        if token["tipo"] == "PARENTESIS_IZQ":
            self._consumir("PARENTESIS_IZQ")
            expresion = self._parsear_expresion()
            self._consumir("PARENTESIS_DER")
            return expresion

        raise SyntaxError(
            f"Expresion inesperada '{token['valor']}' en linea {token['linea']}, columna {token['columna']}"
        )


def analizar(tokens):
    """Analiza los tokens y retorna el AST como diccionario."""
    parser = Parser(tokens)
    return parser._parsear_programa()
