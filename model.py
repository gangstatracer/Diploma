#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flow import *
from nets_manager import cls_ranges


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
                raise ValueError
            if not ({f.node1, f.node2} < node_range):
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
        self.genome[i].mutation()

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
