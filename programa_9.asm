section .data
  _newline: db 10
  _newline_len equ 1
section .bss
  _buffer_num: resb 12
  _cadena_0: db "Resultado de float + int:"
  _cadena_0_len equ $ - _cadena_0
  _cadena_1: db "Cast implicito float a int:"
  _cadena_1_len equ $ - _cadena_1

section .text
  global _start

_imprimir_entero:
  push ebp
  mov ebp, esp
  push eax
  push ebx
  push ecx
  push edx
  push esi

  ; Manejar numeros negativos
  mov esi, 0        ; flag negativo
  cmp eax, 0
  jge .positivo
  neg eax
  mov esi, 1
.positivo:
  mov ecx, _buffer_num
  add ecx, 11       ; final del buffer
  mov byte [ecx], 0 ; null terminator
  mov ebx, 10

.bucle_digitos:
  dec ecx
  xor edx, edx
  div ebx           ; eax / 10, cociente en eax, residuo en edx
  add dl, '0'
  mov [ecx], dl
  cmp eax, 0
  jne .bucle_digitos

  ; Agregar signo negativo si es necesario
  cmp esi, 0
  je .imprimir
  dec ecx
  mov byte [ecx], '-'

.imprimir:
  ; Calcular longitud
  mov edx, _buffer_num
  add edx, 11
  sub edx, ecx      ; edx = longitud
  ; sys_write(1, ecx, edx)
  mov eax, 4
  mov ebx, 1
  int 0x80

  pop esi
  pop edx
  pop ecx
  pop ebx
  pop eax
  pop ebp
  ret

_start:
  push ebp
  mov ebp, esp
  sub esp, 16
  mov eax, 1080033280  ; float 3.5
  mov [ebp-4], eax
  mov eax, 2
  mov [ebp-8], eax
  mov eax, [ebp-4]
  push eax
  mov eax, [ebp-8]
  cvtsi2ss xmm0, eax
  movd eax, xmm0
  mov ebx, eax
  pop eax
  movd xmm0, eax
  movd xmm1, ebx
  addss xmm0, xmm1
  movd eax, xmm0
  mov [ebp-12], eax
  ; print cadena
  mov eax, 4
  mov ebx, 1
  mov ecx, _cadena_0
  mov edx, _cadena_0_len
  int 0x80
  ; newline
  mov eax, 4
  mov ebx, 1
  mov ecx, _newline
  mov edx, _newline_len
  int 0x80
  mov eax, [ebp-12]
  call _imprimir_entero
  ; newline
  mov eax, 4
  mov ebx, 1
  mov ecx, _newline
  mov edx, _newline_len
  int 0x80
  mov eax, [ebp-12]
  movd xmm0, eax
  cvttss2si eax, xmm0
  mov [ebp-16], eax
  ; print cadena
  mov eax, 4
  mov ebx, 1
  mov ecx, _cadena_1
  mov edx, _cadena_1_len
  int 0x80
  ; newline
  mov eax, 4
  mov ebx, 1
  mov ecx, _newline
  mov edx, _newline_len
  int 0x80
  mov eax, [ebp-16]
  call _imprimir_entero
  ; newline
  mov eax, 4
  mov ebx, 1
  mov ecx, _newline
  mov edx, _newline_len
  int 0x80
  ; salir del programa
  mov eax, 1
  xor ebx, ebx
  int 0x80