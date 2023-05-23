from auxiliares import no_sale, riega, vecino
from random import randint, seed

# Conjunto que tiene las listas de los puntos (h,l)
# de la grilla (grid) que no se salen de la misma
# al regar con un aspersor de radio r


def Chl(radios, filas, columnas):

    C_hl = {}
    for r in radios:
        C_hl[r] = (set(range(r, filas - r)), set(range(r, columnas - r)))
    return C_hl

# ------------------------------------------------------------------------------------------
# Lugares donde no puedo poner un regador excepto
# para distancias = r (para arriba, abajo, derecha, izquierda)

#   POR AHORA ESTE CONJUNTO ES EL MISMO QUE DONDE SI SE RIEGA (W_hlr)

# ----------------------------------------------------------------------------------------------
# Todos los lugares que son regados si se pone un regador en (x, y)
# Lugares donde no puedo poner un regador de radio r si pongo uno en x,y


def Whlr(radios, filas, columnas):
    
    C1_hl = {}

    for r in radios:
        C1_hl[r] = [(f, c) for f in range(filas) for c in range(columnas) if
                    no_sale(f, c, r, filas, columnas)]

    W_hlr = {}

    for r in radios:
        for (x, y) in C1_hl[r]:
            W_hlr[(x, y, r)] = [(f, c) for f in range(filas) for c in range(columnas) if
                                riega(x, y, f, c, r)]
    return W_hlr
# ---------------------------------------------------------------------------------------------
# Numero de lugares que son regados si pongo un regador de radio r en (x, y)


def Rhlr(radios, filas, columnas):

    C1_hl = {}

    for r in radios:
        C1_hl[r] = [(f, c) for f in range(filas) for c in range(columnas) if
                    no_sale(f, c, r, filas, columnas)]

    W_hlr = {}

    for r in radios:
        for (x, y) in C1_hl[r]:
            W_hlr[(x, y, r)] = [(f, c) for f in range(filas) for c in range(columnas) if
                                riega(x, y, f, c, r)]
    R_hlr = {}

    for r in radios:
        for x, y in C1_hl[r]:
            R_hlr[(x, y, r)] = len(W_hlr[(x, y, r)])

    return W_hlr

# ---------------------------------------------------------------------------------------------

# Todos los lugares donde si se coloca un aspersor en (x,y) se hacen vecinos


def Vhlr(radios, filas, columnas):

    C1_hl = {}
    for r in radios:
        C1_hl[r] = [(f, c) for f in range(filas) for c in range(columnas) if
                    no_sale(f, c, r, filas, columnas)]
    V_xyr = {}

    for r in radios:
        for x, y in C1_hl[r]:
            V_xyr[(x, y, r)] = vecino(x, y, r, filas, columnas)
    return V_xyr
