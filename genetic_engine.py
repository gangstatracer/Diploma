#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyevolve import GenomeBase
from flow import Flow
from fx import FFlow
from nets_manager import cls_ranges


class NetworkGenome(GenomeBase):
    """
    Класс, представляющий соболь модель реальной сети, для эволюционирования в pyevolve
    """
    def __init__(self, nets, nodes, flows, fflow, texp):
        super(NetworkGenome, self).__init__()

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

        # TODO: реализовать операции над особями
        self.initializator.set(AttackInitializator)
        self.mutator.set(AttackMutator)
        self.crossover.set(AttackCrossover)
        self.evaluator.set(eval_func)

    # Реализация контракта pyevolve
    def copy(self, g):
        g.nets = self.nets[:]
        g.nodes = self.nodes[:]
        g.flows = self.flows[:]
        g.fflow = self.fflow.clone()
        g.texp = self.texp

        # ссылки на ФРВ всех вложенных потоков для ускорения доступа
        g.fxs = []
        for f in g.flows:
            g.fxs += f.fxs
        # полный геном организма
        g.genome = g.fxs + [g.fflow]

    # Реализация контракта pyevolve
    def clone(self):
        clone = NetworkGenome(self.nets, self.nodes, self.flows, self.fflow, self.texp)
        self.copy(clone)
        return clone