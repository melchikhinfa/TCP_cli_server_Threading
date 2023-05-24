import os
import socket
import threading
import logging
from proc import traffic_quota as quota
import configparser
import pathlib, hashlib
from proc.file_processing import FileProcessing
import pickle


from dotenv import load_dotenv

load_dotenv()

config = configparser.ConfigParser()
path = os.path.dirname(os.path.abspath(__file__)) + "/settings.ini"
config.read(path)


class FileServer:
    def __init__(self):
        self.host = config.get('Server', 'DEFAULT_HOST')
        self.port = int(config.get('Server', 'DEFAULT_PORT'))
        self.work_dir = str(pathlib.Path.home() / config.get('Server', 'DEFAULT_DIR'))
        self.max_quota = int(config.get('Server', 'DEFAULT_QUOTA'))
        self.connection_list = []

        self.conn_logger = self.setup_logger('connection', config.get('Logging', 'CONN_LOG_FILE'))
        self.auth_logger = self.setup_logger('authorization', config.get('Logging', 'AUTH_LOG_FILE'))
        self.file_logger = self.setup_logger('file', config.get('Logging', 'FP_LOG_FILE'))

    @staticmethod
    def setup_logger(name, log_file, level=logging.INFO):
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        handler = logging.FileHandler(log_file, mode='a')
        handler.setFormatter(formatter)

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)
        return logger

    def log_connection(self, message):
        self.conn_logger.info(message)

    def log_authorization(self, message):
        self.auth_logger.info(message)

    def log_file_operation(self, message):
        self.file_logger.info(message)

    def auth(self, client_socket):
        user = os.environ.get('user')
        hashed_password = hashlib.md5(os.environ.get('pass').encode()).hexdigest()
        cli_data = client_socket.recv(1024).decode().split(':')
        cli_username, cli_pass = cli_data[0], cli_data[1]
        if user == cli_username and hashed_password == cli_pass:
            self.log_authorization(f'Клиент {cli_username} авторизован!')
            return True
        else:
            self.log_authorization(f'Ошибка авторизации клиента {cli_username}!')
            client_socket.close()
            return False

    def comm_proc(self, client_socket):
        username = os.environ.get('user')
        fp_logger = self.file_logger
        file_proc = FileProcessing(fp_logger, username)
        while True:
            request = pickle.loads(client_socket.recv(1024))
            comm = request["comm"]
            if comm == "exit":
                client_socket.close()
                self.log_connection(f'Клиент {username} вышел.')
                break
            elif comm == "manual":
                client_socket.sendall(file_proc.command_manual().encode())
                self.log_connection('Мануал отправлен клиенту!')
            elif comm == 'upload':
                file_name = request["file_name"]
                data = request["data"]
                dest_path = request["dest_path"]
                file_size = request["file_size"]
                if file_proc.upload_file(username, dest_path, file_size, data):
                    client_socket.sendall(f'Файл {file_name} успешно загружен на сервер!'.encode())
                    self.log_file_operation(f'Клиент {username}: файл {file_name} успешно загружен на сервер!')
            elif comm == 'download':
                path_to_file = request["file_dir"]
                data = file_proc.download_file(path_to_file)
                file_name = path_to_file.split('/')[-1]
                if file_proc.download_file(path_to_file):
                    data_to_send = {"file_name": file_name, "data": data}
                    client_socket.sendall(pickle.dumps(data_to_send))
                    self.log_file_operation(f'Клиент {username}: файл {file_name} успешно отправлен клиенту!')
                else:
                    self.log_connection(f'Клиент {username}: файл {file_name} не найден на сервере!')
            elif comm == 'lsdir':
                res = file_proc.ls_dir(*request["args"])
                client_socket.sendall(res.encode())
                self.log_connection(f'Результат выполнения операции {comm} отправлен клиенту!')

            elif file_proc.command_routing(comm, *request["args"]):
                client_socket.sendall(f'Операция {comm} успешно выполнена'.encode())
                self.log_connection(f'Результат выполнения операции {comm} отправлен клиенту!')

            else:
                client_socket.sendall(f'Не удалось выполнить операцию {comm}'.encode())
                self.log_connection(f'Результат выполнения операции {comm} отправлен клиенту!')
                print("Не удалось выполнить операцию. Проверьте логи.")
                break

    def handle_client(self, client_socket):
        if self.auth(client_socket):
            client_socket.sendall('success'.encode())
            self.log_connection('Клиент авторизован!')
            self.comm_proc(client_socket)
        else:
            client_socket.sendall('fail'.encode())
            self.log_connection('Клиент не авторизован!')
            self.run()

        if not os.path.exists(self.work_dir):
            os.mkdir(self.work_dir)
            self.log_connection(f'Создана рабочая директория {self.work_dir}')

        username = os.environ.get('user')
        if quota.get_quota(username) > self.max_quota:
            self.log_connection(f"Превышен лимит дискового пространства для пользователя {username}")
            client_socket.sendall(f"Превышен лимит дискового пространства для пользователя {username}".encode())
            client_socket.close()

    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        self.log_connection(f'Сервер инициализирован. Слушает {self.host}:{self.port}')

        try:
            while True:
                client_sock, address = server.accept()
                self.connection_list.append(client_sock)
                self.log_connection(f'Принято соединение от {address[0]}:{address[1]}')
                client_handler = threading.Thread(
                    target=self.handle_client,
                    args=(client_sock,), daemon=True
                )
                client_handler.start()
        except KeyboardInterrupt:
            self.log_connection("Keyboard interrupt. Server stopped.")
            server.close()
        finally:
            server.close()


if __name__ == '__main__':
    server = FileServer()
    server.run()
