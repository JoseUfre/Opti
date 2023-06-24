from gurobipy import GRB, Model, quicksum
from Grilla import Chl, Whlr, Vhlr, Rhlr
import numpy as np 


class Sector():
    def __init__(self) -> None:
        self.num_fil = None
        self.num_col = None
        self.id = None


class Casilla():
    def __init__(self) -> None:
        self.riego = 0


class SolverGurobi():

    def __init__(self) -> None:
        self.model = Model()
        self.n_sectores = 0
        self.fil = {}
        self.col = {}
        self.sectores = {}
        self.n_r = 0

        self.R = set()  # Conjunto con Radios Disponibles

        self.posible_places = {}  # Diccionario que de llave tiene el str "radio, sector" y de valor tiene una
                                  # tupla de valores (F,C) donde se puede colocar el regador de dicho radio

        self.not_posible_places = {}  # Diccionario que de llave tiene el "fila,columna,radio" y de valor tiene una
                                      # lista de valores donde no puede haber otro regador de la forma 

        self.vecinos_places = {}  # Diccionario que de llave tiene la fila, columna y el radio y de valor tiene
                                  # lista de valores donde si hay otro regador es vecino

        self.regados = {}  # Diccionario que tiene llave fila col radio y da todos lugares que riega ese aspersor

        self.vars = {}  # Diccionario que guarda las variables

        self.inversion = {}  # Diccionario que tiene de llave el sector y la inversion a este

        self.min_cover = None  # Parametro que indica el minimo de cobertura para cada area

        self.costo_aspersor = None  # Parametro que indica el costo del aspersor 

    # Funcion encargada de cargar los csv
    def get_data(self):
        print("Obteniendo sector")
        with open("Radios.csv", "rt", encoding="utf-8") as archivo:
            raw_list = archivo.readlines()
            w_list = []
            for e in raw_list:
                w_list.append(e.strip().split(","))
            w_list.pop(0)
            for linea in w_list:
                for valor in linea:
                    self.R.add(int(valor))

        with open("Sectores.csv", "rt", encoding="utf-8") as archivo:
            raw_list = archivo.readlines()
            w_list = []
            for e in raw_list:
                w_list.append(e.strip().split(","))
            w_list.pop(0)
            for linea in w_list:
                n = 0 
                for valor in linea:
                    self.n_sectores += 1
                    fila, columna = valor.split("x")
                    fila = int(fila)
                    columna = int(columna)
                    self.fil[n] = fila
                    self.col[n] = columna
                    n += 1

        with open("Inversiones.csv", "rt", encoding="utf-8") as archivo:
            raw_list = archivo.readlines()
            w_list = []
            for e in raw_list:
                w_list.append(e.strip().split(","))
            w_list.pop(0)
            for linea in w_list:
                n = 0 
                for valor in linea:
                    self.inversion[n] = int(valor)
                    n += 1

        with open("Costo.csv", "rt", encoding="utf-8") as archivo:
            raw_list = archivo.readlines()
            w_list = []
            for e in raw_list:
                w_list.append(e.strip().split(","))
            w_list.pop(0)
            for linea in w_list:
                for valor in linea:
                    self.costo_aspersor = int(valor)

        with open("Cobertura.csv", "rt", encoding="utf-8") as archivo:
            raw_list = archivo.readlines()
            w_list = []
            for e in raw_list:
                w_list.append(e.strip().split(","))
            w_list.pop(0)
            for linea in w_list:
                for valor in linea:
                    self.min_cover = float(valor)
        self.process_data()
        print("Termine Obteniendo sector")

    # Funcion encargada de tomar la informacion de los csv
    # Pasar la informacion a los parametros de la clase
    def process_data(self):
        print("Procesando data")
        for n_sector in range(self.n_sectores):
            z = Sector()
            z.id = n_sector
            z.num_fil = self.fil[n_sector]
            z.num_col = self.col[n_sector]
            self.sectores[z.id] = z
            self.posible_places[z.id] = Chl(self.R, z.num_fil, z.num_col)
            self.not_posible_places[z.id] = Whlr(self.R, z.num_fil, z.num_col)
            self.vecinos_places[z.id] = Vhlr(self.R, z.num_fil, z.num_col)
            self.regados[z.id] = Rhlr(self.R, z.num_fil, z.num_col)
        print("Termine Procesando data")

    # Funcion encargada de definir las variables del modelo.
    def set_vars(self):
        print("Setting vars")
        for id_sector in self.sectores.keys():  # Crear conjuntos de variables para cada sector
            sector: Sector = self.sectores[id_sector]
            F = range(sector.num_fil)  # Tomar el conjunto de filas del sector z
            C = range(sector.num_col)  # Tomar el conjunto de columnas del sector z

            # Primer conjunto de variables: Varaible "x" que indica si hay un aspersor
            # en la fila f en la columna c de radio r
            self.vars[f"x{sector.id}"] = self.model.addVars(F, C, self.R, vtype=GRB.BINARY, name=f"x{sector.id}_f,c,r")

            # Segundo conjunto de variables: Variable "r" que indica si el bloque de la fila f y columna c es regado
            self.vars[f"r{sector.id}"] = self.model.addVars(F, C, vtype=GRB.BINARY, name=f"r{sector.id}_f,c")

            # Tercer conjunto de variables: Variable v que indica si hay una vecindad entre el regador que esta en f,c 
            # y el que esta en l,h
            self.vars[f"v{sector.id}"] = self.model.addVars(F, C, F, C, vtype=GRB.BINARY, name=f"v{sector.id}_f,c,l,h")

            # Cuarto conjunto de variables: Variable e que indica el porcentaje de pasto no regado para el sector
            self.vars[f"e{sector.id}"] = self.model.addVar(vtype=GRB.CONTINUOUS, name = f"e{sector.id}")
        self.model.update()
        print("Termine vars")

    # Funcion que setea las variables relacionadas con la posicion de los aspersores
    def set_constrs_sprinklers(self):
        print("Setting sprinklers constrais")
        for id_sector in self.sectores.keys():  # Crear las restricciones para cada sector
            sector: Sector = self.sectores[id_sector]
            var = self.vars[f"x{sector.id}"]  # Rescatar el conjunto de variables para ese sector

            # Restriccion 1: Puede haber a lo mas un tipo de regador en cada coordenada del sector
            self.n_r += 1
            self.model.addConstrs((quicksum(var[f, c, r] for r in self.R) <= 1
                                   for f in range(sector.num_fil) 
                                   for c in range(sector.num_col)),
                                       name=f"R{self.n_r}")

            # Restriccion 2.1: Si hay un regador en la posicion f,c de radio r NO puede haber un regador,
            # de cualquier tipo dentro de su radio de alcance
            for radio in self.R:
                for fil in range(sector.num_fil):
                    for col in range(sector.num_col):
                        key = (fil, col, radio)
                        not_places: list = self.not_posible_places[sector.id].get(key)
                        if not_places is None:
                            continue
                        self.n_r += 1
                        self.model.addConstrs((1 - var[fil, col, radio] >= quicksum(var[f2, c2, a] for a in self.R)
                                               for f2 in range(sector.num_fil)
                                               for c2 in range(sector.num_col)
                                               if (f2, c2) in not_places), name=f"R{self.n_r}")

            # Restriccion 2.2: No puede haber un regador en una posicion si no esta permitida para su tipo
            # Es decir, que no riegue para afuera.
            for radio in self.R:
                self.n_r += 1
                key = radio
                F, C = self.posible_places[sector.id][key]
                self.model.addConstrs((var[f,c,radio] == 0 for f in range(sector.num_fil)
                                           for c in range(sector.num_col) 
                                           if (not f in F) or (not c in C)))
        print("Termine Setting sprinklers constrais")

    # Funcion encargada de las restricciones de las vecindades
    def set_vecinos_cts(self):
        print("Setting Vecinos constrais")
        for z in range(self.n_sectores):  # Para cada sector
            sector: Sector = self.sectores[z]
            var = self.vars[f"x{sector.id}"]  # Rescatar el conjunto de variables asociadas a las posiciones
            varvec = self.vars[f"v{sector.id}"]  # Rescatar el conjunto de variables asociadas a las vecindades

            # Necesitamos recorrer los radios, filas y columnas.
            for radio in self.R:
                for fil in range(sector.num_fil):
                    for col in range(sector.num_col):
                        # Evaluar cada combinacion de fila, columna, radio.
                        key = (fil, col, radio)
                        vecinos: list = self.vecinos_places[sector.id].get(key)   
                        if vecinos is None:
                            # Si la casilla no permite vecindades
                            # no se considera
                            continue

                        # Restriccion 3: Si hay un regador de radio "radio" en la fila "fil" y columna "col"
                        # y hay un regador de cualquier tipo en la  fila "l" columna "h" y la casilla (l,h)
                        # es un lugar que hace vecino con el aspersor (fil, col, radio) entonces, hay una vecindad
                        self.n_r += 1
                        self.model.addConstrs((var[fil,col,radio] + quicksum(var[l,h,a] for a in self.R)
                                              <= 1 + varvec[fil,col,l,h]
                                              for l in range(sector.num_fil)
                                              for h in range(sector.num_col)
                                              if (l,h) in vecinos) , name = f"R{self.n_r}")
                        # Restriccion 4: No puede haber vecindad de ("fil", "col") si no existe regador en "fil", "col"
                        self.n_r += 1               
                        self.model.addConstrs((quicksum(var[l,h,a] for a in self.R) >=  varvec[fil,col,l,h]
                                              for l in range(sector.num_fil)
                                              for h in range(sector.num_col)
                                              if (l,h) in vecinos) , name = f"R{self.n_r}")
        print("Termine Setting Vecinos constrais")

    # Funcion encargada de las restricciones asociadas a la covertura del pasto
    def set_constrains_obj(self):
        print("Setting Pasto cubierto constrais")
        for id_sector in self.sectores.keys():  # Para cada sector de pasto
            sector: Sector = self.sectores[id_sector]

            var = self.vars[f"x{sector.id}"] # Rescatar el conjunto de variables asociado a la posicion de los aspersores.

            varreg = self.vars[f"r{sector.id}"]  # Rescatar el conjunto de variables asociado a si una casilla es regada

            e = self.vars[f"e{id_sector}"]  # Rescatar la variable asociada a lo no regado

            dv = sector.num_col * sector.num_fil  # Rescatar el area del sector

            # Restriccion 5: La cantidad no regada no puede superar la 1 - "El porcentaje minimo de corvertura"
            self.n_r += 1
            self.model.addConstr(e <= 1-self.min_cover, name=f"R{self.n_r}")

            # Restriccion 6: La cantidad no regada no puede ser negativa 
            self.n_r += 1
            self.model.addConstr(e >= 0.0, name=f"R{self.n_r}")

            # Restriccion 7: El porcentaje regado + el porcentaje no regado debe ser igual al total
            self.n_r += 1
            self.model.addConstr((quicksum(varreg[l,h] 
                                  for l in range(sector.num_fil)
                                  for h in range(sector.num_col))/dv + e == 1), name = f"R{self.n_r}")

            # Buscar los lugares que pueden tener regador
            for r in self.R:
                for c in range(sector.num_col):
                    for f in range(sector.num_fil):
                        if self.posible_places[sector.id].get((f,c,r)) is None:
                            # Si ese lugar no puede tener regador se omite
                            continue

                        # Restriccion 8 :Si el lugar f,c tiene un regador de radio r
                        # y el bloque l,h esta a su alcance entonces,
                        # el lugar l,h esta regado
                        self.n_r += 1
                        self.model.addConstrs((var[f, c, r] <= varreg[l,h]
                                            for h in range(sector.num_col)
                                            for l in range(sector.num_fil) 
                                            if (l,h) in self.regados[sector.id][(f, c, r)]), 
                                            name = f"R{self.n_r}")

            # Restriccion 9: si el lugar (l,h) no esta alcance de ningun regador entonces no esta regado
            self.n_r += 1
            self.model.addConstrs((varreg[l,h] <= quicksum(var[f,c,r] 
                                            for r in self.R 
                                            for c in range(r, sector.num_col-r)
                                            for f in range(r, sector.num_fil-r)
                                            if (l,h) in self.regados[sector.id].get((f,c,r))) 
                                            for h in range(sector.num_col)
                                            for l in range(sector.num_fil)), name=f"R{self.n_r}")
        print("Termine Setting Pasto cubierto constrais")

    # Funcion encargada de manejar las restricciones de costo
    def set_constrains_cost(self):
        print("Setting Costo constrais")
        for id_sector in self.sectores.keys():  # Para cada sector 
            sector: Sector = self.sectores[id_sector] 

            inversion = self.inversion[id_sector]  # Rescatar la inversion maxima del sector

            var = self.vars[f"x{sector.id}"]  # Rescatar el conjunto de variables asociado a las posiciones de los aspersores

            costo = self.costo_aspersor  # Rescatar el costo de cada aspersor

            # Restriccion 10: El costo de la operacion en el sector no puede superar la inversion del sector
            self.n_r += 1
            self.model.addConstr((costo * quicksum(var[f,c,r] 
                                           for r in self.R
                                           for c in range(sector.num_col)
                                           for f in range(sector.num_fil)) <= inversion),name = f"R{self.n_r}") 
        print("Termine setting Costo constrais")

    # Funcion encargada de setear la funcion objetivo
    def set_objetivo(self):
        print("Empeze a setear objetivo")
        global_function = 0.0
        for id_sector in self.sectores.keys():  # Tomar en cuenta los aportes de cada sector
            sector: Sector = self.sectores[id_sector]

            varvec = self.vars[f"v{sector.id}"]  # Rescatar el conjunto de variables de vecindades del sector
            # Sumar todas las vecindades 
            funcion_sector = quicksum(varvec[f,c,l,h]
                            for c in range(self.sectores[id_sector].num_col)
                            for f in range(self.sectores[id_sector].num_fil)
                            for l in range(self.sectores[id_sector].num_fil)
                            for h in range(self.sectores[id_sector].num_col))
            global_function += funcion_sector

        # Maximizar la cantidad de vecindades
        self.model.setObjective(global_function, GRB.MAXIMIZE)
        print("Termine setear objetivo")

    def optimizar(self):
        print("Empeze a optimizar")
        self.model.optimize()

    # Funcion de analizis y encargada de generar el txt
    def analizar(self):
        if self.model.SolCount >= 1:
            print(f"Valor objetivo {self.model.ObjVal}")
            with open("sector.txt", "w") as file:
                for id_sector in self.sectores.keys():
                    file.write(f"Mostrando sector {id_sector}\n")
                    sector = []
                    fila = []
                    var = self.vars[f"x{id_sector}"]
                    varvec = self.vars[f"v{id_sector}"]
                    for i in range(self.sectores[id_sector].num_fil):
                        fila = []
                        for j in range(self.sectores[id_sector].num_col):
                            encontre = False
                            for l in range(self.sectores[id_sector].num_fil):
                                for h in range(self.sectores[id_sector].num_col):
                                    if varvec[i, j, l, h].x == 1:
                                        #print(f"Vecino para el aspersor ({i},{j}) en ({l},{h})")
                                        sum = 0
                                        for a in self.R:
                                            sum += var[i, j, a].x
                                        #print(f"{sum == 1}")
                            for a in self.R:
                                radio = 0
                                if var[i, j, a].x == 1:
                                    encontre = True
                                    radio = a
                                    break
                                if var[i, j, a].x == 0:
                                    continue
                            if encontre:
                                fila.append(str(radio))
                            else:
                                fila.append("0")
                        sector.append(fila)
                    for fila in sector:
                        fila.append("\n")
                        file.write("|".join(fila))
        else:
            print("error")

    # Funciones encargada de simular cuanto riega un regador a que bloque
    def get_reg(self, radio, x, y, a):
        b = np.array((x, y))
        distancia = np.max(np.absolute(a-b))-1
        if distancia <= radio*0.4:
            return 1
        else:
            if distancia/radio > 1.0:
                distancia = radio
            wt = -(1/(radio*0.6))*(distancia - 0.4*radio) + 1
            return wt

    # Calcular parametros estadisticos
    def get_UC(self):
        sectores = []
        for id, sector in self.sectores.items():
            var = self.vars[f"x{id}"]
            grid = np.zeros([sector.num_fil, sector.num_col])
            for fila in range(sector.num_fil):
                for col in range(sector.num_col):
                    for radio in self.R:
                        if var[fila, col, radio].x == 1:
                            a = np.array((fila, col))
                            for le, h in self.regados[id][(fila, col, radio)]:
                                grid[le, h] += self.get_reg(radio, le, h, a)
            # Analizar la zona central
            d2 = int(sector.num_fil/2)
            o2 = int(sector.num_col/2)
            mean = np.mean(grid[d2-3:d2+3, o2-3:o2+3])
            std = np.std(grid[d2-3:d2+3, o2-3:o2+3])
            du = 1 - 1.27*std/mean
            uc = 1 - 0.798*(std/mean)
            sectores.append((mean, std, uc, du))
            print(sectores)

    def start(self):
        self.get_data()
        self.set_vars()
        self.set_constrs_sprinklers()
        self.set_vecinos_cts()
        self.set_constrains_obj()
        self.set_constrains_cost()
        self.set_objetivo()
        self.optimizar()
        self.analizar()
        self.get_UC()

if __name__ == "__main__":
    gurobi = SolverGurobi()
    gurobi.start()
