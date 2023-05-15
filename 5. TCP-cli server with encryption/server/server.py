import socket, threading, pickle, uuid, datetime, os, sys, time, json
from serv_logger import server_logger, change_stream_logs
from auth import UserRegistration
from port_checker import PortValidator
from settings import *

crypto_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(crypto_path)
from encryption import MessageEncryption, DHKeyExchange


class Server:
    def __init__(self, port):
        server_logger.info("Сервер запускается...")
        self.port = port
        self.sock = None
        self.sessions_list = []
        self.auth_processing = UserRegistration()
        self.socket_init(self.port)
        print("Сервер запущен на порту:", port)
        server_logger.info(f"Инициализация сервера. Слушает порт:{port}")

        # Проверка ключей и режима шифрования
        self.accept_conn = None
        self.secret_key = None
        self.receive_data = None
        self.msg_crypter = None

        self.resume_listening()
        self.commands_routing()

        for session in self.sessions_list:
            self.check_token(session)

    # TODO: Тут какая-то галимотья. Разобраться с потоками и ошибкой при получении сообщения
    def check_keys(self, conn):
        time.sleep(5)
        data = conn.recv(1024)
        cli_pub_key1, cli_pub_key2, cli_pub_key = pickle.loads(data)
        server_logger.info("Получен публичный ключ клиента")

        with open('./certs/key.txt', 'r') as f:
            server_keys = f.read().split(' ')
            secret = server_keys[2]
            encryption = DHKeyExchange(int(secret), int(cli_pub_key1), int(cli_pub_key2))
            server_partial_key = encryption.partial_key

        with open('./certs/cert.txt', 'r') as f:
            cert_keys = f.read().split(' ')
            if str(cli_pub_key) in cert_keys:
                server_logger.info("Ключ клиента подтвержден")
                conn.sendall(pickle.dumps(server_partial_key))
                self.secret_key = encryption.generate_full_key(cli_pub_key)
                server_logger.info("Секретный ключ сгенерирован")
                cr_port = PortValidator().generate_free_port()
                self.msg_crypter = MessageEncryption(self.secret_key)
                encrypted_port = self.msg_crypter.encryptor(str(cr_port))
                conn.sendall(pickle.dumps(encrypted_port))
                server_logger.info(f"Порт для передачи сообщений сгенерирован. Отправляем зашифрованный порт {encrypted_port} клиенту.")
                self.sock.close()
                server_logger.info("Сокет закрыт. Ожидаем переподключения клиента.")
                self.socket_init(cr_port)
                server_logger.info(f"Сокет переинициализирован на зашифрованном порту. Слушает порт {cr_port}.")
                self.encrypted_conn_await()
                server_logger.info(f"Клиент переподключился на зашифрованном порту {cr_port}.")

            else:
                with open('./certs/cert.txt', 'a') as f:
                    f.write(f" {cli_pub_key}")
                self.sock.close()
                server_logger.info("Ключ клиента не подтвержден. Разрыв соединения.")


    def socket_init(self, port):
        """Инициализация подключения"""
        sock = socket.socket()
        sock.bind(("", port))
        sock.listen(0)
        self.sock = sock

    def encrypted_conn_await(self):
        """Ожидание зашифрованного подключения клиента и создание для него отдельного потока на раутинг"""
        while self.receive_data:
            conn, addr = self.sock.accept()
            server_logger.info(f"Подключился клиент {addr[0]}")
            thr = threading.Thread(target=self.route, args=(conn, addr), daemon=True)
            thr.start()

    def conn_await(self):
        """Ожидание подключения клиента и создание для него отдельного потока проверки ключей шифрования"""
        while self.receive_data:
            conn, addr = self.sock.accept()
            server_logger.info(f"Подключился клиент {addr[0]}")
            thr = threading.Thread(target=self.check_keys, args=(conn,), daemon=True)
            thr.start()

    def commands_routing(self):
        """Команды управления сервером"""
        commands = {"exit": {'comm': self.close_server, 'descr': 'Завершение работы сервера'},
                    "pause": {'comm': self.pause_listening, 'descr': 'Приостановка прослушивания порта'},
                    "resume": {'comm': self.resume_listening, 'descr': 'Возобновление прослушивания порта'},
                    "switch logs": {'comm': self.show_or_disable_logs,
                                    'descr': 'Вывод логов сервера в консоль или в файл'},
                    "clear sessions": {'comm': self.clear_sessions_list, 'descr': 'Очистка списка активных сессий'}}
        print("Доступные команды:")
        for key in commands.keys():
            print(key, '-', commands[key]['descr'])

        while True:
            command = input("Введите команду: ")
            if command in commands.keys():
                commands[command]['comm']()
            else:
                print("Команда не распознана")
                print("Доступные команды:")
                for key in commands.keys():
                    print(key, '-', commands[key]['descr'])

    def close_server(self):
        """Завершение работы сервера"""
        self.sock.close()
        server_logger.info("Сервер остановлен")
        exit(0)

    def pause_listening(self):
        """Приостановка прослушивания порта"""
        self.receive_data = False
        server_logger.info("Прослушивание порта приостановлено")

    def resume_listening(self):
        """Возобновление прослушивания порта"""
        self.receive_data = True
        thr = threading.Thread(target=self.conn_await, daemon=True)
        thr.start()

    @staticmethod
    def show_or_disable_logs():
        """Вывод логов сервера в файл или консоль, вызов метода активирует вывод логов в консоль,
        повторный вызов - отключает"""
        change_stream_logs()

    @staticmethod
    def reset_logs():
        """Сброс логов сервера"""
        open('w', SERVER_LOG_FILE).close()
        server_logger.info("Логи сервера сброшены")

    def clear_sessions_list(self):
        '''Очистка списка активных сессий + таблицы идентификации'''
        self.sessions_list.clear()
        self.auth_processing.clear_table()
        server_logger.info("Список активных сессий очищен")
        server_logger.info("Таблица идентификации очищена")

    # Дальше основная логика сервера
    @staticmethod
    def generate_token():
        """Генерация токена для поддержания сессии пользователя"""
        token = str(uuid.uuid4())
        est_time = datetime.datetime.now() + datetime.timedelta(minutes=TOKEN_EST_TIME)
        return token, est_time

    def check_token(self, session):
        """Проверка токена пользователя"""
        active = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)
        if session[4] < datetime.datetime.now() and active is True:
            server_logger.info(f"Сессия пользователя {session[2]} еще активна, генерирую новый токен")
            token, est_time = self.generate_token()
            session[3] = token
            session[4] = est_time
            self.auth_processing.update_info(session[1], session[2], 'active', token, est_time)

        else:
            self.sessions_list.remove(session)
            server_logger.info(f"Сессия пользователя {session[2]} истекла, удаляю из списка активных сессий")
            self.auth_processing.update_info(session[1], session[2], 'offline', '', '')
            self.auth_logic(session[0], session[1])

    def send_message(self, conn, data: dict, ip: str) -> None:
        """Отправка данных"""
        pr_data = data.copy()
        if type(pr_data) == dict:
            cr_data = self.msg_crypter.encrypt_message(pr_data)
            conn.send(pickle.dumps(cr_data))
            server_logger.info(f"Cообщение {cr_data} было отправлено клиенту {ip}")

    def message_logic(self, conn, ip_addr):
        """Логика обработки сообщений"""
        data = ''
        while True:
            cr_data = pickle.loads(conn.recv(4096))
            data = self.msg_crypter.encrypt_message(cr_data)
            username = data["username"]
            server_logger.info(
                f"Получили сообщение {data['text']} от клиента {ip_addr} ({username})"
            )
            data = {"username": username, "text": data['text']}
            server_logger.info(
                f"Текущее кол-во подключений к серверу: {len(self.sessions_list)}"
            )
            for connection in self.sessions_list:
                current_conn, current_ip = connection[0], connection[1]
                try:
                    self.send_message(current_conn, data, current_ip)
                except BrokenPipeError:
                    server_logger.info(f"Клиент {current_ip} отключился")
                    self.auth_processing.update_info(current_ip, username, 'offline', '', '')
                    self.sessions_list.remove(connection)
                    continue
            data = ""
            if not cr_data:
                self.auth_processing.update_info(ip_addr, username, 'offline', '', '')
                break

    def reg_logic(self, conn, addr):
        try:
            encr_data = pickle.loads(conn.recv(1024))
            print(self.secret_key)
        except Exception as e:
            server_logger.info(f"Ошибка при получении данных от клиента {addr}: {e}")
        else:
            decr_data = self.msg_crypter.encrypt_message(encr_data)
            username = decr_data["username"]
            password = decr_data["password"]
            addr = addr[0]
            if self.auth_processing.userreg(addr, username, password):
                server_logger.info(f"Пользователь {username} зарегистрирован (ip: {addr})")
                data = {'username': username, 'result': 'success'}
            else:
                server_logger.info(f"Пользователь c ip: {addr} уже зарегистрирован")
                data = {'username': username, 'result': 'failure'}

            self.send_message(conn, data, addr)
            server_logger.info(f"Отправлены данные о результате регистсрации клиенту {addr}")

    def auth_logic(self, conn, addr):
        encr_data = pickle.loads(conn.recv(1024))
        decr_data = self.msg_crypter.encrypt_message(encr_data)
        username = decr_data["username"]
        password = decr_data["password"]
        auth_result = self.auth_processing.userauth(username, password)
        addr = addr[0]

        if auth_result == 1:
            server_logger.info(f"Пользователь {username} авторизован (ip: {addr})")
            data = {'username': username, 'result': 'success'}
            token, est_time = self.generate_token()
            self.auth_processing.update_info(addr, username, 'active', token, est_time)
            server_logger.info(f"Создан временный токен для клиента {addr}: {token} (время жизни: {est_time})")
            self.sessions_list.append((conn, addr, username, token, est_time))
            self.send_message(conn, data, addr)
            server_logger.info(f"Клиенту {addr} отправлена информация {data} о результате авторизации")
        elif auth_result == 0:
            server_logger.info(f"Пользователь {username} ввел неверный пароль (ip: {addr})")
            data = {'username': username, 'result': "wrong pass"}
            self.send_message(conn, data, addr)
            server_logger.info(f"Клиенту {addr} отправлена информация {data} о результате авторизации")
            self.auth_logic(conn, addr)
        else:
            server_logger.info(f"Пользователь {username} не зарегистрирован (ip: {addr})")
            data = {'username': username, 'result': "not registered"}
            self.send_message(conn, data, addr)
            server_logger.info(f"Клиенту {addr} отправлена информация о результате авторизации")
            self.reg_logic(conn, addr)

    def route(self, conn, addr):
        client_ip = addr[0]
        menu_resp = conn.recv(1024).decode()
        if menu_resp == '1':
            self.auth_logic(conn, addr)
            self.message_logic(conn, client_ip)
        elif menu_resp == '2':
            self.reg_logic(conn, addr)
            self.auth_logic(conn, addr)
            self.message_logic(conn, client_ip)
        else:
            server_logger.info(f"Клиент {client_ip} отключился")
            conn.close()
            exit(0)


def main():
    try:
        port_input = input("Введите номер порта для подключения -> ")
        server_logger.info(f"Проверка порта {port_input}, выбранного пользователем для подключения.")
        validator = PortValidator()
        free_port = validator.port_validation(int(port_input))
        server = Server(free_port)
    except KeyboardInterrupt:
        server_logger.info("Сервер принудительно остановлен ")

        exit(0)


if __name__ == "__main__":
    main()
