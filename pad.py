from machine import Pin
from time import sleep
#constantes
Tecla_Arriba   = const(0)
Tecla_Abajo = const(1)
#definicion de filas
teclas = [['1', '2', '3'], ['4', '5', '6'], ['7', '8', '9'], ['-1','0','-1']]
# Defininicón de Pines
filas = [9,8,7,2]
columnas = [6,5,4]

# Definimos los pines de las filas como salida
pines_Filas = [Pin(pin_nombre, mode=Pin.OUT) for pin_nombre in filas]

# Definimos los pines de las columnas de salida
pines_Columnas = [Pin(pin_nombre, mode=Pin.IN, pull=Pin.PULL_DOWN) for pin_nombre in columnas]

#Funciónpara inicializar el teclado

def inicio():
    for fila in range(0,4):
        for col in range(0,3):
            pines_Filas[fila].value(0)

def escanear(fila, columna):
    """ Escaneo del teclado """

    # poner todas las filas en alto
    pines_Filas[fila].value(1)
    key = None

    # verificación al presionar una tecla o evento
    if pines_Columnas [columna].value() == Tecla_Abajo:
        key = Tecla_Abajo
    if pines_Columnas [columna].value() == Tecla_Arriba:
        key = Tecla_Arriba
    pines_Filas [fila].value(0)

    # retorne el estado de la tecla
    return key

