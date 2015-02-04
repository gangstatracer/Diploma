#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

directions = ('l', 'r')

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

        net_counts = {}  # {'z': 0, 'a': 0, 'l': 0, 'b': 0, 'c': 0, 'd': 0, 'e': 0, 'm': 0}
        for k in cls_ranges.keys():
            net_counts[k] = 0
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

            if len(node_counts) <= net:
                raise IndexError(net, node_counts, nodes)
            node_counts[net] += 1
            while node_counts[net] & 0xff in (0xff, 0x00):
                node_counts[net] += 1

            address = self.__int2ip_str(net_addrs[net] + node_counts[net])
            self.node2ip.append(address)
            self.node2pos.append(nets[net][1])
            self.ip2pos[address] = nets[net][1]

    # -------------------------------------------------------------------------

    @staticmethod
    def __int2ip_str(ip_int):
        s = str(ip_int & 0xff)
        for i in xrange(1, 4):
            s = '{0}.{1}'.format(str((ip_int >> i * 8) & 0xff), s)
        return s


# =============================================================================

