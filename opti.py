from gurobipy import GRB, Model, quicksum
from random import randint, seed, uniform
import os 
import json


class Sector():
    def __init__(self) -> None:
        self.num_fil = None
        self.num_col = None
        self.id = None


class SolverGurobi():

    def __init__(self) -> None:
        self.model = Model()
        self.path = None
        self.n_sectores = None
        self.fil = None
        self.col = None
        self.sectores = {}
        self.n_r = 0
        self.R = set(3, 5, 7) # Evaluar la unidad de medida de las grillas, los radios estan en metros y 
                              # Tienen que pasar a cuadrados

        self.posible_places = {} # Diccionario que de llave tiene el str "radio, sector" y de valor tiene una
                                 # tupla de valores (F,C) donde se puede colocar el regador de dicho radio
                                
        self.not_posible_places = {} # Diccionario que de llave tiene el "fila,columna,radio" y de valor tiene una
                                     # lista de valores donde no puede haber otro regador de la forma 
                                 
        self.vars = {}

    def get_data(self):
        with open(self.path, "r") as file:
            info = json.load(file)
            self.n_sectores = info["num_sectores"]
            self.fil = info["filas"]
            self.col = info["columnas"]
        self.process_data()

    def process_data(self):
        for n_sector in range(self.n_sectores):
            z = Sector()
            z.id = n_sector
            z.num_fil = self.fil[n_sector]
            z.num_col = self.col[n_sector]
            self.sectores[z.id] = z

    def set_vars(self):
        for id_sector in self.sectores.keys():
            sector: Sector = self.sectores[id_sector]
            F = range(sector.num_fil)
            C = range(sector.num_col)
            nombre = f"x{sector.id}_f,c,r"
            self.vars[f"x{sector.id}"] = self.model.addVars(F, C, self.R,
                                                 vtype=GRB.BINARY,
                                                 name=nombre)
        self.model.update()
 
    def set_constrs_sprinklers(self):
        for id_sector in self.sectores.keys():
            sector: Sector = self.sectores[id_sector]
            var = self.vars[sector.id]
            # Restriccion solo haber a lo mas un regador en dicho cuadrado
            for radio in self.R:
                self.n_r += 1
                set_radio = set(radio)
                key = str(radio)+", "+str(sector.id)
                F, C = self.posible_places[key]
                # Restriccion solo haber a lo mas un regador en dicho cuadrado de ese radio
                self.model.addConstrs((var[f,c,r] <= 1 for f in F for c in C for r in set_radio),
                                       name=f"R{self.n_r}")
            # Restriccion solo haber a lo mas un regador de cualquier tipo en la casilla
            self.n_r += 1
            self.model.addConstrs((quicksum(var[f, c, r] for r in self.R) <= 1
                                   for f in range(sector.num_fil) 
                                   for c in range(sector.num_col)),
                                       name=f"R{self.n_r}")
            # Restriccion: Si hay un regador en f,c de radio r entonces no puede hacer un regador en 
            # los lugares que diga el 
            
            





"""

NUM_SECTORES = 3
sectores = []
for sector in range(NUM_SECTORES):
    z = Sector()
    z.num_fil

model = Model()

F = range()

sectores = set()

R = set(3,5,7)


for sector in sectores:
    F = range(sector.num_fil)
    C = range(sector.num_col)
    x = model.addVars(F, C, R, vtype=GRB.BINARY, name=x)


model.update()

# Coloque aca sus restricciones
model.addConstrs((quicksum(x[i, j] for j in J) == 1 for i in I), name="R1")
model.addConstr((quicksum(y[j] for j in J) == n), name="R2")
model.addConstrs((x[i, j] <= y[j] for i in I for j in J), name="R3")
model.addConstrs((x[i, j] >= y[j] - quicksum(y[k] for k in J if t[i, k]
                  < t[i, j]) for i in I for j in J), name="R4")
model.addConstrs((v[i] <= quicksum(y[j] for j in J
                                   if t[i, j] <= alpha) for i in I), name="R5")
model.addConstrs((w[i] <= quicksum(y[j] for j in J if t[i, j] <= beta)
                  for i in I), name="R6")
model.addConstr((quicksum(v[i] for i in I) ==
                  (0.85 + z1)*quicksum(1 for _ in I)), name="R7")
model.addConstr((quicksum(c[i]*w[i] for i in I) ==
                  (0.9 + z2)*quicksum(c[i] for i in I)), name="R8")
model.addConstr((z1 >= 0), name="R9")
model.addConstr((z2 >= 0), name="R10")

# ------------------------ Funcion Objetivo ---------------------------
funcion_objetivo = (
                    b1 * z1 + b2 * z2 -
                    p * quicksum((t[i, j] - alpha)*x[i, j]
                    for i in I for j in J if t[i, j] > alpha)
                    )

model.setObjective(funcion_objetivo, GRB.MAXIMIZE) 
model.optimize()"""