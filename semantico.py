class ErrorSemantico(Exception):
    pass

class TablaSimbolos:
    def __init__(self):
        self.scopes = [{}]
        self.funciones = {}
    
    def entrar_scope(self):
        self.scopes.append({})
        
    def salir_scope(self):
        self.scopes.pop()
        
    def declarar_variable(self, nombre, tipo_dato):
        if nombre in self.scopes[-1]:
            raise ErrorSemantico(f"Variable '{nombre}' ya declarada en este scope.")
        self.scopes[-1][nombre] = tipo_dato
        
    def obtener_variable(self, nombre):
        for scope in reversed(self.scopes):
            if nombre in scope:
                return scope[nombre]
        raise ErrorSemantico(f"Variable '{nombre}' no declarada.")
        
    def declarar_funcion(self, nombre, tipo_retorno, parametros):
        if nombre in self.funciones:
            raise ErrorSemantico(f"Funcion '{nombre}' ya declarada.")
        self.funciones[nombre] = {"tipo_retorno": tipo_retorno, "parametros": parametros}
        
    def obtener_funcion(self, nombre):
        if nombre not in self.funciones:
            raise ErrorSemantico(f"Funcion '{nombre}' no declarada.")
        return self.funciones[nombre]


def analizar(ast):
    tabla = TablaSimbolos()
    
    # Pre-declarar funciones
    todas_funciones = list(ast["funciones"])
    if ast["main"]:
        todas_funciones.append(ast["main"])
        
    for func in todas_funciones:
        parametros = [{"nombre": p["nombre"], "tipo_dato": p["tipo_dato"]} for p in func["parametros"]]
        tabla.declarar_funcion(func["nombre"], func["tipo_retorno"], parametros)
        
    # Analizar el cuerpo de cada funcion
    for func in todas_funciones:
        tabla.entrar_scope()
        for p in func["parametros"]:
            tabla.declarar_variable(p["nombre"], p["tipo_dato"])
            
        _analizar_bloque(func["cuerpo"], tabla, func["tipo_retorno"])
        tabla.salir_scope()
        
    return ast

def _analizar_bloque(instrucciones, tabla, tipo_retorno_func):
    for instr in instrucciones:
        _analizar_instruccion(instr, tabla, tipo_retorno_func)

def _analizar_instruccion(nodo, tabla, tipo_retorno_func):
    tipo = nodo["tipo"]
    
    if tipo == "declaracion":
        if nodo["expresion"] is not None:
            tipo_expr = _analizar_expresion(nodo["expresion"], tabla)
            if nodo["tipo_dato"] != tipo_expr:
                if (nodo["tipo_dato"] == "float" and tipo_expr == "int") or (nodo["tipo_dato"] == "int" and tipo_expr == "float"):
                    pass # cast implicito
                else:
                    raise ErrorSemantico(f"Incompatibilidad de tipos en declaracion de '{nodo['nombre']}': se esperaba {nodo['tipo_dato']}, se obtuvo {tipo_expr}")
        tabla.declarar_variable(nodo["nombre"], nodo["tipo_dato"])
        
    elif tipo == "asignacion":
        tipo_var = tabla.obtener_variable(nodo["nombre"])
        tipo_expr = _analizar_expresion(nodo["expresion"], tabla)
        if tipo_var != tipo_expr:
            if (tipo_var == "float" and tipo_expr == "int") or (tipo_var == "int" and tipo_expr == "float"):
                pass
            else:
                raise ErrorSemantico(f"Incompatibilidad de tipos en asignacion de '{nodo['nombre']}': se esperaba {tipo_var}, se obtuvo {tipo_expr}")
            
    elif tipo == "print" or tipo == "println":
        _analizar_expresion(nodo["expresion"], tabla)
        
    elif tipo == "printf":
        for arg in nodo["argumentos"]:
            _analizar_expresion(arg, tabla)
            
    elif tipo == "si":
        tipo_cond = _analizar_expresion(nodo["condicion"], tabla)
        tabla.entrar_scope()
        _analizar_bloque(nodo["cuerpo_verdadero"], tabla, tipo_retorno_func)
        tabla.salir_scope()
        if nodo["cuerpo_falso"]:
            tabla.entrar_scope()
            _analizar_bloque(nodo["cuerpo_falso"], tabla, tipo_retorno_func)
            tabla.salir_scope()
            
    elif tipo == "mientras":
        tipo_cond = _analizar_expresion(nodo["condicion"], tabla)
        tabla.entrar_scope()
        _analizar_bloque(nodo["cuerpo"], tabla, tipo_retorno_func)
        tabla.salir_scope()
        
    elif tipo == "para":
        tabla.entrar_scope()
        _analizar_instruccion(nodo["inicializacion"], tabla, tipo_retorno_func)
        _analizar_expresion(nodo["condicion"], tabla)
        _analizar_instruccion(nodo["incremento"], tabla, tipo_retorno_func)
        _analizar_bloque(nodo["cuerpo"], tabla, tipo_retorno_func)
        tabla.salir_scope()
        
    elif tipo == "return":
        if nodo["expresion"] is not None:
            tipo_expr = _analizar_expresion(nodo["expresion"], tabla)
            if tipo_retorno_func != tipo_expr:
                if (tipo_retorno_func == "float" and tipo_expr == "int") or (tipo_retorno_func == "int" and tipo_expr == "float"):
                    pass
                else:
                    raise ErrorSemantico(f"Tipo de retorno incorrecto: se esperaba {tipo_retorno_func}, se obtuvo {tipo_expr}")
        else:
            if tipo_retorno_func != "void":
                # In this language "void" might not be implemented, let's just accept
                pass
                
    elif tipo == "llamada":
        func = tabla.obtener_funcion(nodo["nombre"])
        if len(nodo["argumentos"]) != len(func["parametros"]):
            raise ErrorSemantico(f"Funcion '{nodo['nombre']}' esperaba {len(func['parametros'])} argumentos, se obtuvieron {len(nodo['argumentos'])}")
        for arg, param in zip(nodo["argumentos"], func["parametros"]):
            tipo_arg = _analizar_expresion(arg, tabla)
            if tipo_arg != param["tipo_dato"]:
                if (param["tipo_dato"] == "float" and tipo_arg == "int") or (param["tipo_dato"] == "int" and tipo_arg == "float"):
                    pass
                else:
                    raise ErrorSemantico(f"Argumento invalido para '{param['nombre']}' en '{nodo['nombre']}': se esperaba {param['tipo_dato']}, se obtuvo {tipo_arg}")

