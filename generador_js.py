def generar(ast):
    """Genera codigo JavaScript a partir del AST."""
    generador = GeneradorJS()
    return generador._generar_programa(ast)


class GeneradorJS:
    def __init__(self):
        self.nivel_indentacion = 0

    def _indentacion(self):
        return "  " * self.nivel_indentacion

    def _generar_programa(self, nodo):
        lineas = []

        # Generar funciones
        for funcion in nodo["funciones"]:
            lineas.append(self._generar_funcion(funcion))
            lineas.append("")

        # Generar main
        lineas.append(self._generar_funcion(nodo["main"]))
        lineas.append("")

        # Llamar a main
        lineas.append("main();")
        lineas.append("")

        return "\n".join(lineas)

    def _generar_funcion(self, nodo):
        parametros = ", ".join(p["nombre"] for p in nodo["parametros"])
        lineas = [f"function {nodo['nombre']}({parametros}) {{"]
        self.nivel_indentacion += 1
        for instruccion in nodo["cuerpo"]:
            lineas.append(self._generar_instruccion(instruccion))
        self.nivel_indentacion -= 1
        lineas.append("}")
        return "\n".join(lineas)

    def _generar_instruccion(self, nodo):
        tipo = nodo["tipo"]
        ind = self._indentacion()

        if tipo == "declaracion":
            if nodo["expresion"] is not None:
                return f"{ind}let {nodo['nombre']} = {self._generar_expresion(nodo['expresion'])};"
            else:
                return f"{ind}let {nodo['nombre']};"

        if tipo == "asignacion":
            return f"{ind}{nodo['nombre']} = {self._generar_expresion(nodo['expresion'])};"

        if tipo == "print":
            expr = self._generar_expresion(nodo["expresion"])
            return f"{ind}process.stdout.write(String({expr}));"

        if tipo == "println":
            expr = self._generar_expresion(nodo["expresion"])
            return f"{ind}console.log({expr});"

        if tipo == "printf":
            args = ", ".join(self._generar_expresion(a) for a in nodo["argumentos"])
            return f"{ind}process.stdout.write(require('util').format({args}));"

        if tipo == "return":
            if nodo["expresion"] is not None:
                return f"{ind}return {self._generar_expresion(nodo['expresion'])};"
            else:
                return f"{ind}return;"

        if tipo == "si":
            resultado = f"{ind}if ({self._generar_expresion(nodo['condicion'])}) {{\n"
            self.nivel_indentacion += 1
            for instr in nodo["cuerpo_verdadero"]:
                resultado += self._generar_instruccion(instr) + "\n"
            self.nivel_indentacion -= 1
            resultado += f"{ind}}}"
            if nodo["cuerpo_falso"] is not None:
                resultado += " else {\n"
                self.nivel_indentacion += 1
                for instr in nodo["cuerpo_falso"]:
                    resultado += self._generar_instruccion(instr) + "\n"
                self.nivel_indentacion -= 1
                resultado += f"{ind}}}"
            return resultado

        if tipo == "mientras":
            resultado = f"{ind}while ({self._generar_expresion(nodo['condicion'])}) {{\n"
            self.nivel_indentacion += 1
            for instr in nodo["cuerpo"]:
                resultado += self._generar_instruccion(instr) + "\n"
            self.nivel_indentacion -= 1
            resultado += f"{ind}}}"
            return resultado

        if tipo == "para":
            init = self._generar_para_init(nodo["inicializacion"])
            cond = self._generar_expresion(nodo["condicion"])
            inc = self._generar_para_incremento(nodo["incremento"])
            resultado = f"{ind}for ({init} {cond}; {inc}) {{\n"
            self.nivel_indentacion += 1
            for instr in nodo["cuerpo"]:
                resultado += self._generar_instruccion(instr) + "\n"
            self.nivel_indentacion -= 1
            resultado += f"{ind}}}"
            return resultado

        if tipo == "llamada":
            args = ", ".join(self._generar_expresion(a) for a in nodo["argumentos"])
            return f"{ind}{nodo['nombre']}({args});"

        return f"{ind}/* instruccion no soportada: {tipo} */"

    def _generar_para_init(self, nodo):
        if nodo["tipo"] == "declaracion":
            if nodo["expresion"] is not None:
                return f"let {nodo['nombre']} = {self._generar_expresion(nodo['expresion'])};"
            return f"let {nodo['nombre']};"
        # asignacion
        return f"{nodo['nombre']} = {self._generar_expresion(nodo['expresion'])};"

    def _generar_para_incremento(self, nodo):
        return f"{nodo['nombre']} = {self._generar_expresion(nodo['expresion'])}"

    def _generar_expresion(self, nodo):
        tipo = nodo["tipo"]

        if tipo == "literal_entero":
            return str(nodo["valor"])

        if tipo == "literal_flotante":
            return str(nodo["valor"])

        if tipo == "literal_cadena":
            # Escapar caracteres especiales para JavaScript
            valor = nodo["valor"]
            valor = valor.replace("\\", "\\\\")
            valor = valor.replace('"', '\\"')
            valor = valor.replace("\n", "\\n")
            valor = valor.replace("\t", "\\t")
            return f'"{valor}"'

        if tipo == "identificador":
            return nodo["nombre"]

        if tipo == "operacion_binaria":
            izq = self._generar_expresion(nodo["izquierdo"])
            der = self._generar_expresion(nodo["derecho"])
            return f"({izq} {nodo['operador']} {der})"

        if tipo == "operacion_unaria":
            operando = self._generar_expresion(nodo["operando"])
            return f"({nodo['operador']}{operando})"

        if tipo == "llamada_expr":
            args = ", ".join(self._generar_expresion(a) for a in nodo["argumentos"])
            return f"{nodo['nombre']}({args})"

        return f"/* expresion no soportada: {tipo} */"
