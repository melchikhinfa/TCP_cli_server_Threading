import socket
import threading
import json
import uuid
import datetime
from serv_logger import server_logger, change_stream_logs
from auth import UserRegistration
from port_checker import PortValidator
from settings import *


class Server:
    def __init__(self, port):
        server_logger.info("Сервер запускается...")
        self.port = port
        self.sock = None
        self.sessions_list = []
        self.auth_processing = UserRegistration()
        self.socket_init()
        print("Сервер запущен на порту:", port)
        server_logger.info(f"Инициализация сервера. Слушает порт:{port}")

        self.resume_listening()
        self.commands_routing()

        for session in self.sessions_list:
            self.check_token(session)

    def socket_init(self):
        """Инициализация подключения"""
        sock = socket.socket()
        sock.bind(("", self.port))
        sock.listen(0)
        self.sock = sock

    # ПП. 2
    def conn_await(self):
        """Ожидание подключения клиента и создание для него отдельного потока"""
        while self.receive_data:
            conn, addr = self.sock.accept()
            self.sessions_list.append([conn, addr])
            server_logger.info(f"Подключился клиент {addr[0]}")
            thr = threading.Thread(target=self.route, args=(conn, addr), daemon=True)
            thr.start()

    # ПП. 4
    def commands_routing(self):
        """Команды управления сервером"""
        commands = {"exit": {'comm': self.close_server, 'descr': 'Завершение работы сервера'},
                    "pause": {'comm': self.pause_listening, 'descr': 'Приостановка прослушивания порта'},
                    "resume": {'comm': self.resume_listening, 'descr': 'Возобновление прослушивания порта'},
                    "switch logs": {'comm': self.show_or_disable_logs, 'descr': 'Вывод логов сервера в консоль или в файл'},
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
        data_text = data
        if type(data) == dict:
            data = json.dumps(data, ensure_ascii=False)
        data = data.encode('utf-8')
        conn.send(data)
        server_logger.info(f"Сообщение {data_text} было отправлено клиенту {ip}")

    def message_logic(self, conn, ip_addr):
        """Логика обработки сообщений"""
        data = ""
        while True:
            conn_data = conn.recv(4096)
            data = json.loads(conn_data.decode('utf-8'))
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
            if not conn_data:
                self.auth_processing.update_info(ip_addr, username, 'offline', '', '')
                break

    def reg_logic(self, conn, addr):
        data = json.loads(conn.recv(1024).decode('utf-8'))
        username = data["username"]
        password = data["password"]
        addr = addr[0]
        if self.auth_processing.userreg(addr, username, password):
            server_logger.info(f"Пользователь {username} зарегистрирован (ip: {addr})")
            data = {'username': username, 'text': {'result': 'success'}}
        else:
            server_logger.info(f"Пользователь c ip: {addr} уже зарегистрирован")
            data = {'username': username, 'text': {'result': 'failure'}}

        self.send_message(conn, data, addr)
        server_logger.info(f"Отправлены данные о результате регистсрации клиенту {addr}")

    def auth_logic(self, conn, addr):
        data = json.loads(conn.recv(1024).decode('utf-8'))
        username = data["username"]
        password = data["password"]
        auth_result = self.auth_processing.userauth(username, password)
        addr = addr[0]
        if auth_result == 1:
            server_logger.info(f"Пользователь {username} авторизован (ip: {addr})")
            data = {'username': username, 'text': {'result': 'success'}}
            token, est_time = self.generate_token()
            self.auth_processing.update_info(addr, username, 'active', token, est_time)
            server_logger.info(f"Создан временный токен для клиента {addr}: {token} (время жизни: {est_time})")
            self.sessions_list.append((conn, addr, username, token, est_time))
            self.send_message(conn, data, addr)
            server_logger.info(f"Клиенту {addr} отправлена информация {data} о результате авторизации")
        elif auth_result == 0:
            server_logger.info(f"Пользователь {username} ввел неверный пароль (ip: {addr})")
            data = {'username': username, 'text': {'result': "wrong pass"}}
            self.send_message(conn, data, addr)
            server_logger.info(f"Клиенту {addr} отправлена информация {data} о результате авторизации")
            self.auth_logic(conn, addr)
        else:
            server_logger.info(f"Пользователь {username} не зарегистрирован (ip: {addr})")
            data = {'username': username, 'text': {'result': "not registered"}}
            self.send_message(conn, data, addr)
            server_logger.info(f"Клиенту {addr} отправлена информация о результате авторизации")
            self.reg_logic(conn, addr)

    def route(self, conn, addr):
        client_ip = addr[0]
        menu_resp = json.loads(conn.recv(1024).decode('utf-8'))
        if menu_resp == 1:
            self.auth_logic(conn, addr)
            self.message_logic(conn, client_ip)
        elif menu_resp == 2:
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
