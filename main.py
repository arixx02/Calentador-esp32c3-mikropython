from lcd_i2c import LCD
from machine import I2C, Pin, PWM
import pad
from time import sleep
from machine import ADC
import time
import micropython
import network
from umqtt.simple import MQTTClient
#para testear hagan un dashboard en adafruit con un telcado y un led
#en este caso el teclado es el topic_ingreso y el led es el topic_led. tener en cuenta al conectar
#Indicamos red WIFI y clave
ssid = 'Wokwi-GUEST'#red wifi para simular en wokwi
wifipassword = ''
#Datos Server MQTT (Broker)
#Indicamos datos MQTT Broker (server y puerto)
mqtt_server = 'io.adafruit.com'
port = 1883
user = '' #definido en adafruit
password = '' #key adafruit
#Indicamos ID(unico) y topicos
client_id = ''#aca va el nombre de usuario de adafruit
topic_ingreso = ''#aca va el path al feed respectivo
topic_Led=''

#Definimos modo Station (conectarse a Access Point remoto)
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
#Conectamos al wifi
sta_if.connect(ssid, wifipassword)
print("Conectando")
while not sta_if.isconnected():
  print(".", end="")
  time.sleep(0.1)
print("Conectado a Wifi!")
#Vemos cuales son las IP
print(sta_if.ifconfig())

# Función de callback para manejar mensajes entrantes
# Función de callback para manejar mensajes entrantes
def callback_ingreso(topic, msg):
    global received_value  # Usar la variable global
    dato = msg.decode('utf-8')
    topicrec = topic.decode('utf-8')
    print("Cambio en: " + topicrec + ":" + dato)
    if topicrec == topic_ingreso:
        received_value = dato

def publish_message(topic, message):
    conexionMQTT.publish(topic, message)
    print(f"Mensaje publicado a {topic}: {message}")

#Intentamos conectarnos al broker MQTT
try:
    conexionMQTT = MQTTClient(client_id, mqtt_server,user=user,password=password,port=int(port))
    conexionMQTT.set_callback(callback_ingreso)
    conexionMQTT.connect()
    conexionMQTT.subscribe(topic_ingreso)
    conexionMQTT.subscribe(topic_Led)
    print("Conectado con Broker MQTT")
except OSError as e:
    #Si fallo la conexion, reiniciamos todo
    print("Fallo la conexion al Broker, reiniciando...")
    time.sleep(5)
    machine.reset()


#configuracion para el lcd
I2C_ADDR = 0x27     # DEC 39, HEX 0x27
i2c = I2C(0, scl=Pin(10), sda=Pin(3), freq=800000)
lcd = LCD(addr=I2C_ADDR, cols=20, rows=4, i2c=i2c)


# poner todas las columnas en bajo. Iniciar el lcd
lcd.begin()

def ingreso(string):
    global received_value
    tecla_presionada = None
    contador_digitos = 0
    lista_ingreso = []
    string_ingreso = ''
    columna_ingreso = 0
    ya_escrito = 0
    # Esta flag sirve para que no se escriba constantemente el primer mensaje
    # Hace que sea más rápido al tocar el botón también
    while True:
        received_value=None
        tecla_presionada = None
        if ya_escrito == 0:
            lcd.clear()
            lcd.print("por favor ingrese")
            lcd.set_cursor(col=0, row=1)
            lcd.print(f"{string}:")
            lcd.set_cursor(col=0, row=3)
            lcd.print("#confirmar, *borrar")
            ya_escrito = 1
            lcd.cursor()
            lcd.blink_on()
        try:
            while True:
                conexionMQTT.check_msg()
                if received_value is not None:
                    tecla_presionada = str(received_value)
                    received_value = None  # Resetea el valor después de usarlo
                    break
        except KeyboardInterrupt:
            conexionMQTT.disconnect()
            print("Desconectado de Adafruit IO")
        tecla_presionada=str(tecla_presionada)
        if tecla_presionada == '*':
            if contador_digitos > 0:
                lista_ingreso.pop()
                contador_digitos -= 1
                columna_ingreso -= 1
                lcd.set_cursor(col=1 + columna_ingreso, row=2)
                lcd.print(' ')
        elif tecla_presionada == '#':
            if contador_digitos != 0:
                for i in lista_ingreso:
                    string_ingreso += i
                return int(string_ingreso)
            else:
                lcd.clear()
                lcd.print("no se ingreso ningun numero, retorno 0")
                return 0
        elif tecla_presionada in ['0','1','2','3','4','5','6','7','8','9']:
            lista_ingreso.append(tecla_presionada)
            lcd.set_cursor(col=1 + columna_ingreso, row=2)
            lcd.print(tecla_presionada)
            contador_digitos += 1
            columna_ingreso += 1
        tecla_presionada = None

def presionar_tecla_continuar():
    global received_value
    received_value=None
    try:
        while True:
            conexionMQTT.check_msg()
            if received_value is not None:
                break  # Resetea el valor después de usarlo
    except KeyboardInterrupt:
        conexionMQTT.disconnect()
        print("Desconectado de Adafruit IO")

