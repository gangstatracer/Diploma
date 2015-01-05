#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flow import Flow, cls_ranges

from fx import *

# =============================================================================


def main():
    pass


# =============================================================================


class Translator:

    """
    преобразователь индексов узлов в IP-адреса
    >>> nets  = [('a', 'l'), ('b', 'r')]
    >>> nodes = [0, 1]
    >>> t     = Translator(nets, nodes)
    >>> len(t.node2ip[0].split('.'))
    4
    >>> t.node2pos[1]
    'r'
    >>> t.ip2pos[t.node2ip[0]]
    'l'
    """

    def __init__(self, nets, nodes):

        self.node2ip = []
        self.node2pos = []
        self.ip2pos = {}

        # cls_ranges = {
        #     'z': (0x00000000, 0),  # zero
        #     'a': (0x01000000, 3),  # a
        #     'l': (0x7F000000, 3),  # loopback
        #     'b': (0x80000000, 2),  # b
        #     'c': (0xc0000000, 1),  # c
        #     'd': (0xe0000000, 3),  # d
        #     'e': (0xf0000000, 3),  # e
        #     'm': (0xffffffff, 0),  # multicast
        # }

        net_counts = {'z': 0, 'a': 0, 'l': 0, 'b': 0, 'c': 0, 'd': 0, 'e': 0, 'm': 0}
        net_addrs = []
        node_counts = []

        for i in xrange(len(nets)):
            cls = nets[i][0]
            addr_start = cls_ranges[cls][0]
            node_bytes = cls_ranges[cls][1]
            net_addrs.append(addr_start + (net_counts[cls] << 8 * node_bytes))
            node_counts.append(0)
            net_counts[cls] += 1

        for i in xrange(len(nodes)):
            net = nodes[i]

            node_counts[net] += 1
            while node_counts[net] & 0xff in (0xff, 0x00):
                node_counts[net] += 1

            address = self.__int2ipstr(net_addrs[net] + node_counts[net])
            self.node2ip.append(address)
            self.node2pos.append(nets[net][1])
            self.ip2pos[address] = nets[net][1]

    # -------------------------------------------------------------------------

    def __int2ipstr(self, ipint):

        s = str(ipint & 0xff)
        for i in xrange(1, 4):
            s = '{0}.{1}'.format(str((ipint >> i * 8) & 0xff), s)
        return s


# =============================================================================


class Model:

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
    >>> o2 = Model(nets, nodes, flows, fflow, 42.0)

    >>> o1.diff(o2)
    0.0
    >>> o1.mutation()
    >>> o3 = o1.crossover(o2)
    """

    def __init__(self, nets, nodes, flows, fflow, texp):

        cls_names = cls_ranges.keys()
        dirs = ('l', 'r')
        for n in nets:
            if (n[0] not in cls_names) or (n[1] not in dirs):
                raise ValueError
        net_range = xrange(len(nets))
        for n in nodes:
            if n not in net_range:
                raise ValueError
        node_range = set(xrange(len(nodes)))
        for f in flows:
            if not isinstance(f, Flow):
                ValueError
            if not (set([f.node1, f.node2]) < node_range):
                raise ValueError
        if (type(fflow) != FFlow) or (type(texp) != float):
            raise ValueError

        self.nets = nets
        self.nodes = nodes
        self.flows = flows
        self.fflow = fflow
        self.texp = texp

        # ссылки на ФРВ всех вложенных потоков для ускорения доступа
        self.fxs = []
        for f in flows:
            self.fxs += f.fxs
        # полный геном организма
        self.genome = self.fxs + [self.fflow]

    # -------------------------------------------------------------------------

    def save(self):
        # TODO: сохранить в файл
        pass

    # -------------------------------------------------------------------------
    # реализация интерфейса model
    # -------------------------------------------------------------------------

    def mutation(self):

        lfx = len(self.fxs)
        # значение = lfx означает мутацию ФРВ потоков (fflow)
        i = random.randint(0, lfx)
        if i < lfx:
            self.fxs[i].mutation()
        else:
            self.fflow.mutation_v()

    # -------------------------------------------------------------------------

    def diff(self, other):

        """
        вычисление коэффициента различия между двумя особями;
        является среднеквадратичным значением всех вероятностей
        и нормированных значений точек всех хромосом
        """

        # TODO: не проверяется равенство длин хромосом и количества точек в генах

        res = 0.0
        points_cnt = 0
        for sf, of in zip(self.genome, other.genome):
            for sp, op in zip(sf.points_normalized, of.points_normalized):
                for i in xrange(2):
                    res += (sp[i] - op[i]) ** 2
                points_cnt += 2
        res = (res / points_cnt) ** 0.5
        return res

    # -------------------------------------------------------------------------

    def crossover(self, other):

        """
        одноточечный кроссовер; возможные точки кроссовера - на границе потоков
        fflow и совокупность fxs в потоках - фактически две хромосомы
        """

        # TODO: потенциальная проблема копирования ссылок вместо создания новых объектов

        new_fflow = self.fflow if random.randint(0, 1) else other.fflow
        new_texp = self.texp if random.randint(0, 1) else other.texp
        first, second = (self, other) if random.randint(0, 1) else (other, self)
        cross = random.randint(0, len(self.flows) - 1)
        new_flows = first.flows[:cross] + second.flows[cross:]
        return Model(self.nets, self.nodes, new_flows, new_fflow, new_texp)


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
