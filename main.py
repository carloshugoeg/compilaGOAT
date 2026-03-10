# main.py - Punto de entrada del compilador compilaGOAT

import json
import lexico
import sintactico
import generador_js
import generador_asm
import compilador


# ==================== Programas de prueba ====================

PROGRAMAS = [
    {
        "nombre": "1. Hello World",
        "codigo": '''
int main() {
    println("Hola Mundo!");
}
'''
    },
    {
        "nombre": "2. Variables y aritmetica",
        "codigo": '''
int main() {
    int a = 10;
    int b = 20;
    int suma = a + b;
    int producto = a * b;
    println("Suma:");
    println(suma);
    println("Producto:");
    println(producto);
}
'''
    },
    {
        "nombre": "3. If/Else",
        "codigo": '''
int main() {
    int x = 15;
    if (x > 10) {
        println("x es mayor que 10");
    } else {
        println("x es menor o igual a 10");
    }
}
'''
    },
    {
        "nombre": "4. While",
        "codigo": '''
int main() {
    int i = 0;
    while (i < 5) {
        println(i);
        i = i + 1;
    }
}
'''
    },
    {
        "nombre": "5. For",
        "codigo": '''
int main() {
    for (int i = 0; i < 5; i = i + 1) {
        println(i);
    }
}
'''
    },
    {
        "nombre": "6. Funciones con parametros",
        "codigo": '''
int suma(int a, int b) {
    return a + b;
}

int main() {
    int resultado = suma(3, 7);
    println("Resultado:");
    println(resultado);
}
'''
    },
]


def separador(texto):
    print(f"\n{'='*60}")
    print(f"  {texto}")
    print(f"{'='*60}")


def ejecutar_programa(programa):
    nombre = programa["nombre"]
    codigo = programa["codigo"].strip()

    separador(nombre)
    print(f"\n--- Codigo fuente ---\n{codigo}")

    # Fase 1: Analisis lexico
    try:
        tokens = lexico.analizar(codigo)
    except SyntaxError as e:
        print(f"\nError lexico: {e}")
        return

    print(f"\n--- Tokens ({len(tokens)}) ---")
    for token in tokens:
        print(f"  {token}")

    # Fase 2: Analisis sintactico
    try:
        ast = sintactico.analizar(tokens)
    except SyntaxError as e:
        print(f"\nError sintactico: {e}")
        return

    print(f"\n--- AST (JSON) ---")
    print(json.dumps(ast, indent=2, ensure_ascii=False))

    # Fase 3: Generacion de JavaScript
    try:
        codigo_js = generador_js.generar(ast)
    except Exception as e:
        print(f"\nError generando JavaScript: {e}")
        return

    print(f"\n--- JavaScript generado ---")
    print(codigo_js)

    # Fase 4: Generacion de NASM
    try:
        codigo_asm = generador_asm.generar(ast)
    except Exception as e:
        print(f"\nError generando NASM: {e}")
        return

    print(f"\n--- NASM generado ---")
    print(codigo_asm)

    # Fase 5: Compilacion (intentar, puede fallar en macOS)
    print(f"\n--- Compilacion ---")
    nombre_salida = f"programa_{nombre.split('.')[0].strip()}"
    nombre_salida = nombre_salida.replace(" ", "_").lower()
    exito = compilador.compilar(codigo_asm, nombre_salida)
    if exito:
        print(f"  Compilacion exitosa!")
    else:
        print(f"  Compilacion no completada (ver advertencias arriba)")


def main():
    print("=" * 60)
    print("  compilaGOAT - Compilador")
    print("  Lenguaje tipo C -> JavaScript / NASM x86")
    print("=" * 60)

    for programa in PROGRAMAS:
        ejecutar_programa(programa)

    print(f"\n{'='*60}")
    print("  Fin de la ejecucion")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
