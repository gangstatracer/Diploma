#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

from scapy.all import *


# =============================================================================

def main():
    pass


# =============================================================================

class FX(object):
    """
    универсальный класс ФРВ
    """

    def __init__(self, v_from=0, v_to=1, v_type=int, points=[]):

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
        """

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
        self.points_normalized = []
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

        # TODO: проверка отсутствия одинаковых p/v в points
        # TODO: сортировка точек по v
        self.points = []
        for p in points:
            if not ((0 <= p[0] <= 1) and (self.v_from <= p[1] <= self.v_to)):
                raise ValueError
            self.points.append([p[0], self.v_type(p[1])])
        self.points.sort(key=lambda x: x[0])
        # вероятность последней точки всегда = 1
        self.points[-1][0] = 1.0
        self.__update_points_normalized()

    # -------------------------------------------------------------------------

    def __update_points_normalized(self):

        """
        обновить нормализованное представления точек ФРВ
        """

        self.points_normalized = map(lambda x: [x[0], float(x[1] - self.v_from) / self.v_delta], self.points)

    # -------------------------------------------------------------------------

    def __mutation_vi(self, i):

        """
        случайная мутация значения (v) i-й точки
        >>> f       = FX(10, 109, int, [[0.2, 42], [0.5, 10], [1.0, 13]])
        >>> changed = False
        >>> v0      = f.points[1][1]
        >>> for i in xrange(1000):
        ... 	f._FX__mutation_vi(1)
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
        self.__update_points_normalized()

    #-------------------------------------------------------------------------

    def __mutation_pi(self, i):
        """
        случайная мутация вероятности (p) i-й точки
        >>> f       = FX(10, 109, int, [[0.2, 42], [0.5, 10], [1.0, 13]])
        >>> changed = False
        >>> p0      = f.points[1][0]
        >>> for i in xrange(1000):
        ... 	f._FX__mutation_pi(1)
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
        self.points_normalized.sort(key=lambda x: x[0])

    #-------------------------------------------------------------------------

    def mutation_p(self):

        """
        случайная мутация вероятностей (p) точек функции
        """

        self.__mutation_pi(random.randint(0, len(self.points) - 1))

    #-------------------------------------------------------------------------

    def mutation_v(self):

        """
        случайная мутация значений (v) точек функции
        """

        self.__mutation_vi(random.randint(0, len(self.points) - 1))

    #-------------------------------------------------------------------------

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

    #-------------------------------------------------------------------------

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
        while (r > self.points[i][0]):
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

        cls_ranges = {
        'z': (0x00000000, 0),  # zero
        'a': (0x01000000, 3),  # a
        'l': (0x7F000000, 3),  # loopback
        'b': (0x80000000, 2),  # b
        'c': (0xc0000000, 1),  # c
        'd': (0xe0000000, 3),  # d
        'e': (0xf0000000, 3),  # e
        'm': (0xffffffff, 0),  # multicast
        }

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

            addr = self.__int2ipstr(net_addrs[net] + node_counts[net])
            self.node2ip.append(addr)
            self.node2pos.append(nets[net][1])
            self.ip2pos[addr] = nets[net][1]

    # -------------------------------------------------------------------------

    def __int2ipstr(self, ipint):

        s = str(ipint & 0xff)
        for i in xrange(1, 4):
            s = str((ipint >> i * 8) & 0xff) + '.' + s
        return s


# =============================================================================

class Flow(object):
    """
    универсальный класс потока, содержащий метод генерации своего трафика
    params = (node1, node2, ftp1, flp1, fttl1, ftp2, flp2, fttl2, ftf)
    >>> ftp  = FTP([[1.0, 0.1]])
    >>> flp  = FLP([[1.0, 100]])
    >>> fttl = FTTL([[1.0, 1]])
    >>> ftf  = FTF([[1.0, 100]])
    >>> f    = Flow(0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf)
    """



    # TODO: ВВЕСТИ FHF - ФРВ ПОЛУПОТОКА (НАПРАВЛЕНИЯ)




    def __init__(self, *params):
        param_types = map(lambda x: type(x), params)
        if param_types != [int, int] + [FTP, FLP, FTTL] * 2 + [FTF]:
            raise ValueError, params

        self.node1 = params[0]
        self.node2 = params[1]

        self.ftp1 = params[2]
        self.flp1 = params[3]
        self.fttl1 = params[4]

        self.ftp2 = params[5]
        self.flp2 = params[6]
        self.fttl2 = params[7]

        self.ftf = params[8]

        # массив ссылок на все ФРВ
        self.fxs = params[2:]

    #-------------------------------------------------------------------------

    def generate(self, translator, t0):
        """
        функция генерации
        translator - транслятор индексов узлов в сетевые адреса
        t0         - время начала потока
        """

        return []


#=============================================================================

class FlowSock(Flow):
    """
    класс потока, поддерживающего сокеты
    params = (port1, port2, node1, node2, ftp1, flp1, fttl1, ftp2, flp2, fttl2, ftf)
    >>> ftp  = FTP([[1.0, 0.1]])
    >>> flp  = FLP([[1.0, 100]])
    >>> fttl = FTTL([[1.0, 1]])
    >>> ftf  = FTF([[1.0, 100]])
    >>> f    = FlowSock(9999, 42, 0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf)
    """


    def __init__(self, *params):
        parent_params = params[2:]
        super(FlowSock, self).__init__(*parent_params)
        if not (type(params[0]) == type(params[1]) == int):
            raise ValueError
        self.port1 = params[0]
        self.port2 = params[1]


#=============================================================================


class FlowTCP(FlowSock):
    """
    класс потока TCP
    params = (port1, port2, node1, node2, ftp1, flp1, fttl1, ftp2, flp2, fttl2, ftf)
    >>> ftp   = FTP([[1.0, 0.1]])
    >>> flp   = FLP([[1.0, 100]])
    >>> fttl  = FTTL([[1.0, 1]])
    >>> ftf   = FTF([[1.0, 100]])
    >>> f     = FlowTCP(9999, 42, 0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf)
    >>> nets  = [('a', 'l'), ('b', 'r')]
    >>> nodes = [0, 1]
    >>> t     = Translator(nets, nodes)
    >>> packs = f.generate(t, 42.0)
    >>> 950 < len(packs) < 1050
    True
    >>> (packs[0][TCP].sport, packs[1][TCP].sport, packs[2][TCP].sport)
    (9999, 42, 9999)
    """

    def __init__(self, *params):

        super(FlowTCP, self).__init__(*params)

    #-------------------------------------------------------------------------

    def generate_l5(self, length):

        l5 = 'A' * length
        return l5

    #-------------------------------------------------------------------------

    def generate(self, translator, t0):

        t1 = t0 + self.ftf.random()

        ip1 = translator.node2ip[self.node1]
        ip2 = translator.node2ip[self.node2]

        l3_1 = IP(src=ip1, dst=ip2)
        l4_1 = TCP(sport=self.port1, dport=self.port2)
        l3_2 = IP(src=ip2, dst=ip1)
        l4_2 = TCP(sport=self.port2, dport=self.port1)

        l34_1 = l3_1 / l4_1
        l34_2 = l3_2 / l4_2
        params1 = {'ftp': self.ftp1, 'flp': self.flp1, 'fttl': self.fttl1}
        params2 = {'ftp': self.ftp2, 'flp': self.flp2, 'fttl': self.fttl2}

        seq_mod = 2 ** 32
        max_seq = 2 ** 32 - 1
        seq1 = random.random() * max_seq
        seq2 = random.random() * max_seq

        packets = []
        t = t0
        state = 'C'

        while state != 'Q':

            # открытие соединения
            if state == 'C':

                l34 = l34_1
                l5 = ''
                flags_on = 2  # 2 - SYN, 4 - RST, 16 - ACK
                flags_off = 1 | 4 | 16
                params = params1
                seq = seq1
                ack = 0
                seq1 += 1  # для пакетов с SYN в процессе инициализации (см. RFC)
                state = 'O1'

            elif state == 'O1':

                l34 = l34_2
                l5 = ''
                flags_on = 2 | 16
                flags_off = 1 | 4
                seq = seq2
                ack = seq1
                params = params2
                seq2 += 1
                state = 'O2'

            elif state == 'O2':

                l34 = l34_1
                l5 = ''
                flags_on = 16
                flags_off = 1 | 2 | 4
                seq = seq1
                ack = seq2
                params = params1
                state = 'E'

            # передача данных
            elif state == 'E':

                flags_on = 16
                flags_off = 1 | 2 | 4
                l5 = self.generate_l5(params['flp'].random())
                if random.random() > 0.5:
                    l34 = l34_1
                    seq = seq1
                    ack = seq2
                    params = params1
                    seq1 += len(l5)
                else:
                    l34 = l34_2
                    seq = seq2
                    ack = seq1
                    params = params2
                    seq2 += len(l5)
                if t >= t1:
                    state = 'F1'

            # завершение
            elif state == 'F1':

                l34 = l34_2
                l5 = self.generate_l5(params['flp'].random())
                flags_on = 1 | 16  # 1 - FIN
                flags_off = 2 | 4
                seq = seq2
                ack = seq1
                params = params2
                seq2 += len(l5)
                state = 'F2'

            elif state == 'F2':
                l34 = l34_1
                l5 = self.generate_l5(params['flp'].random())
                flags_on = 1 | 16
                flags_off = 2 | 4
                seq = seq1
                ack = seq2
                params = params1
                seq1 += len(l5)
                state = 'Q'

            seq1 %= seq_mod  # сохранение в пределах допустимых значений
            seq2 %= seq_mod

            l34[TCP].flags |= flags_on
            l34[TCP].flags &= ~flags_off
            l34[TCP].seq = seq
            l34[TCP].ack = ack
            l34[IP].ttl = params['fttl'].random()

            p = l34 / l5
            p.time = t

            packets.append(p)

            tp = params['ftp'].random()
            t += tp

        return packets


#=============================================================================

class FlowUDP(FlowSock):
    """
    класс потока TCP
    params = (port1, port2, node1, node2, ftp1, flp1, fttl1, ftp2, flp2, fttl2, ftf)
    >>> ftp   = FTP([[1.0, 0.1]])
    >>> flp   = FLP([[1.0, 100]])
    >>> fttl  = FTTL([[1.0, 1]])
    >>> ftf   = FTF([[1.0, 100]])
    >>> f     = FlowUDP(9999, 42, 0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf)
    >>> nets  = [('a', 'l'), ('b', 'r')]
    >>> nodes = [0, 1]
    >>> t     = Translator(nets, nodes)
    >>> packs = f.generate(t, 42.0)
    >>> 950 < len(packs) < 1050
    True
    >>> (packs[0][UDP].sport, packs[0][UDP].dport)
    (9999, 42)
    """

    def __init__(self, *params):

        super(FlowUDP, self).__init__(*params)

    #-------------------------------------------------------------------------

    def generate_l5(self, length):

        l5 = 'A' * length
        return l5

    #-------------------------------------------------------------------------

    def generate(self, translator, t0):

        t1 = t0 + self.ftf.random()

        ip1 = translator.node2ip[self.node1]
        ip2 = translator.node2ip[self.node2]

        l3_1 = IP(src=ip1, dst=ip2)
        l4_1 = UDP(sport=self.port1, dport=self.port2)
        l3_2 = IP(src=ip2, dst=ip1)
        l4_2 = UDP(sport=self.port2, dport=self.port1)

        l34_1 = l3_1 / l4_1
        l34_2 = l3_2 / l4_2
        params1 = {'ftp': self.ftp1, 'flp': self.flp1, 'fttl': self.fttl1}
        params2 = {'ftp': self.ftp2, 'flp': self.flp2, 'fttl': self.fttl2}

        packets = []
        t = t0

        l5 = self.generate_l5(self.flp1.random())
        l34_1[IP].ttl = self.fttl1.random()
        p = l34_1 / l5
        p.time = t
        packets.append(p)
        tp = self.ftp1.random()
        t += tp
        while t < t1:
            if random.random() > 0.5:
                l34 = l34_1
                params = params1
            else:
                l34 = l34_2
                params = params2
            l5 = self.generate_l5(params['flp'].random())
            l34[IP].ttl = params['fttl'].random()
            p = l34 / l5
            p.time = t
            packets.append(p)
            tp = params['ftp'].random()
            t += tp

        return packets


#=============================================================================

class FlowICMP(Flow):
    def __init__(self, *params):
        """
        params = (type1, type2, node1, node2, ftp1, flp1, fttl1, ftp2, flp2, fttl2, ftf):
        """

        parent_params = params[:2]
        super(FlowSock, self).__init__(*parent_params)
        self.type1 = params[0]
        self.type2 = params[1]

    #-------------------------------------------------------------------------

    def generate(self, translator, t0):
        return []

#=============================================================================


cls_ranges = {
'z': (0x00000000, 0),  # zero
'a': (0x01000000, 3),  # a
'l': (0x7F000000, 3),  # loopback
'b': (0x80000000, 2),  # b
'c': (0xc0000000, 1),  # c
'd': (0xe0000000, 3),  # d
'e': (0xf0000000, 3),  # e
'm': (0xffffffff, 0),  # multicast
}

#=============================================================================

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

    #-------------------------------------------------------------------------

    def save(self):
        # TODO: сохранить в файл
        pass

    #-------------------------------------------------------------------------
    # реализация интерфейса model
    #-------------------------------------------------------------------------

    def mutation(self):

        lfx = len(self.fxs)
        # значение = lfx означает мутацию ФРВ потоков (fflow)
        i = random.randint(0, lfx)
        if i < lfx:
            self.fxs[i].mutation()
        else:
            self.fflow.mutation_v()

    #-------------------------------------------------------------------------

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

    #-------------------------------------------------------------------------

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


#=============================================================================

class Tester(object):
    """
    интерфейсный класс для тестирования приспособленности популяции
    """

    def __init__(self):
        pass

    def run(self, population):
        # результат от 0 до 1
        return [0] * len(population)


#=============================================================================

class TesterRandom(Tester):
    """
    непредсказуемые результаты тестирования популяции для doctest'ов
    """

    def __init__(self):
        pass

    def run(self, population):
        return [random.random() for i in xrange(len(population))]


#=============================================================================

class TesterJitter(Tester):
    def __init__(self):

        self.cache = {}
        self.generator = Generator()
        self.player = Player()

    #-------------------------------------------------------------------------

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


#=============================================================================

class Player(object):
    def __init__(self):
        pass

    #-------------------------------------------------------------------------

    def run(self, fn_l, fn_r):
        return {'jitter': random.random()}


#=============================================================================


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
        #if not isinstance(tester, Tester):
        #	raise ValueError

        self.tester = tester

        # вероятность мутации отдельного гена
        self.mutation_prob = 0.1
        # базовая модель
        self.population = [model] * 50
        for org in self.population:
            org.mutation()

    #-------------------------------------------------------------------------

    def mutation(self):
        for m in self.population:
            if random.random() < self.mutation_prob:
                m.mutation()

    #-------------------------------------------------------------------------

    def outbreeding(self):

        children = []
        for m in self.population:
            diffs = map(lambda x: x.diff(m), self.population)
            m2 = self.population[diffs.index(max(diffs))]
            child = m.crossover(m2)
            children.append(child)
        self.population += children

    #-------------------------------------------------------------------------

    def inbreeding(self):

        children = []
        for m in self.population:
            diffs = map(lambda x: x.diff(m), self.population)
            m2 = self.population[diffs.index(min(diffs))]
            child = m.crossover(m2)
            children.append(child)
        self.population += children


    #-------------------------------------------------------------------------

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

    #-------------------------------------------------------------------------

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


#=============================================================================

if __name__ == '__main__':
    main()
