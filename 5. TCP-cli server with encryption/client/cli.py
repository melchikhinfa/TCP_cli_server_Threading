import threading, socket, time, json, sys, os, pickle
from cli_logger import cli_log

crypto_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(crypto_path)
from encryption import MessageEncryption, DHKeyExchange


class Client:
    def __init__(self, ip_addr: str, port: int, encryption) -> None:
        self.host = ip_addr
        self.port = port
        self.sock = None
        self.cr_port = None

        # Подключаем шифрование:
        self.encryption = encryption
        self.secret_key = None
        self.connect()
        self.message_encrypt = MessageEncryption(self.secret_key)

        self.route_menu()
        # Создаем поток на чтение сообщений с сервера
        read_thr = threading.Thread(target=self.read_message, daemon=True)
        read_thr.start()
        write_trh = threading.Thread(target=self.send_message, daemon=True)
        write_trh.start()

    def crypto_connect(self, cr_port: int):
        """Создание зашифрованного подключения по зашифрованному порту и адресу"""
        cr_sock = socket.socket()
        cr_sock.setblocking(True)
        cli_log.info(f"Инициализация защищенного подключения.")
        cr_sock.connect((self.host, cr_port))
        self.sock = cr_sock
        cli_log.info(f"Клиент {self.host} подключен к серверу по зашифрованному порту:{cr_port}")

    def connect(self):
        """Создание подключения по указанному порту и адресу"""
        sock = socket.socket()
        sock.setblocking(True)
        sock.connect((self.host, self.port))
        cli_log.info(f"Подключен к серверу {self.host}:{self.port}")
        self.sock = sock

        cli_pub_keys = self.encryption.auth_keys
        print(cli_pub_keys)
        self.sock.sendall(pickle.dumps(cli_pub_keys))
        cli_log.info(f"Отправлены публичные ключи клиента: {cli_pub_keys}")

        server_pub_key = pickle.loads(self.sock.recv(1024))
        self.secret_key = self.encryption.generate_full_key(int(server_pub_key))
        cli_log.info(f"Произведен обмен ключами. Получен публичный ключ сервера: {server_pub_key}.")

        self.message_encrypt = MessageEncryption(self.secret_key)
        encr_port = pickle.loads(self.sock.recv(1024))
        cr_port = self.message_encrypt.encryptor(encr_port)
        cli_log.info(f"Получен зашифрованный порт: {encr_port}. Расшифрованный порт: {cr_port}")
        self.sock.close()
        cli_log.info(f"Закрыто незашифрованное соединение с сервером.")
        self.crypto_connect(int(cr_port))


    def reg_form(self):
        """Регистрация пользователя в системе"""
        print("Регистрация нового пользователя --->")
        while True:
            username = input("Введите имя пользователя: ")
            password = input("Введите пароль: ")
            password2 = input("Повторите пароль: ")
            if password == password2 and username != "":
                data = {"username": username, "password": password}
                encr_data = self.message_encrypt.encrypt_message(data)
                self.sock.sendall(pickle.dumps(encr_data))
                cli_log.info(f"Отправлен запрос на регистрацию пользователя {username}")
                server_response = self.message_encrypt.encrypt_message(pickle.loads(self.sock.recv(1024)))
                cli_log.info(f"Принимаем ответ от сервера - результат регистрации: {server_response['result']}")
                if server_response['result'] == "success":
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
            encr_data = self.message_encrypt.encrypt_message(data)
            if username != "" and password != "":
                self.sock.sendall(pickle.dumps(encr_data))
                cli_log.info(f"Отправлен запрос на авторизацию пользователя {username}")
                server_response = self.message_encrypt.encrypt_message(pickle.loads(self.sock.recv(1024)))
                cli_log.info(f"Принимаем ответ от сервера - результат авторизации: {server_response['result']}")
                if server_response['result'] == "success":
                    print("Клиент успешно авторизован!")
                    cli_log.info(f"Пользователь {username} авторизован на сервере.")
                    self.send_message(username)
                elif server_response['result'] == "wrong pass":
                    print("Неверный пароль!")
                    cli_log.info(f"Пользователь {username} ввел неверный пароль.")
                    self.auth_form()
                elif server_response['result'] == "not registered":
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
        data_encoded = ''
        data = ''
        time.sleep(10)
        try:
            data_encoded = pickle.loads(self.sock.recv(1024))
            data = self.message_encrypt.encrypt_message(data_encoded)
            username, message = data["username"], data["text"]
            print(f"Сообщение от {username}: {message}")
            cli_log.info(f"Принято зашифрованное сообщение от {username} : *{data_encoded['text']}*")
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
            encr_data = self.message_encrypt.encrypt_message(data)
            data = pickle.dumps(encr_data)
            self.sock.sendall(data)
            cli_log.info(f"Пользователь отправил сообщение: {message}")
            cli_log.info(f"Пользователь отправил сообщение в зашифрованном виде: {encr_data['text']}")
            #self.read_message()
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
    with open('./keys.txt', 'r') as f:
        keys = f.read()
        p, g, a = map(int, keys.split(' '))

    port_input = int(input("Введите порт подключения: "))
    ip_addr_input = input("Введите ip-адрес подключения к серверу: ")

    get_keys = DHKeyExchange(a, p, g)
    client = Client(ip_addr_input, port_input, get_keys)


if __name__ == "__main__":
    main()
