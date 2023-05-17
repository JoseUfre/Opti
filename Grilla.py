from auxiliares import no_sale


filas = 9
columnas = 8
radios = (1, 3)

grid = [[c for c in range(columnas)] for f in range(filas)]

# Conjunto que tiene las listas de los puntos (h,l)
# de la grilla (grid) que no se salen de la misma
# al regar con un aspersor de radio r

C_hl = {}

for r in radios:
    C_hl[r] = [(f, c) for f in range(filas) for c in range(columnas) if
               no_sale(f, c, r, filas, columnas)]


