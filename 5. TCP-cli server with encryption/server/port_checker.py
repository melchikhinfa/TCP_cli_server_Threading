import socket
import random
from serv_logger import server_logger

ip_addr = "127.0.0.1"


class PortValidator:
    def __int__(self):
        pass

    def port_validation(self, port: int):
        """Проверка порта на корректность ввода и возможность подключения,
            если занят - генерирует и возвращает новый порт"""
        port = int(port)
        if 1023 < port < 65536 and self.check_port_open(port) == True:
            return port
        else:
            server_logger.info(f"Порт {port} занят, генерируем новый свободный порт")
            port = self.generate_free_port()
            return port

    @staticmethod
    def check_port_open(port: int) -> bool:
        """Проверка порта на возможность подключения"""
        port = int(port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((ip_addr, port))
            server_logger.info(f"Порт {port} свободен")
            return True
        except socket.error:
            server_logger.info(f"Порт {port} занят")
            return False
        finally:
            sock.close()

    def generate_free_port(self):
        """Генерация свободного порта"""
        check_flag = False
        while not check_flag:
            port = random.randint(1024, 65535)
            check_flag = self.check_port_open(port)
            return port
