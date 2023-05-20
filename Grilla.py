from auxiliares import no_sale, riega
from random import randint, seed

filas = 8
columnas = 8
radios = (1, 3, 5, 7)

grid = [[c for c in range(columnas)] for f in range(filas)]

# Conjunto que tiene las listas de los puntos (h,l)
# de la grilla (grid) que no se salen de la misma
# al regar con un aspersor de radio r

C_hl = {}

for r in radios:
    C_hl[r] = (set(range(r, filas - 1 - r)), set(range(r, columnas - 1 - r)))

C1_hl = {}

for r in radios:
    C1_hl[r] = [(f, c) for f in range(filas) for c in range(columnas) if
               no_sale(f, c, r, filas, columnas)]


# Lugares donde no puedo poner un regador excepto 
# para distancias = r (para arriba, abajo, derecha, izquierda)

# Todos los lugares que son regados si se pone un regador en (x, y)

W_hlr = {}

for r in radios:
    for (x, y) in C_hl[r]:
        W_hlr[(x, y, r)] = [(f, c) for f in range(filas) for c in range(columnas) if
                         riega(x, y, f, c, r)]

R_hlr = {}

for r in radios:
    for x, y in C1_hl[r]:
        R_hlr[(x, y, r)] = len(W_hlr[(x, y, r)])


   
#deberia incluir el radio en el diccionario? si

print(C_hl)
print()
for (x, y) in W_hlr:
    print((x, y), W_hlr[(x, y)])



# Todos los lugares donde si se coloca un aspersor en (x,y) se hacen vecinos
# Falta
# Son vecinos si comparten pasto a regar

V_xyr = {}

for r in radios:
    for x, y in C1_hl[r]:
