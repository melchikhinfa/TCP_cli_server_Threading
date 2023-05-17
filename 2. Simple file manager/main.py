from file_manager import FileManager
from settings import WORKING_DIR
import os


def main():
    # Экземпляр обработчика файлов
    file_processing = FileManager()
    try:
        os.mkdir(WORKING_DIR)
    except FileExistsError:
        pass
    os.chdir(WORKING_DIR)
    print(
        "Создана рабочая директория:" + str(WORKING_DIR) +
        "\nВы можете изменить рабочую директорию в файле settings.py"
    )

    while True:
        try:
            command = input("\nВведите команду -> ").split(" ")
            # Остановка работы программы
            if command[0] == "exit":
                break
            # Получаем комманду
            result = file_processing.router(command[0])
            if result:
                try:
                    result(*command[1:])
                except TypeError:
                    print(f"Команда {command[0]} была вызвана с некорректными аргументами")

            else:
                print(f"Команда {command[0]} не найдена! \nВведите команду manual для вывода справки по командам.")
        except KeyboardInterrupt:
            print("Произведен выход из программы.")
    print("Произведен выход из программы.")


if __name__ == "__main__":
    main()
