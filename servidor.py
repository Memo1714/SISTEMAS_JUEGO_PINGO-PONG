
import socket
import json
import pygame

# Configuración del servidor
HOST = "0.0.0.0"
PORT = 5005

ANCHO = 1280
ALTO = 720
VELOCIDAD_RAQUETA = 600

class Pelota:
    """Clase que controla la posición y movimiento de la pelota."""

    def __init__(self):
        self.x = ANCHO / 2
        self.y = ALTO / 2
        self.vel_x = 400
        self.vel_y = 300
        self.radio = 10

    def mover(self, dt):
        # Mover la pelota según su velocidad
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt

        # Rebotar en los bordes superior e inferior
        if self.y - self.radio <= 0 or self.y + self.radio >= ALTO:
            self.vel_y *= -1

    def reiniciar(self, direccion):
        # Regresar la pelota al centro
        self.x = ANCHO / 2
        self.y = ALTO / 2
        self.vel_x = 400 * direccion
        self.vel_y = 300

class Juego:
    """Clase que administra las raquetas y las reglas del juego."""

    def __init__(self):
        self.pelota = Pelota()

        self.p1_y = 300
        self.p2_y = 300

        self.puntos1 = 0
        self.puntos2 = 0

    def mover_raqueta(self, jugador, teclas, dt):
        # Determinar qué raqueta debe moverse
        if jugador == "p1":
            posicion = self.p1_y
        else:
            posicion = self.p2_y

        if teclas.get("up"):
            posicion -= VELOCIDAD_RAQUETA * dt

        if teclas.get("down"):
            posicion += VELOCIDAD_RAQUETA * dt

        # Evitar que la raqueta salga de la pantalla
        posicion = max(0, min(ALTO - 120, posicion))

        if jugador == "p1":
            self.p1_y = posicion
        else:
            self.p2_y = posicion

    def actualizar(self, dt):
        """Actualiza pelota, colisiones y puntos."""
        self.pelota.mover(dt)

        x = self.pelota.x
        y = self.pelota.y
        radio = self.pelota.radio

        # Crear los rectángulos de las raquetas
        raqueta1 = pygame.Rect(20, self.p1_y, 20, 120)
        raqueta2 = pygame.Rect(1240, self.p2_y, 20, 120)

        # Colisión con la raqueta izquierda
        if self.pelota.vel_x < 0:
            if raqueta1.collidepoint(x - radio, y):
                self.pelota.x = raqueta1.right + radio
                self.pelota.vel_x *= -1.20
                self.pelota.vel_y *= 1.20

        # Colisión con la raqueta derecha
        if self.pelota.vel_x > 0:
            if raqueta2.collidepoint(x + radio, y):
                self.pelota.x = raqueta2.left - radio
                self.pelota.vel_x *= -1.20
                self.pelota.vel_y *= 1.20

        # Verificar puntos
        if self.pelota.x + radio < 0:
            self.puntos2 += 1
            self.pelota.reiniciar(1)

        elif self.pelota.x - radio > ANCHO:
            self.puntos1 += 1
            self.pelota.reiniciar(-1)

    def obtener_estado(self):
        """Devuelve los datos que necesitan los clientes."""
        return {
            "ball_x": self.pelota.x,
            "ball_y": self.pelota.y,
            "p1_y": self.p1_y,
            "p2_y": self.p2_y,
            "score_p1": self.puntos1,
            "score_p2": self.puntos2
        }

class Servidor:
    """Clase encargada de la comunicación entre los jugadores."""

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((HOST, PORT))
        self.socket.setblocking(False)

        self.juego = Juego()
        self.clientes = {}

        # Guardar las últimas teclas recibidas
        self.teclas = {
            "p1": {},
            "p2": {}
        }

        print("Servidor Pong activo en el puerto", PORT)

    def recibir_datos(self):
        """Recibe los controles y registra a los jugadores."""
        while True:
            try:
                datos, direccion = self.socket.recvfrom(1024)
                mensaje = json.loads(datos.decode())

                # Registrar máximo dos jugadores
                if direccion not in self.clientes.values():
                    if "p1" not in self.clientes:
                        self.clientes["p1"] = direccion
                        print("Jugador 1 conectado")

                    elif "p2" not in self.clientes:
                        self.clientes["p2"] = direccion
                        print("Jugador 2 conectado")

                # Identificar al jugador
                for jugador, cliente in self.clientes.items():
                    if cliente == direccion:
                        self.teclas[jugador] = mensaje.get("keys", {})

            except BlockingIOError:
                break

            except (ValueError, UnicodeError, TypeError):
                print("Se recibió un mensaje incorrecto")

    def enviar_datos(self):
        """Envía el estado del juego a ambos jugadores."""
        estado = self.juego.obtener_estado()
        datos = json.dumps(estado).encode()

        for direccion in self.clientes.values():
            self.socket.sendto(datos, direccion)

    def iniciar(self):
        """Inicia el bucle principal del servidor."""
        pygame.init()
        reloj = pygame.time.Clock()

        try:
            while True:
                dt = reloj.tick(60) / 1000

                self.recibir_datos()

                # Actualizar movimientos de los jugadores
                for jugador in self.clientes:
                    self.juego.mover_raqueta(
                        jugador,
                        self.teclas[jugador],
                        dt
                    )

                self.juego.actualizar(dt)
                self.enviar_datos()

        except KeyboardInterrupt:
            print("Servidor detenido")

        finally:
            self.socket.close()
            pygame.quit()

# Iniciar el servidor
if __name__ == "__main__":
    servidor = Servidor()
    servidor.iniciar()