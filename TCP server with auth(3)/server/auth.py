import sqlite3 as sl
import hashlib
import db_logger


class UserRegistration:
    def __init__(self):
        """Инициализация первичного подключения к базе данных
                и проверки наличия таблицы users"""
        self.conn = sl.connect("./data/users.db", check_same_thread=False, timeout=10)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS users("
            "id INTEGER PRIMARY KEY, "
            "ip, "
            "name, "
            "password NOT NULL, "
            "status, "
            "token, "
            "token_time"
            ")"
        )
        self.conn.commit()
        db_logger.db_log.info("Подключение к базе данных установлено.")
        self.conn.close()
        db_logger.db_log.info("Соединение с базой данных закрыто")

    def userreg(self, ip, name, password):
        """Регистрация пользователя в базе данных"""
        with sl.connect("./data/users.db", check_same_thread=False) as conn:
            db_logger.db_log.info("Подключение к базе данных установлено.")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
            db_logger.db_log.info(f"Проверка наличия пользователя {name} в базе данных")
            hashed_password = hashlib.md5(password.encode()).hexdigest()
            if cursor.fetchone():
                return False
            else:
                cursor.execute("INSERT INTO users (ip, name, password, status, token, token_time) VALUES (?, ?, ?, ?, ?, ?)", (ip, name, hashed_password, "registered", "", ""))
                db_logger.db_log.info(f"Внесены данные пользователя {name} (ip: {ip}) в базу данных")
                conn.commit()
                return True

    def userauth(self, name, password):
        """Авторизация пользователя в базе данных"""
        with sl.connect("./data/users.db", check_same_thread=False, timeout=10) as conn:
            db_logger.db_log.info("Подключение к базе данных установлено.")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
            db_logger.db_log.info(f"Проверка наличия пользователя {name} в базе данных")
            try:
                db_passwd = cursor.fetchone()[3]
                hashed_user_pass = hashlib.md5(password.encode()).hexdigest()
                db_logger.db_log.info("Соединение с базой данных закрыто")
                if db_passwd == hashed_user_pass:
                    return 1
                elif db_passwd != hashed_user_pass:
                    return 0
                else:
                    return -1
            except TypeError: # Если пользователь не найден
                db_logger.db_log.info("Соединение с базой данных закрыто")
                return -1

    def update_info(self, ip, name, status, token, token_time):
        """Внесение изменений информации пользователя в бд"""
        with sl.connect("./data/users.db", check_same_thread=False, timeout=10) as conn:
            db_logger.db_log.info("Подключение к базе данных установлено.")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET status = ?, token=?, token_time=? WHERE ip = ? AND name = ?", (status, token, token_time, ip, name))
            db_logger.db_log.info(f"Обновлена информация о пользователе с именем: {ip}")
            conn.commit()
            db_logger.db_log.info("Соединение с базой данных закрыто")




