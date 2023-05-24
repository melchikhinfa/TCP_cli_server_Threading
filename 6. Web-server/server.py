import os
import threading
import socket
import datetime
import logging
from configparser import ConfigParser

config_file = './config.ini'
config = ConfigParser()
config.read(config_file)
logging.basicConfig(format="%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s",
                    handlers=[logging.FileHandler(config.get('logging', 'log_file'))],
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class WebServer:
    def __init__(self):
        self.sock = None
        self.host = config.get('server', 'host')
        self.port = config.getint('server', 'port')
        self.backlog = config.getint('server', 'backlog')
        self.server_dir = config.get('server', 'server_dir')
        self.max_request_size = config.getint('server', 'max_request_size')
        self.allowed_files = config.get('server', 'allowed_files').split(',')
        self.allowed_pic = config.get('server', 'allowed_pic').split(',')

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(self.backlog)
        logger.info("Сервер запущен на {}:{}".format(self.host, self.port))

        while True:
            self.conn_accept()

    def conn_accept(self):
        client_sock, address = self.sock.accept()
        threading.Thread(target=self.listen_to_client, args=(client_sock, address)).start()

    def stop(self):
        self.sock.close()

    def listen_to_client(self, client_sock, address):
        size = self.max_request_size
        data = client_sock.recv(size)
        logger.info("Получен запрос от {}:{}".format(address[0], address[1]))
        if data:
            response = self.handle_request(data, address[0])
            client_sock.send(response)
            logger.info("Отправлен ответ клиенту {}:{}".format(address[0], address[1]))
        else:
            pass

    def handle_request(self, data, addr):
        headers = data.decode().split('\n')
        filename = headers[0].split()[1]
        if filename == "/":
            filename = "/index.html"

        logger.info(f"Запроc на файл: {filename} от ip: {addr}")
        requested_file = self.server_dir + filename

        if not os.path.isfile(requested_file):
            response = self.prepare_headers(404, data_type="Not available")
            response += self.read_file('./data/404.html', 'html')
            response = response.encode()
        else:
            data_type = filename.split(".")[-1]
            if data_type in self.allowed_files:
                response = self.prepare_headers(200, data_type)
                response += self.read_file(requested_file, data_type)
                response = response.encode()
            elif data_type in self.allowed_pic:
                response = self.prepare_headers(200, data_type).encode()
                response += self.read_file(requested_file, data_type)
            else:
                response = self.prepare_headers(403, data_type)
                response += self.read_file('./data/403.html', 'html')
                response = response.encode()
        return response

    def prepare_headers(self, code, data_type):
        header = ''
        if code == 200:
            header = 'HTTP/1.1 200 OK\n'
        elif code == 404:
            header = 'HTTP/1.1 404 Not Found\n'
        elif code == 403:
            header = 'HTTP/1.1 403 Forbidden\n'

        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        header += f'Date: ' + current_date + '\n' \
                     f'Content-type: {data_type}\n' \
                     'Server: Simple-Python-HTTP-Server\n' \
                     'Connection: close\n\n'
        return header

    def read_file(self, filename, data_type):
        if data_type in self.allowed_files:
            with open(filename, 'r') as file:
                return file.read().replace("\n", '')
        else:
            with open(filename, 'rb') as file:
                return file.read()


if __name__ == "__main__":
    server = WebServer()
    server.start()
