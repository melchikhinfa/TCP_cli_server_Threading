import threading
import socket
from cli_logger import cli_log
import json
import time



class Client:
    def __init__(self, ip_addr: str, port: int) -> None:
        self.host = ip_addr
        self.port = port
        self.sock = None
        # Создаем новое подключение и авторизуемся
        self.connect()
        self.route_menu()
        # Создаем поток на чтение сообщений с сервера
        read_thr = threading.Thread(target=self.read_message, daemon=True)
        read_thr.start()
        write_trh = threading.Thread(target=self.send_message, daemon=True)
        write_trh.start()




    def connect(self):
        """Создание подключения по указанному порту и адресу"""
        sock = socket.socket()
        sock.setblocking(True)
        sock.connect((self.host, self.port))
        cli_log.info(f"Подключен к серверу {self.host}:{self.port}")
        self.sock = sock

    def reg_form(self):
        """Регистрация пользователя в системе"""
        print("Регистрация нового пользователя --->")
        while True:
            username = input("Введите имя пользователя: ")
            password = input("Введите пароль: ")
            password2 = input("Повторите пароль: ")
            if password == password2 and username != "":
                data = {"username": username, "password": password}
                self.sock.sendall(json.dumps(data).encode())
                cli_log.info(f"Отправлен запрос на регистрацию пользователя {username}")
                resp = self.sock.recv(1024).decode()
                server_response = json.loads(resp)
                cli_log.info(f"Принимаем ответ от сервера - результат регистрации: {server_response}")
                if server_response['text']['result'] == "success":
                    print("Клиент успешно зарегистрирован! Теперь можете авторизоваться --->")
                    self.auth_form()
                    cli_log.info(f"Пользователь {username} зарегистрирован на сервере.")
                    break
                elif not server_response:
                    cli_log.info("Сервер не отвечает. Попробуйте позже.")
                    self.connect()
                    self.reg_form()
                    break
                else:
                    print("Пользователь с таким именем уже существует")
                    cli_log.info(f"Пользователь с таким именем уже существует")
                    self.reg_form()
                    continue

    def auth_form(self):
        """Авторизация пользователя в системе"""
        print("Авторизуйтесь в системе используя логин и пароль --->")
        while True:
            username = input("Введите имя пользователя: ")
            password = input("Введите пароль: ")
            data = {"username": username, "password": password}
            if username != "" and password != "":
                self.sock.sendall(json.dumps(data).encode('utf-8'))
                cli_log.info(f"Отправлен запрос на авторизацию пользователя {username}")
                server_response = json.loads(self.sock.recv(1024).decode('utf-8'))
                cli_log.info(f"Принимаем ответ от сервера - результат авторизации: {server_response}")
                if server_response['text']['result'] == "success":
                    print("Клиент успешно авторизован")
                    cli_log.info(f"Пользователь {username} авторизован на сервере.")
                    self.send_message(username)
                elif server_response['text']['result'] == "wrong pass":
                    print("Неверный пароль!")
                    cli_log.info(f"Пользователь {username} ввел неверный пароль.")
                    self.auth_form()
                elif server_response['text']['result'] == "not registered":
                    print("Пользователь не зарегистрирован. Пожалуйста, зарегистрируйтесь.")
                    cli_log.info(f"Пользователь {username} не зарегистрирован на сервере.")
                    self.reg_form()

                elif not server_response:
                    cli_log.info("Сервер не отвечает. Попробуйте позже.")
                    self.connect()

                else:
                    cli_log.info(f"Получен неожидаенный ответ от сервера: {server_response}")
                    break
            else:
                print("Поля ввода не должны быть пустыми!")

    def read_message(self):
        """Чтение сообщений с сервера"""
        try:
            data = json.loads(self.sock.recv(1024).decode('utf-8'))
            username, message = data["username"], data["text"]
            print(f"Сообщение от {username}: {message}")
            cli_log.info(f"Принято сообщение от {username} : *{message}*")
        except IOError:
            cli_log.info("Сервер не отвечает. Попробуйте позже.")

    def send_message(self, username):
        while True:
            message = input("Введите сообщение ---> ")
            if message == "exit":
                self.sock.close()
                cli_log.info("Пользователь вышел из чата.")
                break

            data = {'username': username, 'text': message}
            data = json.dumps(data)
            self.sock.sendall(data.encode('utf-8'))
            cli_log.info(f"Пользователь отправил сообщение: {message}")
            self.read_message()
            data = ''

    def route_menu(self):
        """Меню выбора действия"""
        while True:
            print("Выберите действие:")
            print("1. Авторизация")
            print("2. Регистрация")
            print("3. Выход")
            choice = input("Введите номер действия: ")
            if choice == "1":
                self.sock.sendall(choice.encode('utf-8'))
                self.auth_form()
            elif choice == "2":
                self.sock.sendall(choice.encode('utf-8'))
                self.reg_form()
                self.auth_form()
            elif choice == "3":
                self.sock.close()
                break
            else:
                print("Неверный ввод")
                continue


def main():
    port_input = int(input("Введите порт подключения: "))
    ip_addr_input = input("Введите ip-адрес подключения к серверу: ")
    client = Client(ip_addr_input, port_input)


if __name__ == "__main__":
    main()
