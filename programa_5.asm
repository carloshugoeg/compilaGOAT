section .data
  _newline: db 10
  _newline_len equ 1
section .bss
  _buffer_num: resb 12

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
  sub esp, 4
  mov eax, 0
  mov [ebp-4], eax
_para_1:
  mov eax, [ebp-4]
  push eax
  mov eax, 5
  mov ebx, eax
  pop eax
  cmp eax, ebx
  setl al
  movzx eax, al
  cmp eax, 0
  je _finpara_2
  mov eax, [ebp-4]
  call _imprimir_entero
  ; newline
  mov eax, 4
  mov ebx, 1
  mov ecx, _newline
  mov edx, _newline_len
  int 0x80
  mov eax, [ebp-4]
  push eax
  mov eax, 1
  mov ebx, eax
  pop eax
  add eax, ebx
  mov [ebp-4], eax
  jmp _para_1
_finpara_2:
  ; salir del programa
  mov eax, 1
  xor ebx, ebx
  int 0x80