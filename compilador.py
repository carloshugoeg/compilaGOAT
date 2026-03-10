# compilador.py - Orquesta nasm + ld para compilar el .asm generado

import subprocess
import sys
import os
import platform


def compilar(codigo_asm, nombre_salida="programa"):
    """Escribe el .asm y lo compila con nasm + ld.

    Retorna True si la compilacion fue exitosa, False en caso contrario.
    """
    archivo_asm = f"{nombre_salida}.asm"
    archivo_obj = f"{nombre_salida}.o"

    # Escribir archivo .asm
    with open(archivo_asm, "w") as f:
        f.write(codigo_asm)
    print(f"  Archivo ASM escrito: {archivo_asm}")

    # Detectar plataforma
    if platform.system() == "Darwin":
        print("  ADVERTENCIA: El codigo NASM generado es para Linux x86 32-bit.")
        print("  Para compilar, usa una maquina virtual Linux o WSL.")
        print("  Intentando ensamblar de todas formas (puede fallar)...")

    # Paso 1: nasm
    print(f"  Ensamblando: nasm -f elf32 {archivo_asm} -o {archivo_obj}")
    resultado_nasm = subprocess.run(
        ["nasm", "-f", "elf32", archivo_asm, "-o", archivo_obj],
        capture_output=True, text=True
    )
    if resultado_nasm.returncode != 0:
        print(f"  Error en nasm: {resultado_nasm.stderr.strip()}")
        return False

    # Paso 2: ld
    print(f"  Enlazando: ld -m elf_i386 -o {nombre_salida} {archivo_obj}")
    resultado_ld = subprocess.run(
        ["ld", "-m", "elf_i386", "-o", nombre_salida, archivo_obj],
        capture_output=True, text=True
    )
    if resultado_ld.returncode != 0:
        print(f"  Error en ld: {resultado_ld.stderr.strip()}")
        return False

    print(f"  Ejecutable generado: {nombre_salida}")

    # Limpiar archivos intermedios
    try:
        os.remove(archivo_obj)
    except OSError:
        pass

    return True
