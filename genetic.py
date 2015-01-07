#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fx import *

# =============================================================================
from model import Model


def main():
    pass


# =============================================================================

class Tester(object):

    """
    интерфейсный класс для тестирования приспособленности популяции
    """

    def __init__(self):
        pass

    def run(self, population):
        # результат от 0 до 1
        return [0] * len(population)


# =============================================================================

class TesterRandom(Tester):

    """
    непредсказуемые результаты тестирования популяции для doctest'ов
    """

    def __init__(self):
        pass

    def run(self, population):
        return [random.random() for i in xrange(len(population))]


# =============================================================================

class TesterJitter(Tester):
    def __init__(self):

        self.cache = {}
        self.generator = Generator()
        self.player = Player()

    # -------------------------------------------------------------------------

    def run(self, population):

        fn_l = 'l.cap'
        fn_r = 'r.cap'

        results = []
        for m in population:
            if m in self.cache:
                stats = self.cache[m]
            else:
                self.generator.run(m, fn_l, fn_r)
                stats = self.player.run(fn_l, fn_r)
            results.append(stats['jitter'])
        return results


# =============================================================================

class Player(object):
    def __init__(self):
        pass

    # -------------------------------------------------------------------------

    def run(self, fn_l, fn_r):
        return {'jitter': random.random()}


# =============================================================================


class Population(object):

    """
    >>> fflow = FFlow([[0.1, 1], [0.3, 2], [0.5, 3], [1.0, 4]])

    >>> ftp   = FTP([[0.1, 10], [0.2, 20], [0.8, 40], [1.0, 60]])
    >>> flp1  = FLP([[0.1, 110], [0.3, 220], [0.5, 330], [1.0, 440]])
    >>> flp2  = FLP([[0.1, 110], [0.3, 220], [0.7, 330], [1.0, 440]])
    >>> fttl  = FTTL([[0.1, 0], [0.3, 5], [0.5, 15], [1.0, 25]])
    >>> ftf   = FTF([[0.2, 1000], [0.3, 2000], [0.6, 3000], [1.0, 4000]])

    >>> f1    = FlowUDP(9995,   42, 0, 1, ftp, flp1, fttl, ftp, flp2, fttl, ftf)
    >>> f2    = FlowUDP(9999,   40, 0, 2, ftp, flp2, fttl, ftp, flp1, fttl, ftf)
    >>> f3    = FlowTCP(123,   456, 1, 2, ftp, flp1, fttl, ftp, flp2, fttl, ftf)
    >>> f4    = FlowTCP(8899, 9800, 2, 0, ftp, flp2, fttl, ftp, flp1, fttl, ftf)

    >>> flows = [f1, f2, f3, f4]
    >>> nets  = [('a', 'l'), ('b', 'r'), ('a', 'r')]
    >>> nodes = [0, 1, 2, 0]

    >>> o1 = Model(nets, nodes, flows, fflow, 42.0)

    >>> p = Population(TesterRandom(), o1)
    >>> p.mutation()
    >>> p.outbreeding()
    >>> p.inbreeding()
    >>> fitness = [float(i) / len(p.population) for i in xrange(len(p.population))]
    >>> p.selection_exclusion(fitness, 32)
    >>> len(p.population)
    32
    >>> p.run()
    """

    def __init__(self, tester, model):

        """
        создать популяцию на основе организма
        """

        if not isinstance(model, Model):
            raise ValueError

        self.tester = tester

        # вероятность мутации отдельного гена
        self.mutation_prob = 0.1
        # базовая модель
        self.population = [model] * 50
        for org in self.population:
            org.mutation()

    # -------------------------------------------------------------------------

    def mutation(self):
        for m in self.population:
            if random.random() < self.mutation_prob:
                m.mutation()

    # -------------------------------------------------------------------------

    def outbreeding(self):
        children = []
        for m in self.population:
            diffs = map(lambda x: x.diff(m), self.population)
            m2 = self.population[diffs.index(max(diffs))]
            child = m.crossover(m2)
            children.append(child)
        self.population += children

    # -------------------------------------------------------------------------

    def inbreeding(self):

        children = []
        for m in self.population:
            diffs = map(lambda x: x.diff(m), self.population)
            m2 = self.population[diffs.index(min(diffs))]
            child = m.crossover(m2)
            children.append(child)
        self.population += children

    # -------------------------------------------------------------------------

    def selection_exclusion(self, fitness, count):

        old_pop = zip(self.population, fitness)
        old_pop.sort(lambda x, y: x[1] < y[1])

        # добавление лучших различающихся экземпляров
        new_pop = [old_pop[0]]
        i = 1
        while (len(new_pop) < count) and (i < len(old_pop)):
            passed = True
            for mf in new_pop:
                if (mf[0].diff(old_pop[i][0]) < 0.05) and (abs(mf[1] - old_pop[i][1]) < 0.05):
                    passed = False
                    break
            if passed:
                new_pop.append(old_pop[i])
                old_pop.remove(old_pop[i])
            i += 1

        # добавление лучших оставшихся для соответствия требуемому размеру популяции
        need = count - len(new_pop)
        if need > 0:
            new_pop += old_pop[:need]

        self.population = map(lambda x: x[0], new_pop)  # TODO: для оптимизации стоит сохранить результаты тестов!!!

    # -------------------------------------------------------------------------

    def run(self):

        i = 0
        fitness = self.tester.run(self.population)
        while fitness < 2 or i < 50:
            self.mutation()
            self.outbreeding()
            self.inbreeding()
            self.selection_exclusion(fitness, 50)
            fitness = self.tester.run(self.population)
            i += 1
            print self.population
        print self.population


# =============================================================================

if __name__ == '__main__':
    main()
