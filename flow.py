#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fx import *
from scapy.all import *
from scapy.layers.inet import TCP, IP, UDP, ICMP


class Flow(object):
    """
    универсальный класс потока, содержащий метод генерации своего трафика
    params = (node1, node2, ftp1, flp1, fttl1, ftp2, flp2, fttl2, ftf)
    >>> ftp  = FTP([[1.0, 0.1]])
    >>> flp  = FLP([[1.0, 100]])
    >>> fttl = FTTL([[1.0, 1]])
    >>> ftf  = FTF([[1.0, 100]])
    >>> fhf = FHF([0.5,1])
    >>> f    = Flow(0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf,fhf)
    """

    def __init__(self, *params):
        param_types = map(lambda x: type(x), params)
        if param_types != [int, int] + [FTP, FLP, FTTL] * 2 + [FTF, FHF]:
            raise ValueError(params)

        self.node1 = params[0]
        self.node2 = params[1]

        self.ftp1 = params[2]
        self.flp1 = params[3]
        self.fttl1 = params[4]

        self.ftp2 = params[5]
        self.flp2 = params[6]
        self.fttl2 = params[7]

        self.ftf = params[8]
        self.fhf = params[9]

        # массив ссылок на все ФРВ
        self.fxs = params[2:]

    # -------------------------------------------------------------------------

    def generate(self, translator, t0):
        """
        функция генерации
        translator - транслятор индексов узлов в сетевые адреса
        t0         - время начала потока
        """

        return []

    @staticmethod
    def generate_l5(length):
        l5 = 'A' * length
        return l5

    def copy(self, g):
        if not isinstance(g, Flow):
            raise ValueError("Expected flow, got: {0}", type(g))

        g.node1 = self.node1
        g.node2 = self.node2

        g.ftp1 = self.ftp1.clone()
        g.flp1 = self.flp1.clone()
        g.fttl1 = self.fttl1.clone()

        g.ftp2 = self.ftp2.clone()
        g.flp2 = self.flp2.clone()
        g.fttl2 = self.fttl2.clone()

        g.ftf = self.ftf.clone()
        g.fhf = self.fhf.clone()

        # массив ссылок на все ФРВ
        g.fxs = [g.ftp1, g.flp1, g.fttl1, g.ftp2, g.flp2, g.fttl2, g.ftf, g.fhf]

    def clone(self):
        clone = Flow(self.node1, self.node2, self.ftp1, self.flp1, self.fttl1, self.ftp2, self.flp2, self.fttl2,
                     self.ftf, self.fhf)
        self.copy(clone)
        return clone


# =============================================================================


class FlowSock(Flow):
    """
    класс потока, поддерживающего сокеты
    params = (port1, port2, node1, node2, ftp1, flp1, fttl1, ftp2, flp2, fttl2, ftf)
    >>> ftp  = FTP([[1.0, 0.1]])
    >>> flp  = FLP([[1.0, 100]])
    >>> fttl = FTTL([[1.0, 1]])
    >>> ftf  = FTF([[1.0, 100]])
    >>> f    = FlowSock(9999, 42, 0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf,fhf)
    """

    def __init__(self, *params):
        parent_params = params[2:]
        super(FlowSock, self).__init__(*parent_params)
        if not (type(params[0]) == type(params[1]) == int):
            raise ValueError
        self.port1 = params[0]
        self.port2 = params[1]

    def copy(self, g):
        if not isinstance(g, FlowSock):
            raise ValueError("Expected FlowSock, got: {0}".format(type(g)))
        super(FlowSock, self).copy(g)

        g.port1 = self.port1
        g.port2 = self.port2
        return

    def clone(self):
        clone = type(self)(self.port1, self.port2, self.node1, self.node2, self.ftp1, self.flp1, self.fttl1, self.ftp2,
                           self.flp2, self.fttl2, self.ftf, self.fhf)
        self.copy(clone)
        return clone

    def mutation(self):
        mutation_index = random.randint(0, len(self.fxs) + 1)
        if mutation_index == len(self.fxs):  # мутирует порт1
            self.port1 = random.randint(0, 2 ** 16 - 1)
        if mutation_index > len(self.fxs):  # мутирует порт2
            self.port2 = random.randint(0, 2 ** 16 - 1)
        else:
            self.fxs[mutation_index].mutation()


# =============================================================================


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

    # -------------------------------------------------------------------------

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


# =============================================================================

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

    # -------------------------------------------------------------------------

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

        while t < t1:
            if not self.fhf.random():
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


# =============================================================================

class FlowICMP(Flow):
    def __init__(self, *params):
        """
        params = (type1, type2, node1, node2, ftp1, flp1, fttl1, ftp2, flp2, fttl2, ftf,fhf):
        """

        parent_params = params[2:]
        super(FlowICMP, self).__init__(*parent_params)

        if not isinstance(params[0], int) or not isinstance(params[1], int):
            raise TypeError
        if not (0 <= params[0] <= 40) or not (0 <= params[1] <= 40):
            raise ValueError

        self.type1 = params[0]
        self.type2 = params[1]

    # -------------------------------------------------------------------------

    def mutation(self):
        mutation_index = random.randint(0, len(self.fxs) + 1)
        if mutation_index == len(self.fxs):  # мутирует тип1
            self.type1 = random.randint(0, 40)
        if mutation_index > len(self.fxs):  # мутирует тип2
            self.type2 = random.randint(0, 40)
        else:
            self.fxs[mutation_index].mutation()

    def copy(self, g):
        if not isinstance(g, FlowICMP):
            raise TypeError("Expected FlowSock, got: {0}".format(type(g)))
        super(FlowICMP, self).copy(g)

        g.type1 = self.type1
        g.type2 = self.type2
        return

    def clone(self):
        clone = FlowICMP(self.type1, self.type2, self.node1, self.node2, self.ftp1, self.flp1, self.fttl1, self.ftp2,
                         self.flp2, self.fttl2, self.ftf, self.fhf)
        self.copy(clone)
        return clone

    def generate(self, translator, t0):

        ip1 = translator.node2ip[self.node1]
        ip2 = translator.node2ip[self.node2]

        l3_1 = IP(src=ip1, dst=ip2)
        l4_1 = ICMP(type=self.type1)
        l3_2 = IP(src=ip2, dst=ip1)
        l4_2 = ICMP(type=self.type2)

        l34_1 = l3_1 / l4_1
        l34_2 = l3_2 / l4_2

        params1 = {'ftp': self.ftp1, 'flp': self.flp1, 'fttl': self.fttl1}
        params2 = {'ftp': self.ftp2, 'flp': self.flp2, 'fttl': self.fttl2}

        seq = 0
        ack = 0

        packets = []
        t1 = t0 + self.ftf.random()
        t = t0
        while t < t1:
            if not self.fhf.random():
                l34 = l34_1
                params = params1
                l34['ICMP'].seq = seq
                ack = seq
                seq += 1
            else:
                l34 = l34_2
                params = params2
                l34['ICMP'].ack = ack

            tp = params['ftp'].random()

            l5 = self.generate_l5(params['flp'].random())
            l34['IP'].time = t
            l34['IP'].ttl = params['fttl'].random()
            p = l34 / l5
            packets.append(p)

            t += tp

        return packets

# =============================================================================

