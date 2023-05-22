from gurobipy import GRB, Model, quicksum
from random import randint, seed, uniform
from Grilla import Chl, Whlr, Vhlr, Rhlr
import os 
import json


class Sector():
    def __init__(self) -> None:
        self.num_fil = None
        self.num_col = None
        self.id = None


class SolverGurobi():

    def __init__(self, inversion, min_c, c_a) -> None:
        self.model = Model()
        self.path = "sectores.json"
        self.n_sectores = None
        self.fil = None
        self.col = None
        self.sectores = {}
        self.n_r = 0
        self.R = set((1,2,3, 4, 5)) # Evaluar la unidad de medida de las grillas, los radios estan en metros y 
                              # Tienen que pasar a cuadrados

        self.posible_places = {} # Diccionario que de llave tiene el str "radio, sector" y de valor tiene una
                                 # tupla de valores (F,C) donde se puede colocar el regador de dicho radio
                 
        self.not_posible_places = {} # Diccionario que de llave tiene el "fila,columna,radio" y de valor tiene una
                                     # lista de valores donde no puede haber otro regador de la forma 

        self.vecinos_places = {} # Diccionario que de llave tiene la fila, columna y el radio y de valor tiene
                                 # lista de valores donde si hay otro regador es vecino
        
        self.regados = {}

        self.vars = {}

        self.inversion = inversion # Diccionario que tiene de llave el sector y la inversion a este
        self.min_cover = min_c
        self.costo_aspersor = c_a

    def get_data(self):
        print("Obteniendo sector")
        with open(self.path, "r") as file:
            info = json.load(file)
            self.n_sectores = info["num_sectores"]
            self.fil = info["filas"]
            self.col = info["columnas"]
        self.process_data()
        print("Termine Obteniendo sector")

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

    def set_vars(self):
        print("Setting vars")
        for id_sector in self.sectores.keys():
            sector: Sector = self.sectores[id_sector]
            F = range(sector.num_fil)
            C = range(sector.num_col)
            nombre = f"x{sector.id}_f,c,r"
            self.vars[f"x{sector.id}"] = self.model.addVars(F, C, self.R,
                                                 vtype=GRB.BINARY,
                                                 name=nombre)
            self.vars[f"r{sector.id}"] = self.model.addVars(F,C, vtype = GRB.BINARY, name = f"r{sector.id}_f,c")
            self.vars[f"v{sector.id}"] = self.model.addVars(F,C,F,C, vtype=GRB.BINARY, name=f"v{sector.id}_f,c,l,h")
        self.vars["e"] = self.model.addVar(vtype = GRB.CONTINUOUS, name = "e1")
        self.model.update()
        print("Termine vars")


    def set_constrs_sprinklers(self):
        print("Setting sprinklers constrais")
        for id_sector in self.sectores.keys():
            sector: Sector = self.sectores[id_sector]
            var = self.vars[f"x{sector.id}"]
            # Restriccion solo haber a lo mas un regador en dicho cuadrado
            for radio in self.R:
                self.n_r += 1
                key = radio
                F, C = self.posible_places[sector.id][key]
                # Restriccion solo haber a lo mas un regador en dicho cuadrado de ese radio
                self.model.addConstrs((var[f,c,radio] <= 1 for f in F for c in C),
                                       name=f"R{self.n_r}")
            # Restriccion solo haber a lo mas un regador de cualquier tipo en la casilla
            self.n_r += 1
            self.model.addConstrs((quicksum(var[f, c, r] for r in self.R) <= 1
                                   for f in range(sector.num_fil) 
                                   for c in range(sector.num_col)),
                                       name=f"R{self.n_r}")
            # Restriccion: Si hay un regador en f,c de radio r entonces no puede haber un regador en 
            # los lugares que diga el diccionario
            for radio in self.R:
                for fil in range(sector.num_fil):
                    for col in range(sector.num_col):
                        key = (fil,col,radio)
                        not_places: list = self.not_posible_places[sector.id].get(key)
                        if not_places is None:
                            continue
                        self.n_r += 1
                        self.model.addConstrs((1 - var[fil ,col, radio] >= quicksum(var[f2, c2, a] for a in self.R)
                                               for f2 in range(sector.num_fil)
                                               for c2 in range(sector.num_col)
                                               if tuple([f2, c2]) in not_places), name=f"R{self.n_r}")
        print("Termine Setting sprinklers constrais")

    def set_vecinos_cts(self):
        # Restriccion: Saber cuantos vecinos hay
        print("Setting Vecinos constrais")
        for z in range(self.n_sectores):
            sector:Sector = self.sectores[z]
            var = self.vars[f"x{sector.id}"]
            varvec = self.vars[f"v{sector.id}"]
            for radio in self.R:
                for fil in range(sector.num_fil):
                    for col in range(sector.num_col):
                        key = (fil,col,radio)
                        vecinos: list = self.vecinos_places[sector.id].get(key)
                        if vecinos is None:
                            continue
                        self.n_r += 1
                        self.model.addConstrs((var[fil,col,radio] + quicksum(var[l,h,a] for a in self.R)
                                              <= 1 + varvec[fil,col,l,h]
                                              for l in range(sector.num_fil)
                                              for h in range(sector.num_col)
                                              if (l,h) in vecinos) , name = f"R{self.n_r}")
                        self.n_r += 1
                        self.model.addConstrs((var[fil,col,radio] >=  varvec[fil,col,l,h]
                                              for l in range(sector.num_fil)
                                              for h in range(sector.num_col)
                                              if (l,h) in vecinos) , name = f"R{self.n_r}")
                        self.n_r += 1
                        
                        self.model.addConstrs((quicksum(var[l,h,a] for a in self.R)>=  varvec[fil,col,l,h]
                                              for l in range(sector.num_fil)
                                              for h in range(sector.num_col)
                                              if (l,h) in vecinos) , name = f"R{self.n_r}")
        print("Termine Setting Vecinos constrais")


    def set_constrains_obj(self):
        print("Setting Pasto cubierto constrais")
        self.n_r += 1
        self.model.addConstr(self.vars["e"] <= 1-self.min_cover, name =f"R{self.n_r}")
        self.n_r += 1
        self.model.addConstr(self.vars["e"] >= 0.0, name =f"R{self.n_r}")
        for id_sector in self.sectores.keys():
            sector: Sector = self.sectores[id_sector]
            var = self.vars[f"x{sector.id}"]
            varreg = self.vars[f"r{sector.id}"]
            e = self.vars["e"]
            dv = sector.num_col * sector.num_fil
            for r in self.R:
                for c in range(sector.num_col):
                    for f in range(sector.num_fil):
                        if self.posible_places[sector.id].get((f,c,r)) is None:
                            continue
                        self.n_r += 1
                        self.model.addConstrs((var[f, c, r] <= varreg[l,h]
                                            for h in range(sector.num_col)
                                            for l in range(sector.num_fil) 
                                            if (l,h) in self.regados[sector.id][(f, c, r)]), 
                                            name = f"R{self.n_r}")
            self.n_r += 1
            self.model.addConstrs((varreg[l,h] <= quicksum(var[f,c,r] 
                                            for r in self.R 
                                            for c in range(r, sector.num_col-r)
                                            for f in range(r, sector.num_fil-r)
                                            if (l,h) in self.regados[sector.id].get((f,c,r))) 
                                            for h in range(sector.num_col)
                                            for l in range(sector.num_fil)), name = f"R{self.n_r}")
            self.n_r += 1
            self.model.addConstr((quicksum(varreg[l,h] 
                                            for l in range(sector.num_fil)
                                            for h in range(sector.num_col))/dv + e == 1), name = f"R{self.n_r}")
        print("Termine Setting Pasto cubierto constrais")

    def set_constrains_cost(self):
        print("Setting Costo constrais")
        for id_sector in self.sectores.keys():
            sector: Sector = self.sectores[id_sector]
            inversion = self.inversion[id_sector]
            var = self.vars[f"x{sector.id}"]
            costo = self.costo_aspersor
            self.n_r += 1
            self.model.addConstr(costo * quicksum(var[f,c,r] 
                                           for r in self.R
                                           for c in range(sector.num_col)
                                           for f in range(sector.num_fil)) <= inversion,name = f"R{self.n_r}" )
            
        print("Termine setting Costo constrais")

    def set_objetivo(self):
        print("Empeze a setear objetivo")
        global_function = 0.0
        for id_sector in self.sectores.keys():
            sector: Sector = self.sectores[id_sector]
            varvec = self.vars[sector.id]
            funcion_sector = quicksum(varvec[f,c,l,h] 
                            for c in range(self.sectores[id_sector].num_col)
                            for f in range(self.sectores[id_sector].num_fil)
                            for l in range(self.sectores[id_sector].num_fil)
                            for h in range(self.sectores[id_sector].num_col))
            global_function += funcion_sector
        self.model.setObjective(global_function, GRB.MAXIMIZE) 
        print("Termine setear objetivo")
    
    def optimizar(self):
        print("Empeze a optimizar")
        self.model.optimize()
    
    def analizar(self):
        with open("sector.txt", "w") as file:
            for id_sector in self.sectores.keys():
                file.write(f"Mostrando sector {id_sector}\n")
                sector = []
                fila = []
                var = self.vars[f"x{id_sector}"]
                for i in range(self.sectores[id_sector].num_fil):
                    fila = []
                    for j in range(self.sectores[id_sector].num_col):
                        encontre = False
                        for a in self.R:
                            radio = 0
                            if var[i,j,a].x == 1:
                                print(f"fila {i} columna {j} radio{a}", var[i,j,a].x)
                                encontre = True
                                radio = a
                                break
                            if var[i,j,a].x == 0:
                                continue
                        if encontre:
                            fila.append(str(radio))
                        else:
                            fila.append("0")
                    sector.append(fila)
                for fila in sector:
                    fila.append("\n")
                    file.write("|".join(fila))
        
                        
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

if __name__ == "__main__":
    inversion1 = {}
    inversion1[0] = 100000000000000
    inversion1[1] = 100000000000000
    min_c1 = 0.90
    c_a1 = 20000
    gurobi = SolverGurobi(inversion=inversion1, min_c=min_c1, c_a=c_a1)
    gurobi.start()