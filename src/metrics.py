from typing import List
import statistics
import numpy as np


class MetricsCalculator:
    """
    Класс для расчета различных метрик на основе списка числовых значений.

    Методы:
    - calc_mean: вычисляет среднее арифметическое значение
    - calc_median: вычисляет медиану
    - calc_p05: вычисляет 5й перцентиль
    - calc_min: находит минимальное значение
    """

    def __init__(self, values: List[float]):
        """
        Инициализирует объект MetricsCalculator списком числовых значений.

        Args:
            values (List[float]): Список числовых значений для анализа
        """
        if not values:
            raise ValueError('Список значений не может быть пустым')

        self.values = values

    def calc_mean(self) -> float:
        """
        Вычисляет среднее арифметическое значение.

        Returns:
            float: Среднее арифметическое
        """
        return statistics.mean(self.values)

    def calc_median(self) -> float:
        """
        Вычисляет медиану (50й перцентиль).

        Returns:
            float: Медиана
        """
        return statistics.median(self.values)

    def calc_p05(self) -> float:
        """
        Вычисляет 5й перцентиль.

        Returns:
            float: 5й перцентиль
        """
        return np.percentile(self.values, 5)

    def calc_min(self) -> float:
        """
        Находит минимальное значение.

        Returns:
            float: Минимальное значение
        """
        return min(self.values)