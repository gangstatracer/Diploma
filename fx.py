#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random


class FX(object):
    """
    универсальный класс ФРВ
    """

    def __init__(self, v_from=0, v_to=1, v_type=int, points=None):

        """
        инициализация ФРВ со значениями (v) в диапазоне [v_from, v_to]
        c типом значений v_type (int или float) и точками points

        >>> f = FX(1, 10, int, [[0.4, 1], [0.2, 3], [0.7, 5], [1.0, 10]])
        >>> f.points
        [[0.2, 3], [0.4, 1], [0.7, 5], [1.0, 10]]

        v_to всегда >= v_from
        >>> f = FX(0, 0)
        >>> f = FX(1, 0)
        Traceback (most recent call last):
        ...
        ValueError

        расчет диапазонов возможных значений различается для int и float,
        т.к. количество целых единиц от v_to до v_from (для int)
        на 1 больше, чем длина непрерывного промежутка
        между ними (для float), что сказывается
        на расчете нормализованного представления точек ФРВ:
        >>> f = FX(10, 19, int, [[0.2, 19], [0.5, 10], [1.0, 14]])
        >>> f.points_normalized
        [[0.2, 0.9], [0.5, 0.0], [1.0, 0.4]]
        >>> f = FX(10, 19, float, [[0.2, 19], [0.5, 10], [1.0, 14]])
        >>> f.points_normalized
        [[0.2, 1.0], [0.5, 0.0], [1.0, 0.4444444444444444]]
        >>> f = FX(10, 20, float, [[0.2, 19], [0.5, 10], [1.0, 14]])
        >>> f.points_normalized
        [[0.2, 0.9], [0.5, 0.0], [1.0, 0.4]]
        >>> f = FX(10, 20, float, [[0.2, 19], [0.2,18], [0.5, 10], [1.0, 14]])
        >>> f.points_normalized
        [[0.2, 0.9], [0.5, 0.0], [1.0, 0.4]]
        """
        if not points:
            points = []

        if (v_type not in (int, float)) or (v_from > v_to):
            raise ValueError
        # тип значений
        self.v_type = v_type
        # пределы значений
        self.v_from = v_from
        self.v_to = v_to
        self.v_delta = v_to - v_from
        if v_type == int:
            # т.к. количество целых единиц от v_to до v_from (для int)
            # на 1 больше, чем длина непрерывного промежутка
            # между ними (для float)
            self.v_delta += 1
        # точки транспонированной функции распределения вероятности
        # вида (вероятность, значение)
        # трансп., т.к. первой указывается вероятность
        self.points = []
        # нормализованные точки (т.е. все v от 0 до 1,
        # где 0 соотв. v_from, а 1 - v_to
        # self.points_normalized = []
        if len(points) > 0:
            self.load(points)

    # -------------------------------------------------------------------------

    def load(self, points):

        """
        загрузка точек с валидацией
        >>> f = FX(10, 109, int)
        >>> f.load([[0.5, 42], [0.2, 10]])
        >>> f.points
        [[0.2, 10], [1.0, 42]]
        >>> f.points_normalized
        [[0.2, 0.0], [1.0, 0.32]]
        >>> f.load([[0.5, 10], [0.2, 110]])
        Traceback (most recent call last):
        ...
        ValueError
        """

        self.points = []
        seen = set()
        for p in points:
            if not ((0 <= p[0] <= 1) and (self.v_from <= p[1] <= self.v_to)):
                raise ValueError
            if p[0] not in seen and not seen.add(p[0]):
                self.points.append([p[0], self.v_type(p[1])])
        self.points.sort(key=lambda x: x[0])
        # вероятность последней точки всегда = 1
        self.points[-1][0] = 1.0
        # self.__update_points_normalized()

    # -------------------------------------------------------------------------

    def __repr__(self):
        return str.format(
            """
Type: {0}
Value: {1}-{2}
Points: {3}
Normalized points: {4}
        """, self.v_type, self.v_from, self.v_to, self.points, self.points_normalized)

    @property
    def points_normalized(self):
        return map(lambda x: [x[0], float(x[1] - self.v_from) / self.v_delta], self.points)

    # -------------------------------------------------------------------------

    def __mutation_vi(self, i):

        """
        случайная мутация значения (v) i-й точки
        >>> f       = FX(10, 109, int, [[0.2, 42], [0.5, 10], [1.0, 13]])
        >>> changed = False
        >>> v0      = f.points[1][1]
        >>> for i in xrange(1000):
        ... 	f.__mutation_vi(1)
        ... 	if v0 != f.points[1][1]:
        ... 		changed = True
        ... 	if not (f.v_from <= f.points[1][1] <= f.v_to):
        ... 		raise ValueError
        ... 	if float(f.points[1][1] - 10) / 100 != f.points_normalized[1][1]:
        ... 		raise ValueError
        >>> changed
        True
        """

        self.points[i][1] = self.v_type(self.v_from + random.random() * self.v_delta)
        # self.__update_points_normalized()

    # -------------------------------------------------------------------------

    def __mutation_pi(self, i):

        """
        случайная мутация вероятности (p) i-й точки
        >>> f       = FX(10, 109, int, [[0.2, 42], [0.5, 10], [1.0, 13]])
        >>> changed = False
        >>> p0      = f.points[1][0]
        >>> for i in xrange(1000):
        ... 	f.__mutation_pi(1)
        ... 	if p0 != f.points[1][0]:
        ... 		changed = True
        ... 	if not (0.0 <= f.points[1][0] <= 1.0):
        ... 		raise ValueError
        >>> changed
        True
        """

        # вычислить новую вероятность
        new_p = random.random() * 0.99  # должно быть < 1
        # нормализовать остальные
        scale = (1. - self.points[i][0]) / 1. - new_p
        for pnt in self.points:
            pnt[0] /= scale
        self.points[i][0] = new_p
        # вероятность последней точки всегда = 1
        self.points[-1][0] = 1.0
        self.points.sort(key=lambda x: x[0])

    # -------------------------------------------------------------------------

    def mutation_p(self):

        """
        случайная мутация вероятностей (p) точек функции
        """

        self.__mutation_pi(random.randint(0, len(self.points) - 1))

    # -------------------------------------------------------------------------

    def mutation_v(self):

        """
        случайная мутация значений (v) точек функции
        """

        self.__mutation_vi(random.randint(0, len(self.points) - 1))

    # -------------------------------------------------------------------------

    def mutation(self):

        """
        случайная мутация точек функции
        может оказатся измененным как значение, так и вероятность
        """

        # индекс точки
        i = random.randint(0, len(self.points) - 1)
        # c вероятностью 0.5 мутация вероятности или значения
        if random.randint(0, 1):
            self.__mutation_vi(i)
        else:
            self.__mutation_pi(i)

    # -------------------------------------------------------------------------

    def random(self):

        """
        возвращает случайное значение, вычисленное по данной ФРВ
        >>> f = FX(1, 100, int, [[0.2, 42], [1.0, 9]])
        >>> counts = {}
        >>> for i in xrange(10000):
        ... 	r = f.random()
        ... 	if counts.has_key(r):
        ... 		counts[r] += 1
        ... 	else:
        ... 		counts[r] = 1
        >>> len(counts)
        2
        >>> 0.23 < float(counts[42])/counts[9] < 0.27
        True
        """

        r = random.random()
        i = 0
        while r > self.points[i][0]:
            i += 1
        return self.points[i][1]


# =============================================================================

class FTP(FX):
    def __init__(self, points):
        super(FTP, self).__init__(0, 1e6, float, points)


class FLP(FX):
    def __init__(self, points):
        super(FLP, self).__init__(100, 1300, int, points)


class FTTL(FX):
    def __init__(self, points):
        super(FTTL, self).__init__(0, 100, int, points)


class FTF(FX):
    def __init__(self, points):
        super(FTF, self).__init__(0, 1e6, float, points)


class FFlow(FX):
    def __init__(self, points):
        super(FFlow, self).__init__(0, 1e6, int, points)


# =============================================================================
