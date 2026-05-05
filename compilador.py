

import subprocess
import sys
import os
import platform


def compilar(codigo_asm, nombre_salida="programa"):
    """Escribe el .asm en disco (como referencia).

    Retorna True siempre (el archivo .asm se genera correctamente).
    """
    archivo_asm = f"{nombre_salida}.asm"

    # Escribir archivo .asm
    with open(archivo_asm, "w") as f:
        f.write(codigo_asm)
    print(f"  Archivo ASM escrito: {archivo_asm}")
    print(f"  (El ASM es para Linux x86 32-bit, se genera como referencia)")

    return True


def ejecutar_js(codigo_js, nombre_salida="programa"):
    """Escribe el .js y lo ejecuta con Node.js.

    Retorna True si la ejecucion fue exitosa, False en caso contrario.
    """
    archivo_js = f"{nombre_salida}.js"

    # Escribir archivo .js
    with open(archivo_js, "w") as f:
        f.write(codigo_js)

    # Ejecutar con Node.js
    try:
        resultado = subprocess.run(
            ["node", archivo_js],
            capture_output=True, text=True, timeout=10
        )
        if resultado.stdout:
            print(resultado.stdout.rstrip())
        if resultado.stderr:
            print(f"  Error: {resultado.stderr.strip()}")
        if resultado.returncode != 0:
            return False
    except FileNotFoundError:
        print("  Error: Node.js no esta instalado.")
        print("  Instala Node.js desde https://nodejs.org/")
        return False
    except subprocess.TimeoutExpired:
        print("  Error: Tiempo de ejecucion excedido (posible bucle infinito)")
        return False
    finally:
        # Limpiar archivo .js temporal
        try:
            os.remove(archivo_js)
        except OSError:
            pass

    return True
