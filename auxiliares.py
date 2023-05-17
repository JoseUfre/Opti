# Funcion que me dice si el agua de una aspersor de radio r sale de la
# grilla al colocarlo en el punto (x,y)

def no_sale(f, c, r, filas, columnas):
    if f + r <= filas - 1 and f - r >= 0:
        if c + r <= columnas - 1 and c - r >= 0:
            return True
    else:
        return False
