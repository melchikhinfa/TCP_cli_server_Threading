import multiprocessing
import random


path_to_matrix_a = "data/matrix_a.txt"
path_to_matrix_b = "data/matrix_b.txt"
path_to_res_file = "data/result.txt"


class MultiplyMatrix:
    def __init__(self, path_to_matrix_a, path_to_matrix_b, path_to_res_file):
        self.path_to_matrix_a = path_to_matrix_a
        self.path_to_matrix_b = path_to_matrix_b
        self.path_to_res_file = path_to_res_file

    def read_matrix(self, path_to_matrix):
        """Чтение матрицы из файла"""
        matrix = []
        with open(path_to_matrix, "r") as f:
            for line in f:
                row = [int(x) for x in line.split()]
                matrix.append(row)
        self.print_matrix(matrix, "Исходная матрица: ")
        return matrix

    @staticmethod
    def print_matrix(matrix, msg: str):
        """Вывод матрицы"""
        m = msg + '\n' + '\n'.join(["\t".join([str(x) for x in row]) for row in matrix])
        return m

    def matrix_gen(self, n: int, m: int):
        """Генерация матрицы"""
        matrix = []
        for i in range(n):
            matrix.append([])
            for j in range(m):
                matrix[i].append(random.randint(1, 100))
        return matrix

    def mult_matrix_worker(self, matrix_a, matrix_b, i, j):
        res = 0
        for k in range(len(matrix_b)):
            res += matrix_a[i][k] * matrix_b[k][j]
        print(f'Вычисление элемента {i} {j}: {res}')
        return res

    def multiply_two_matrices(self):
        matrix_a = self.read_matrix(self.path_to_matrix_a)
        matrix_b = self.read_matrix(self.path_to_matrix_b)
        res_file = open(self.path_to_res_file, "a")
        res_matrix = [[0 for _ in range(len(matrix_b[0]))] for _ in range(len(matrix_a))]
        rows = len(matrix_a)
        cols = len(matrix_b[0])
        size = rows * cols
        print("Вычисляется матрица размера " + str(rows) + "x" + str(cols))
        for i in range(rows):
            for j in range(cols):
                with multiprocessing.Pool(processes=4) as pool:
                    res_m = pool.apply_async(self.mult_matrix_worker, args=(matrix_a, matrix_b, i, j))
                    res_matrix[i][j] = res_m.get()
                    res_file.write(str(res_matrix[i][j]) + '\n')
        res = self.print_matrix(res_matrix, "Результат: ")
        res_file.write('\n' + res)
        print(res)
        res_file.close()


def main():
    mult_matrix = MultiplyMatrix(path_to_matrix_a, path_to_matrix_b, path_to_res_file)
    mult_matrix.multiply_two_matrices()


if __name__ == "__main__":
    main()

