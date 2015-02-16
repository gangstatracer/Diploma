#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import struct

masks = xrange(1, 32)
directions = ('l', 'r')

# =============================================================================


class Translator:

    """
    преобразователь индексов узлов в IP-адреса
    >>> nets  = [(8, 'l'), (24, 'r')]
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

        net_counts = {}
        for k in masks:
            net_counts[k] = 0
        net_addrs = []
        node_counts = []

        for i in xrange(len(nets)):
            net_addr = (0 if nets[i][1] == 'l' else 1) << 31
            mask = nets[i][0]
            net_counts[mask] += 1

            node_bytes = 32 - mask
            if net_counts[mask] > 2 ** (mask - 1):
                raise ValueError('Too many nets({0}) to such mask: {1}'.format(net_counts[mask], mask))
            net_addrs.append(net_addr | (net_counts[mask] << node_bytes))
            node_counts.append(0)

        for i in xrange(len(nodes)):
            net = nodes[i]

            node_counts[net] += 1
            if node_counts[net] > 2 ** (32 - nets[net][0]) - 1:
                raise ValueError('Too many hosts for such mask: {0}'.format(nets[net]))
            address = self.int2ip(net_addrs[net] | node_counts[net])
            self.node2ip.append(address)
            self.node2pos.append(nets[net][1])
            self.ip2pos[address] = nets[net][1]

    # -------------------------------------------------------------------------

    @staticmethod
    def int2ip(addr):
        return socket.inet_ntoa(struct.pack("!I", addr))


# =============================================================================

