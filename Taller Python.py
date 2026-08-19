
"""
SERVIDOR TCP CON FORKING (PROCESOS HIJOS) Y CLIENTE DE PRUEBA
======================================================================
Este programa demuestra cómo crear un servidor de red que puede atender a
múltiples clientes al mismo tiempo creando una "copia" (proceso hijo) de
sí mismo por cada conexión que recibe.
"""

import os            # Permite interactuar con el sistema operativo (para leer el PID/ID del proceso)
import socket        # Nos da las herramientas para crear conexiones de red (Sockets)
import socketserver  # Módulo de alto nivel que simplifica la creación de servidores
import threading     # Permite ejecutar cosas en segundo plano (hilos/threads)

# --- CONFIGURACIÓN GENERAL ---
# 'localhost' el servidor y el cliente se ejecutarán en máquina.
SERVER_HOST = 'localhost'

# Al poner puerto 0, se asignará cualquier puerto libre disponible por el sistema operativo.
SERVER_PORT = 0  

# Tamaño del búfer: cantidad máxima de datos (bytes) que leeremos a la vez del socket.
BUF_SIZE = 1024

# En Python 3, los sockets NO envían texto directo (str), envían secuencias de bytes.
# El prefijo 'b' antes de las comillas convierte el texto a tipo 'bytes'.
ECHO_MSG = b'Hello echo server!'


# ==============================================================================
# 1. LA CLASE CLIENTE (Representa a un usuario que se conecta al servidor)
# ==============================================================================
class ForkedClient:
    """
    Clase encargada de simular un cliente de red.
    Abre una conexión con el servidor, le envía un mensaje y lee la respuesta.
    """
    
    def __init__(self, ip, port):
        """
        El constructor crea el canal de comunicación (socket) y se conecta.
        """
        # socket.AF_INET: Usaremos direcciones de red de tipo IPv4.
        # socket.SOCK_STREAM: Usaremos el protocolo TCP (conexión segura y ordenada).
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Conectamos el socket a la IP y Puerto donde el servidor está escuchando.
        self.sock.connect((ip, port))

    def run(self):
        """
        Método que realiza la interacción de enviar y recibir datos.
        """
        # os.getpid() devuelve el ID del proceso actual en tu sistema operativo.
        current_process_id = os.getpid()
        print(f'PID {current_process_id} Enviando mensaje al servidor: "{ECHO_MSG.decode()}"')
        
        # send(): Envía los bytes del mensaje a través del socket hacia el servidor.
        # Devuelve el número exacto de bytes enviados.
        sent_data_length = self.sock.send(ECHO_MSG)
        print(f"Enviados: {sent_data_length} bytes...")

        # recv(): Se queda esperando hasta recibir la respuesta del servidor.
        response = self.sock.recv(BUF_SIZE)
        
        # response es de tipo bytes, así que usamos .decode() para convertirlo a texto visual.
        # response.decode()[5:] corta los primeros 5 caracteres solo para mostrar una parte del texto.
        print(f"PID {current_process_id} recibió: {response.decode()[5:]}")

    def shutdown(self):
        """
        Cierra el socket para liberar los recursos de red de la computadora.
        """
        self.sock.close()


# ==============================================================================
# 2. EL MANEJADOR DE PETICIONES (Lo que el servidor hace cuando alguien se conecta)
# ==============================================================================
class ForkingServerRequestHandler(socketserver.BaseRequestHandler):
    """
    Esta clase define la LÓGICA del servidor.
    Se crea una instancia de esta clase CADA VEZ que entra una nueva conexión.
    """
    
    def handle(self):
        """
        Este método 'handle' es ejecutado automáticamente por la librería
        socketserver cuando un cliente envía datos.
        """
        # self.request es el socket del cliente que se acaba de conectar.
        # Leemos los datos que envió el cliente.
        data = self.request.recv(BUF_SIZE)
        
        # Obtenemos el PID del proceso que está ejecutando esta respuesta concreta.
        # Gracias al 'Forking', este PID será el de un proceso HIJO recién creado.
        current_process_id = os.getpid()
        
        # preparamos la respuesta pegando el ID del proceso hijo con el texto recibido.
        # .encode() convierte la cadena de texto de vuelta a 'bytes' para enviarla.
        response = f"{current_process_id}: {data.decode()}".encode()
        
        print(f"Servidor enviando respuesta [PID: datos] = [{response.decode()}]")
        
        # Respondemos de vuelta al cliente.
        self.request.send(response)


# ==============================================================================
# 3. EL SERVIDOR CON FORKING (El creador de procesos)
# ==============================================================================
class ForkingServer(socketserver.ForkingMixIn, socketserver.TCPServer):
    """
    Esta clase combina dos funcionalidades (Herencia múltiple):
    1. ForkingMixIn: La capacidad de clonarse en un proceso hijo por cada cliente.
    2. TCPServer: La capacidad básica de ser un servidor de red TCP.
    
    No necesita código adentro (usamos 'pass') porque hereda todo lo necesario.
    """
    pass


# ==============================================================================
# 4. FUNCIÓN PRINCIPAL (Punto de entrada de nuestro programa)
# ==============================================================================
def main():
    # --- PASO A: Crear e Iniciar el Servidor ---
    # Creamos el servidor indicándole el Host/Puerto y qué clase manejará las peticiones.
    server = ForkingServer((SERVER_HOST, SERVER_PORT), ForkingServerRequestHandler)
    
    # server_address nos dice qué puerto libre asignó el sistema operativo.
    ip, port = server.server_address 
    
    # Ponemos a ejecutar el servidor (server.serve_forever) dentro de un hilo secundario
    # (Thread) para que no 'congele' la ejecución de nuestro programa en la consola.
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True  # Para que el hilo se termine automáticamente al cerrar el programa.
    server_thread.start()
    
    print(f'Bucle del servidor corriendo en PID Principal: {os.getpid()}')

    # --- PASO B: Probar con el PRIMER cliente ---
    client1 = ForkedClient(ip, port) # Se conecta al servidor
    client1.run()                     # Envía y recibe mensaje

    # --- PASO C: Probar con un SEGUNDO cliente ---
    client2 = ForkedClient(ip, port) # Se conecta al servidor otra vez
    client2.run()                     # Envía y recibe mensaje

    # --- PASO D: Limpieza y Apagado ---
    server.shutdown()    # Apaga el bucle del servidor
    client1.shutdown()   # Cierra la conexión del cliente 1
    client2.shutdown()   # Cierra la conexión del cliente 2
    server.socket.close()# Cierra la conexión principal del servidor


# Comprobación estándar en Python para saber si este archivo se está ejecutando directamente.
if __name__ == '__main__':
    main()