def menu(tiempo,temperatura):
    global received_value
    received_value=None
    lcd.clear()
    lcd.print(f"[1]encender. {temperatura}C {tiempo}s.")
    lcd.set_cursor(col=0,row=1)
    lcd.print("[2]nuevo ingreso")
    lcd.set_cursor(col=0,row=2)
    lcd.print("[3]terminar y cerrar")
    lcd.set_cursor(col=0,row=3)
    lcd.print("presione una tecla")
    presionar_tecla_continuar()
    seleccion=ingreso("seleccion")
    while seleccion not in [1,2,3]:
        lcd.clear()
        lcd.print("seleccion invalida")
        sleep(1)
        seleccion=ingreso("seleccion")
    return seleccion

def encendido(tiempo,temperatura,temperatura_sensor):
    sensor=ADC(1)
    publish_message(topic_Led, '1')
    LedRojo=Pin(0,Pin.OUT)
    LedRojo.value(1)
    lcd.clear()
    lcd.print("calentando")
    lcd.set_cursor(col=0,row=1)
    lcd.print("temperatura")
    while(temperatura_sensor<temperatura-(temperatura*(3/100))):
        voltaje_sensor=sensor.read()
        temperatura_sensor=0.00000000000076755*(voltaje_sensor**4)-0.000000010616*(voltaje_sensor**3)+0.00004643*(voltaje_sensor**2)-0.10262*voltaje_sensor+118.51
        lcd.set_cursor(col=0,row=2)
        lcd.print(str(temperatura_sensor))
        lcd.set_cursor(col=0,row=4)
        lcd.print(f"objetivo: {temperatura}C")
        sleep(0.3)
        if(temperatura_sensor>=temperatura-(temperatura*(3/100))):
            sleep(tiempo)
            break
    publish_message(topic_Led, '0')
    LedRojo.value(0)

def seteo_temperatura():
    global received_value
    received_value=None
    sensor=ADC(1)
    try:
        while True:
            conexionMQTT.check_msg()
            voltaje_sensor=sensor.read()
            #para desarrollar la funcion use geogebra y un modelo de regresion polinomico
            temperatura_sensor=0.00000000000076755*(voltaje_sensor**4)-0.000000010616*(voltaje_sensor**3)+0.00004643*(voltaje_sensor**2)-0.10262*voltaje_sensor+118.51
            lcd.clear()
            lcd.print("temperatura actual:")
            lcd.set_cursor(col=0,row=1)
            lcd.print(str(temperatura_sensor)+'C')
            lcd.set_cursor(col=0,row=2)
            lcd.print("presione una tecla")
            sleep(0.5)
            if received_value is not None:
                    return temperatura_sensor
    except KeyboardInterrupt:
        conexionMQTT.disconnect()
        print("Desconectado de Adafruit IO")

if __name__=="__main__":
    while True:
        #Si se produce una excepcion, por ejemplo se corta el wifi
        #o perdemos la conexion MQTT, simplemente vamos a reiniciar
        #el micro para que comience la secuencia nuevamente, asi que
        #usamos un bloque Try+Except
        try:
            #inicializando variables
            lcd.clear()
            lcd.print("Hola!")
            sleep(1)
            lcd.clear()
            seleccion=2
            temperatura=90
            temperatura_sensor=seteo_temperatura()
            #el while valida la temperatura y si seleccionamos 2 repite el ingreso
            while(seleccion==2 or temperatura<temperatura_sensor or temperatura>80):
                temperatura=ingreso('temperatura(C)')
                tiempo=ingreso('tiempo(s)')
                seleccion=menu(tiempo,temperatura)
                #si la temperatura es invalida lo mostramos en pantalla
                if(temperatura<temperatura_sensor or temperatura>80):
                    lcd.clear()
                    lcd.print("temperatura invalida")
                    sleep(1)
            if(seleccion==3):
                lcd.clear()
                lcd.print("Saludos!")
                break
            else:
                encendido(tiempo,temperatura,temperatura_sensor)
        except OSError as e:
            print("Error ",e)
            time.sleep(5)
            machine.reset()


