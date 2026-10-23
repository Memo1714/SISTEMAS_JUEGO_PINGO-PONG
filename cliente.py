
import socket
import json
import pygame

# Configuración del cliente
SERVER_IP = "172.17.38.159"
SERVER_PORT = 5005

ANCHO = 1280
ALTO = 720

class Conexion:
    """Clase que permite comunicarse con el servidor."""

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)
        self.servidor = (SERVER_IP, SERVER_PORT)

    def enviar_teclas(self, arriba, abajo):
        """Envía las teclas pulsadas mediante UDP."""
        mensaje = {
            "keys": {
                "up": arriba,
                "down": abajo
            }
        }

        datos = json.dumps(mensaje).encode()
        self.socket.sendto(datos, self.servidor)

    def recibir_estado(self):
        """Recibe la información actualizada del servidor."""
        ultimo_estado = None

        while True:
            try:
                datos, direccion = self.socket.recvfrom(1024)

                if direccion == self.servidor:
                    ultimo_estado = json.loads(datos.decode())

            except BlockingIOError:
                break

            except (ValueError, UnicodeError):
                print("Error al leer datos del servidor")

        return ultimo_estado

    def cerrar(self):
        """Cierra el socket."""
        self.socket.close()

class Pantalla:
    """Clase encargada de dibujar los elementos del juego."""

    def __init__(self):
        self.ventana = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Pong Multijugador")

        self.fuente = pygame.font.SysFont(None, 60)

    def dibujar(self, estado):
        """Dibuja la pelota, las raquetas y el marcador."""
        self.ventana.fill("darkgrey")

        # Obtener posiciones
        pelota_x = int(estado["ball_x"])
        pelota_y = int(estado["ball_y"])

        p1_y = int(estado["p1_y"])
        p2_y = int(estado["p2_y"])

        # Crear raquetas
        raqueta1 = pygame.Rect(20, p1_y, 20, 120)
        raqueta2 = pygame.Rect(1240, p2_y, 20, 120)

        # Dibujar las raquetas
        pygame.draw.rect(self.ventana, "black", raqueta1)
        pygame.draw.rect(self.ventana, "black", raqueta2)

        # Dibujar la pelota
        pygame.draw.circle(
            self.ventana,
            "black",
            (pelota_x, pelota_y),
            10
        )

        # Dibujar marcador
        marcador = (
            str(estado["score_p1"])
            + "  -  "
            + str(estado["score_p2"])
        )

        texto = self.fuente.render(marcador, True, "black")
        posicion = texto.get_rect(center=(ANCHO // 2, 40))

        self.ventana.blit(texto, posicion)

        pygame.display.flip()

class Cliente:
    """Clase principal que controla el cliente del juego."""

    def __init__(self):
        pygame.init()

        self.conexion = Conexion()
        self.pantalla = Pantalla()
        self.reloj = pygame.time.Clock()

        # Estado inicial mientras llega información del servidor
        self.estado = {
            "ball_x": 640,
            "ball_y": 360,
            "p1_y": 300,
            "p2_y": 300,
            "score_p1": 0,
            "score_p2": 0
        }

        self.ejecutando = True

    def iniciar(self):
        """Ejecuta el juego hasta cerrar la ventana."""
        try:
            while self.ejecutando:

                # Revisar si el usuario cierra la ventana
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        self.ejecutando = False

                if not self.ejecutando:
                    break

                # Leer las teclas del jugador
                teclas = pygame.key.get_pressed()

                arriba = teclas[pygame.K_UP] or teclas[pygame.K_w]
                abajo = teclas[pygame.K_DOWN] or teclas[pygame.K_s]

                # Enviar movimiento al servidor
                self.conexion.enviar_teclas(arriba, abajo)

                # Obtener estado actualizado
                nuevo_estado = self.conexion.recibir_estado()

                if nuevo_estado is not None:
                    self.estado = nuevo_estado

                # Dibujar el juego
                self.pantalla.dibujar(self.estado)

                self.reloj.tick(60)

        finally:
            self.conexion.cerrar()
            pygame.quit()

# Iniciar el cliente
if __name__ == "__main__":
    cliente = Cliente()
    cliente.iniciar()