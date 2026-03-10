# generador_asm.py - Generador de codigo ensamblador NASM x86 32-bit Linux para compilaGOAT


def generar(ast):
    """Genera codigo NASM x86 32-bit a partir del AST."""
    generador = GeneradorASM()
    return generador._generar_programa(ast)


class GeneradorASM:
    def __init__(self):
        self.seccion_data = []
        self.seccion_text = []
        self.contador_cadenas = 0
        self.contador_etiquetas = 0
        self.variables = {}  # nombre -> offset desde ebp
        self.offset_stack = 0

    def _nueva_etiqueta(self, prefijo="L"):
        self.contador_etiquetas += 1
        return f"_{prefijo}_{self.contador_etiquetas}"

    def _registrar_cadena(self, valor):
        """Registra una cadena en .data y retorna su etiqueta."""
        etiqueta = f"_cadena_{self.contador_cadenas}"
        self.contador_cadenas += 1

        # Convertir caracteres especiales a bytes NASM
        partes = []
        i = 0
        texto_actual = ""
        while i < len(valor):
            c = valor[i]
            if c == "\n":
                if texto_actual:
                    partes.append(f'"{texto_actual}"')
                    texto_actual = ""
                partes.append("10")
            elif c == "\t":
                if texto_actual:
                    partes.append(f'"{texto_actual}"')
                    texto_actual = ""
                partes.append("9")
            else:
                texto_actual += c
            i += 1
        if texto_actual:
            partes.append(f'"{texto_actual}"')

        if not partes:
            partes = ['""']

        contenido = ", ".join(partes)
        self.seccion_data.append(f"  {etiqueta}: db {contenido}")
        self.seccion_data.append(f"  {etiqueta}_len equ $ - {etiqueta}")
        return etiqueta

    def _registrar_variable(self, nombre):
        """Registra variable local en el stack."""
        self.offset_stack += 4
        self.variables[nombre] = self.offset_stack
        return self.offset_stack

    def _obtener_variable(self, nombre):
        """Obtiene el offset de una variable."""
        if nombre not in self.variables:
            raise NameError(f"Variable no declarada: {nombre}")
        return self.variables[nombre]

    def _emit(self, linea):
        self.seccion_text.append(linea)

    def _generar_programa(self, ast):
        # Registrar newline en data
        self.seccion_data.append('  _newline: db 10')
        self.seccion_data.append('  _newline_len equ 1')
        # Buffer para imprimir enteros
        self.seccion_data.append('section .bss')
        self.seccion_data.append('  _buffer_num: resb 12')

        # Generar funciones auxiliares
        funciones_auxiliares = self._generar_imprimir_entero()

        # Generar funciones del usuario
        codigo_funciones = []
        for funcion in ast["funciones"]:
            codigo_funciones.append(self._generar_funcion(funcion))

        # Generar main
        codigo_main = self._generar_funcion_main(ast["main"])

        # Ensamblar todo
        resultado = []
        resultado.append("section .data")
        resultado.extend(self.seccion_data[:len(self.seccion_data)])  # data items before .bss
        resultado.append("")
        resultado.append("section .text")
        resultado.append("  global _start")
        resultado.append("")

        # Funcion auxiliar para imprimir enteros
        resultado.extend(funciones_auxiliares)
        resultado.append("")

        # Funciones del usuario
        for codigo in codigo_funciones:
            resultado.extend(codigo)
            resultado.append("")

        # Main como _start
        resultado.extend(codigo_main)

        return "\n".join(resultado)

    def _generar_imprimir_entero(self):
        """Genera la rutina _imprimir_entero: convierte eax a string y lo imprime."""
        lineas = []
        lineas.append("_imprimir_entero:")
        lineas.append("  push ebp")
        lineas.append("  mov ebp, esp")
        lineas.append("  push eax")
        lineas.append("  push ebx")
        lineas.append("  push ecx")
        lineas.append("  push edx")
        lineas.append("  push esi")
        lineas.append("")
        lineas.append("  ; Manejar numeros negativos")
        lineas.append("  mov esi, 0        ; flag negativo")
        lineas.append("  cmp eax, 0")
        lineas.append("  jge .positivo")
        lineas.append("  neg eax")
        lineas.append("  mov esi, 1")
        lineas.append(".positivo:")
        lineas.append("  mov ecx, _buffer_num")
        lineas.append("  add ecx, 11       ; final del buffer")
        lineas.append("  mov byte [ecx], 0 ; null terminator")
        lineas.append("  mov ebx, 10")
        lineas.append("")
        lineas.append(".bucle_digitos:")
        lineas.append("  dec ecx")
        lineas.append("  xor edx, edx")
        lineas.append("  div ebx           ; eax / 10, cociente en eax, residuo en edx")
        lineas.append("  add dl, '0'")
        lineas.append("  mov [ecx], dl")
        lineas.append("  cmp eax, 0")
        lineas.append("  jne .bucle_digitos")
        lineas.append("")
        lineas.append("  ; Agregar signo negativo si es necesario")
        lineas.append("  cmp esi, 0")
        lineas.append("  je .imprimir")
        lineas.append("  dec ecx")
        lineas.append("  mov byte [ecx], '-'")
        lineas.append("")
        lineas.append(".imprimir:")
        lineas.append("  ; Calcular longitud")
        lineas.append("  mov edx, _buffer_num")
        lineas.append("  add edx, 11")
        lineas.append("  sub edx, ecx      ; edx = longitud")
        lineas.append("  ; sys_write(1, ecx, edx)")
        lineas.append("  mov eax, 4")
        lineas.append("  mov ebx, 1")
        lineas.append("  int 0x80")
        lineas.append("")
        lineas.append("  pop esi")
        lineas.append("  pop edx")
        lineas.append("  pop ecx")
        lineas.append("  pop ebx")
        lineas.append("  pop eax")
        lineas.append("  pop ebp")
        lineas.append("  ret")
        return lineas

    def _generar_funcion(self, nodo):
        """Genera codigo para una funcion del usuario."""
        self.variables = {}
        self.offset_stack = 0
        lineas = []

        lineas.append(f"_{nodo['nombre']}:")
        lineas.append("  push ebp")
        lineas.append("  mov ebp, esp")

        # Registrar parametros (vienen en el stack encima de ebp)
        # [ebp+8] = primer param, [ebp+12] = segundo, etc.
        for i, param in enumerate(nodo["parametros"]):
            offset_param = 8 + (i * 4)
            self.variables[param["nombre"]] = -offset_param  # negativo indica parametro

        # Reservar espacio para variables locales (se calcula despues)
        indice_sub_esp = len(lineas)
        lineas.append("  sub esp, 0  ; placeholder")

        # Generar cuerpo
        self.seccion_text = []
        for instruccion in nodo["cuerpo"]:
            self._generar_instruccion(instruccion)
        lineas.extend(self.seccion_text)

        # Actualizar espacio reservado
        espacio = self.offset_stack
        if espacio > 0:
            lineas[indice_sub_esp] = f"  sub esp, {espacio}"
        else:
            lineas[indice_sub_esp] = "  ; sin variables locales"

        # Epilogo
        lineas.append("  mov esp, ebp")
        lineas.append("  pop ebp")
        lineas.append("  ret")
        return lineas

    def _generar_funcion_main(self, nodo):
        """Genera _start a partir del main."""
        self.variables = {}
        self.offset_stack = 0
        lineas = []

        lineas.append("_start:")
        lineas.append("  push ebp")
        lineas.append("  mov ebp, esp")

        indice_sub_esp = len(lineas)
        lineas.append("  sub esp, 0  ; placeholder")

        self.seccion_text = []
        for instruccion in nodo["cuerpo"]:
            self._generar_instruccion(instruccion)
        lineas.extend(self.seccion_text)

        espacio = self.offset_stack
        if espacio > 0:
            lineas[indice_sub_esp] = f"  sub esp, {espacio}"
        else:
            lineas[indice_sub_esp] = "  ; sin variables locales"

        # sys_exit(0)
        lineas.append("  ; salir del programa")
        lineas.append("  mov eax, 1")
        lineas.append("  xor ebx, ebx")
        lineas.append("  int 0x80")
        return lineas

    def _generar_instruccion(self, nodo):
        tipo = nodo["tipo"]

        if tipo == "declaracion":
            self._generar_declaracion(nodo)
        elif tipo == "asignacion":
            self._generar_asignacion(nodo)
        elif tipo == "print":
            self._generar_print(nodo, con_newline=False)
        elif tipo == "println":
            self._generar_print(nodo, con_newline=True)
        elif tipo == "si":
            self._generar_si(nodo)
        elif tipo == "mientras":
            self._generar_mientras(nodo)
        elif tipo == "para":
            self._generar_para(nodo)
        elif tipo == "return":
            self._generar_return(nodo)
        elif tipo == "llamada":
            self._generar_llamada_instruccion(nodo)

    def _generar_declaracion(self, nodo):
        offset = self._registrar_variable(nodo["nombre"])
        if nodo["expresion"] is not None:
            self._generar_expresion(nodo["expresion"])
            self._emit(f"  mov [ebp-{offset}], eax")
        else:
            self._emit(f"  mov dword [ebp-{offset}], 0")

    def _generar_asignacion(self, nodo):
        self._generar_expresion(nodo["expresion"])
        offset = self._obtener_variable(nodo["nombre"])
        if offset < 0:
            # Es un parametro
            self._emit(f"  mov [ebp+{-offset}], eax")
        else:
            self._emit(f"  mov [ebp-{offset}], eax")

    def _generar_print(self, nodo, con_newline):
        expresion = nodo["expresion"]

        if expresion["tipo"] == "literal_cadena":
            etiqueta = self._registrar_cadena(expresion["valor"])
            self._emit(f"  ; print cadena")
            self._emit(f"  mov eax, 4")
            self._emit(f"  mov ebx, 1")
            self._emit(f"  mov ecx, {etiqueta}")
            self._emit(f"  mov edx, {etiqueta}_len")
            self._emit(f"  int 0x80")
        else:
            # Evaluar expresion numerica
            self._generar_expresion(expresion)
            self._emit(f"  call _imprimir_entero")

        if con_newline:
            self._emit(f"  ; newline")
            self._emit(f"  mov eax, 4")
            self._emit(f"  mov ebx, 1")
            self._emit(f"  mov ecx, _newline")
            self._emit(f"  mov edx, _newline_len")
            self._emit(f"  int 0x80")

    def _generar_si(self, nodo):
        etiqueta_sino = self._nueva_etiqueta("sino")
        etiqueta_finsi = self._nueva_etiqueta("finsi")

        self._generar_expresion(nodo["condicion"])
        self._emit(f"  cmp eax, 0")
        self._emit(f"  je {etiqueta_sino}")

        # Cuerpo verdadero
        for instr in nodo["cuerpo_verdadero"]:
            self._generar_instruccion(instr)
        self._emit(f"  jmp {etiqueta_finsi}")

        # Cuerpo falso
        self._emit(f"{etiqueta_sino}:")
        if nodo["cuerpo_falso"] is not None:
            for instr in nodo["cuerpo_falso"]:
                self._generar_instruccion(instr)

        self._emit(f"{etiqueta_finsi}:")

    def _generar_mientras(self, nodo):
        etiqueta_inicio = self._nueva_etiqueta("mientras")
        etiqueta_fin = self._nueva_etiqueta("finmientras")

        self._emit(f"{etiqueta_inicio}:")
        self._generar_expresion(nodo["condicion"])
        self._emit(f"  cmp eax, 0")
        self._emit(f"  je {etiqueta_fin}")

        for instr in nodo["cuerpo"]:
            self._generar_instruccion(instr)

        self._emit(f"  jmp {etiqueta_inicio}")
        self._emit(f"{etiqueta_fin}:")

    def _generar_para(self, nodo):
        etiqueta_inicio = self._nueva_etiqueta("para")
        etiqueta_fin = self._nueva_etiqueta("finpara")

        # Inicializacion
        self._generar_instruccion(nodo["inicializacion"])

        self._emit(f"{etiqueta_inicio}:")
        self._generar_expresion(nodo["condicion"])
        self._emit(f"  cmp eax, 0")
        self._emit(f"  je {etiqueta_fin}")

        # Cuerpo
        for instr in nodo["cuerpo"]:
            self._generar_instruccion(instr)

        # Incremento
        self._generar_instruccion(nodo["incremento"])

        self._emit(f"  jmp {etiqueta_inicio}")
        self._emit(f"{etiqueta_fin}:")

    def _generar_return(self, nodo):
        if nodo["expresion"] is not None:
            self._generar_expresion(nodo["expresion"])
        self._emit("  mov esp, ebp")
        self._emit("  pop ebp")
        self._emit("  ret")

    def _generar_llamada_instruccion(self, nodo):
        # Push argumentos en orden inverso
        for arg in reversed(nodo["argumentos"]):
            self._generar_expresion(arg)
            self._emit("  push eax")
        self._emit(f"  call _{nodo['nombre']}")
        if nodo["argumentos"]:
            self._emit(f"  add esp, {len(nodo['argumentos']) * 4}")

    # --- Generacion de expresiones ---

    def _generar_expresion(self, nodo):
        tipo = nodo["tipo"]

        if tipo == "literal_entero":
            self._emit(f"  mov eax, {nodo['valor']}")

        elif tipo == "literal_flotante":
            # Aproximacion: truncar a entero para asm
            self._emit(f"  mov eax, {int(nodo['valor'])}")

        elif tipo == "literal_cadena":
            # Registrar cadena y poner su direccion en eax
            etiqueta = self._registrar_cadena(nodo["valor"])
            self._emit(f"  mov eax, {etiqueta}")

        elif tipo == "identificador":
            offset = self._obtener_variable(nodo["nombre"])
            if offset < 0:
                self._emit(f"  mov eax, [ebp+{-offset}]")
            else:
                self._emit(f"  mov eax, [ebp-{offset}]")

        elif tipo == "operacion_binaria":
            self._generar_operacion_binaria(nodo)

        elif tipo == "operacion_unaria":
            self._generar_expresion(nodo["operando"])
            if nodo["operador"] == "-":
                self._emit("  neg eax")
            elif nodo["operador"] == "!":
                self._emit("  cmp eax, 0")
                self._emit("  sete al")
                self._emit("  movzx eax, al")

        elif tipo == "llamada_expr":
            # Push argumentos en orden inverso
            for arg in reversed(nodo["argumentos"]):
                self._generar_expresion(arg)
                self._emit("  push eax")
            self._emit(f"  call _{nodo['nombre']}")
            if nodo["argumentos"]:
                self._emit(f"  add esp, {len(nodo['argumentos']) * 4}")

    def _generar_operacion_binaria(self, nodo):
        operador = nodo["operador"]

        # Evaluar izquierdo, guardar en stack, evaluar derecho
        self._generar_expresion(nodo["izquierdo"])
        self._emit("  push eax")
        self._generar_expresion(nodo["derecho"])
        self._emit("  mov ebx, eax")  # derecho en ebx
        self._emit("  pop eax")       # izquierdo en eax

        if operador == "+":
            self._emit("  add eax, ebx")
        elif operador == "-":
            self._emit("  sub eax, ebx")
        elif operador == "*":
            self._emit("  imul eax, ebx")
        elif operador == "/":
            self._emit("  cdq")
            self._emit("  idiv ebx")
        elif operador == "%":
            self._emit("  cdq")
            self._emit("  idiv ebx")
            self._emit("  mov eax, edx")  # residuo
        elif operador in ("==", "!=", "<", "<=", ">", ">="):
            self._emit("  cmp eax, ebx")
            instruccion_set = {
                "==": "sete",
                "!=": "setne",
                "<":  "setl",
                "<=": "setle",
                ">":  "setg",
                ">=": "setge",
            }
            self._emit(f"  {instruccion_set[operador]} al")
            self._emit("  movzx eax, al")
        elif operador == "&&":
            # a && b: ambos deben ser != 0
            self._emit("  cmp eax, 0")
            self._emit("  setne al")
            self._emit("  cmp ebx, 0")
            self._emit("  setne bl")
            self._emit("  and al, bl")
            self._emit("  movzx eax, al")
        elif operador == "||":
            # a || b: al menos uno != 0
            self._emit("  or eax, ebx")
            self._emit("  cmp eax, 0")
            self._emit("  setne al")
            self._emit("  movzx eax, al")