'''
datasheets e informacion de componentes
sensor: https://semiconductors.es/datasheet/KY-013.html
sensor de teperatura digital como segunda opcion--->https://pdf1.alldatasheet.com/datasheet-pdf/view/58557/DALLAS/DS18B20.html
lcd: https://www.vishay.com/docs/37314/lcd020n004l.pdf
teclado: https://components101.com/misc/4x4-keypad-module-pinout-configuration-features-datasheet
ESP32C3: https://www.alldatasheet.com/datasheet-pdf/pdf/1424858/ESPRESSIF/ESP32C3.html
led: https://www.sparkfun.com/datasheets/Components/LED/COM-00533-YSL-R531R3D-D2.pdf
'''
'''
proyectos de los cuales use  modulos y funciones
modulos para control lcd_i2c: https://wokwi.com/projects/356429629276638209
modulos para teclado: https://wokwi.com/projects/356429629276638209
wokwi.com/projects/379581547070731265
'''
'''
menu y logica del programa sin adafruit. Con pad fisico
pad.inicio() #usar al inicio para iniciar los pines del pad
#constantes para el keypad
    Tecla_Arriba   = const(0)
    Tecla_Abajo = const(1)
    teclas = [
                ['1', '2', '3'], 
                ['4', '5', '6'], 
                ['7', '8', '9'], 
                 ['*','0','#']       
                                ]
ingreso de pad por teclado
for fila in range(4):
            for columna in range(3):
                tecla = pad.escanear(fila, columna)
                sleep(0.002)
                if tecla == Tecla_Abajo:
                    tecla_presionada = teclas[fila][columna]

def menu(tiempo,temperatura):
    ya_escrito=0
    tecla=0
    while tecla != Tecla_Abajo:
        for fila in range(4):
                for columna in range(3):
                    tecla = pad.escanear(fila, columna)
                    sleep(0.002)
                    if ya_escrito==0:
                        lcd.clear()
                        lcd.print(f"[1]encender. {temperatura}C {tiempo}s.")
                        lcd.set_cursor(col=0,row=1)
                        lcd.print("[2]nuevo ingreso")
                        lcd.set_cursor(col=0,row=2)
                        lcd.print("[3]terminar y cerrar")
                        lcd.set_cursor(col=0,row=3)
                        lcd.print("#(continuar)")
                        ya_escrito=1
    seleccion=ingreso("seleccion")
    while seleccion not in [1,2,3]:
        lcd.clear()
        lcd.print("seleccion invalida")
        sleep(1)
        seleccion=ingreso("seleccion")
    return seleccion

if __name__=="__main__":
    while True:
        lcd.clear()
        lcd.print("Hola!")
        sleep(1)
        lcd.clear()
        seleccion=2
        sensor=ADC(1)
        x=0
        temperatura=90
        while(x<10):
            valor=sensor.read()
            #valor2=-0.03*valor+94.34
            #valor2=-0.0000000040045*(valor**3)+0.000027456*(valor**2)-0.082197*valor+112.07
            #para desarrollar la funcion use geogebra y un modelo de regresion lineal polinomico
            valor2=0.00000000000076755*(valor**4)-0.000000010616*(valor**3)+0.00004643*(valor**2)-0.10262*valor+118.51
            print(valor2)
            lcd.clear()
            lcd.print("temperatura actual:")
            lcd.set_cursor(col=0,row=1)
            lcd.print(str(valor2)+'C')
            sleep(0.5)
            x+=1
        while(seleccion==2 or temperatura<valor2 or temperatura>80):
            temperatura=ingreso('temperatura')
            #print('la temperatura ingresada es: ',str(temperatura)+'°')
            tiempo=ingreso('tiempo{s}')
            #print('el tiempo ingresado es: ',str(tiempo)+'s')
            seleccion=menu(tiempo,temperatura)
            #print(f'la seleccion ingresada es: {seleccion}')
            if(temperatura<valor2 or temperatura>80):
                lcd.clear()
                lcd.print("temperatura invalida")
                sleep(1)
        if(seleccion==3):
            lcd.clear()
            lcd.print("Saludos!")
            break
        else:
            LedRojo=Pin(0,Pin.OUT)
            LedRojo.value(1)
            lcd.clear()
            lcd.print("calentando")
            lcd.set_cursor(col=0,row=1)
            lcd.print("temperatura")
            while(valor2<temperatura-(temperatura*(3/100))):
                
            (
            valor=sensor.read()
            #valor2=-0.03*valor+94.34
            #valor2=-0.0000000040045*(valor**3)+0.000027456*(valor**2)-0.082197*valor+112.07
            #para desarrollar la funcion use geogebra y un modelo de regresion lineal polinomico
            valor2=0.00000000000076755*(valor**4)-0.000000010616*(valor**3)+0.00004643*(valor**2)-0.10262*valor+118.51
            )
                
                valor=sensor.read()
                valor2=0.00000000000076755*(valor**4)-0.000000010616*(valor**3)+0.00004643*(valor**2)-0.10262*valor+118.51
                lcd.set_cursor(col=0,row=2)
                lcd.print(str(valor2))
                sleep(0.3)
            sleep(tiempo)
            LedRojo.value(0)
'''
'''
esto era un manejo de error (try: except:) que tenia hasta que pense en usar asterisco y numeral para
borrar y confirmar respectivamente.
        except ValueError:
            lcd.clear()
            lcd.print(" el * y el # son")
            lcd.set_cursor(col=0, row=1)
            lcd.print("invalidos, por favor")
            lcd.set_cursor(col=0, row=2)
            lcd.print("ingrese un numero")
            sleep(0.5)
            lcd.clear()
            ya_escrito=0
'''