def _analizar_expresion(nodo, tabla):
    tipo_expr = nodo["tipo"]
    
    if tipo_expr == "literal_entero":
        nodo["tipo_dato"] = "int"
        return "int"
        
    elif tipo_expr == "literal_flotante":
        nodo["tipo_dato"] = "float"
        return "float"
        
    elif tipo_expr == "literal_cadena":
        nodo["tipo_dato"] = "string"
        return "string"
        
    elif tipo_expr == "identificador":
        tipo_var = tabla.obtener_variable(nodo["nombre"])
        nodo["tipo_dato"] = tipo_var
        return tipo_var
        
    elif tipo_expr == "operacion_binaria":
        tipo_izq = _analizar_expresion(nodo["izquierdo"], tabla)
        tipo_der = _analizar_expresion(nodo["derecho"], tabla)
        
        # Operadores booleanos y de comparacion retornan int (1 o 0)
        if nodo["operador"] in ("==", "!=", "<", "<=", ">", ">=", "&&", "||"):
            nodo["tipo_dato"] = "int"
            return "int"
            
        # Operadores aritmeticos
        if tipo_izq == "float" or tipo_der == "float":
            nodo["tipo_dato"] = "float"
            return "float"
        else:
            nodo["tipo_dato"] = "int"
            return "int"
            
    elif tipo_expr == "operacion_unaria":
        tipo_op = _analizar_expresion(nodo["operando"], tabla)
        if nodo["operador"] == "!":
            nodo["tipo_dato"] = "int"
            return "int"
        nodo["tipo_dato"] = tipo_op
        return tipo_op
        
    elif tipo_expr == "llamada_expr":
        func = tabla.obtener_funcion(nodo["nombre"])
        if len(nodo["argumentos"]) != len(func["parametros"]):
            raise ErrorSemantico(f"Funcion '{nodo['nombre']}' esperaba {len(func['parametros'])} argumentos, se obtuvieron {len(nodo['argumentos'])}")
        for arg, param in zip(nodo["argumentos"], func["parametros"]):
            tipo_arg = _analizar_expresion(arg, tabla)
            if tipo_arg != param["tipo_dato"]:
                if (param["tipo_dato"] == "float" and tipo_arg == "int") or (param["tipo_dato"] == "int" and tipo_arg == "float"):
                    pass
                else:
                    raise ErrorSemantico(f"Argumento invalido para '{param['nombre']}' en '{nodo['nombre']}': se esperaba {param['tipo_dato']}, se obtuvo {tipo_arg}")
        nodo["tipo_dato"] = func["tipo_retorno"]
        return func["tipo_retorno"]
        
    raise ErrorSemantico(f"Expresion desconocida: {tipo_expr}")
