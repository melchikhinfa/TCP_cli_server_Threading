import configparser
import hashlib
import logging
import os
import pathlib
import pickle
import socket
import threading

from dotenv import load_dotenv

load_dotenv()
CLIENT_LOG_FILE = './client/logs/cli.log'
cli_log = logging.getLogger(__name__)
cli_log.setLevel(logging.INFO)

file_handler = logging.FileHandler(CLIENT_LOG_FILE, mode="a")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(funcName)s: %(message)s")

file_handler.setFormatter(formatter)
cli_log.addHandler(file_handler)

path_to_config = os.path.dirname(os.path.dirname(__file__)) + "/server/settings.ini"
config = configparser.ConfigParser()
config.read(path_to_config)

DEFAULT_HOST = config.get('Server', 'DEFAULT_HOST')
DEFAULT_PORT = config.get('Server', 'DEFAULT_PORT')


class Client:
    def __init__(self, ip_addr, port):
        self.host = ip_addr
        self.port = int(port)
        self.sock = None

    def command_processing(self):
        """Обработчик команд"""
        while True:
            command = input("Введите команду: ").split(' ')
            comm = command[0]
            if comm == "manual":
                data = {"comm": comm}
                self.sock.sendall(pickle.dumps(data))
            elif comm == "exit":
                data = {"comm": comm}
                self.sock.sendall(pickle.dumps(data))
                self.sock.close()
                break
            elif comm == "upload":
                data = pathlib.Path(command[1]).read_bytes()
                size = len(data)
                dest_path = command[2]
                file_name = command[1].split('/')[-1]
                upload_data = {"comm": comm, "size": size, "dest_path": dest_path, "data": data, "file_name": file_name}
                self.sock.sendall(pickle.dumps(upload_data))
            elif comm == "download":
                file_dir = command[1]
                download_dir = command[2]
                data = {"comm": comm, "file_dir": file_dir}
                self.sock.sendall(pickle.dumps(data))
                resp = pickle.loads(self.sock.recv(4096))
                if resp:
                    download_dir = pathlib.Path(download_dir).joinpath(resp['file_name'])
                    pathlib.Path(download_dir).write_bytes(resp['data'])
            else:
                data = {"comm": comm, "args": command[1:]}
                self.sock.sendall(pickle.dumps(data))

            response = self.sock.recv(1024).decode()
            if response:
                print(f"Результат выполнения операции {comm}:\n ---{response}")
            else:
                print("Ошибка получения данных. Попробуйте еще раз.")
                break

    def main_logic(self):
        print("Авторизуйтесь в системе используя логин и пароль --->")
        while True:
            username = input("Введите имя пользователя: ")
            password = input("Введите пароль: ")
            hashed_pass = hashlib.md5(password.encode()).hexdigest()
            data = f"{username}:{hashed_pass}"
            if username != "" and password != "":
                self.sock.sendall(data.encode())
                cli_log.info(f"Отправлен запрос на авторизацию пользователя {username}")
                response = self.sock.recv(1024).decode()
                if response == "success":
                    cli_log.info(f"Пользователь {username} успешно авторизован")
                    print("Вы успешно авторизованы! Отправьте команду 'manual' для получения справки по командам:")
                    self.command_processing()
            #self.command_processing()

    def init_connection(self):
        """Инициализация подключения"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(True)
        sock.connect((self.host, self.port))
        self.sock = sock
        cli_log.info(f"Подключение к серверу {self.host}:{self.port} прошло успешно")
        thr = threading.Thread(target=self.main_logic)
        thr.start()


if __name__ == '__main__':
    client = Client(DEFAULT_HOST, DEFAULT_PORT)
    client.init_connection()
