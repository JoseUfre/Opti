# Funcion que me dice si el agua de una aspersor de radio r sale de la
# grilla al colocarlo en el punto (x,y)

def no_sale(f, c, r, filas, columnas):
    if f + r <= filas - 1 and f - r >= 0:
        if c + r <= columnas - 1 and c - r >= 0:
            return True
    else:
        return False

def riega(x, y, f, c, r):
    if x + r >= f and y + r >= c and x - r <= f and y - r <= c and (x, y) != (f, c):
        return True
    else:
        return False
    
def vecino(x, y, f, c, r):
    pass

