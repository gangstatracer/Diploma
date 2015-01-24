#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random

from pyevolve import GenomeBase, Util
from flow import Flow, random_flow
from fx import FFlow
from nets_manager import cls_ranges


class NetworkGenome(GenomeBase.GenomeBase):
    """
    Класс, представляющий собой модель реальной сети, для эволюционирования в pyevolve
    """

    def __init__(self, nets, nodes, flows, fflow, texp):

        GenomeBase.GenomeBase.__init__(self)

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

        self.initializator.set(network_initializer)

        # В сети может мутировать:
        # 1) какой либо поток (в т.ч добавиться новый или пропасть старый)
        # 2) время жизни
        # 3) какой либо узел (сменить сеть, добавиться, удалиться)
        # 4) какая-либо сеть (в т.ч. добавиться или удалиться)

        self.mutator.setRandomApply(True)  # произвольным образом выбирается только один из мутаторов
        self.mutator.set(network_mutator)
        self.mutator.set(node_mutator)
        self.mutator.set(texp_mutator)
        self.mutator.set(flow_mutator)

        self.crossover.set(network_crossover)
        self.evaluator.set(network_random_tester)

    # Реализация контракта pyevolve
    def copy(self, g):
        g.nets = self.nets[:]
        g.nodes = self.nodes[:]
        g.flows = map(lambda fl: fl.clone(), self.flows)
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


def network_mutator(genome, **args):
    choice = random.randint(0, len(genome.nets) + 1)

    if choice < len(genome.nets):
        if random.randint(0, 1):
            genome.nets[choice][0] = random.choice(cls_ranges.keys())
        else:
            genome.nets[choice][0] = 'l' if random.randint(0, 1) else 'r'

    elif choice == len(genome.nodes):
        genome.nets.append([random.choice(cls_ranges.keys()), 'l' if random.randint(0, 1) else 'r'])

    else:
        net_to_del = random.randint(0, len(genome.nets) - 1)
        del genome.nets[net_to_del]
        # вместе с сетью нужно удалить узлы и потоки
        deleted_nodes = []
        for n in xrange(len(genome.nodes)):
            if genome.nodes[n] == net_to_del:
                deleted_nodes.append(n)

        for n in deleted_nodes:
            del genome.nodes[n]

        for f in genome.flows:
            if f.node1 in deleted_nodes or f.node2 in deleted_nodes:
                del genome.flows[genome.flows.index(f)]

    return 1


def node_mutator(genome, **args):
    choice = random.randint(0, len(genome.nodes) + 1)

    if choice < len(genome.nodes):
        genome.nodes[choice] = random.choice(genome.nets)

    elif choice == len(genome.nodes):
        genome.nodes.append(random.choice(genome.nets))
    else:
        node_to_del = random.randint(0, len(genome.nodes) - 1)
        # вместе с узлом нужно удалить и все его потоки
        for f in genome.flows:
            if f.node1 == node_to_del or f.node2 == node_to_del:
                del genome.flows[genome.flows.index(f)]
        del genome.nodes[node_to_del]

    return 1


def texp_mutator(genome, **args):
    old = genome.texp
    while old == genome.texp:
        genome.texp = random.random() * 100
    return 1


def flow_mutator(genome, **args):
    choice = random.randint(0, len(genome.flows) + 1)
    if choice < len(genome.flows):
        genome.flows[choice].mutation()
    elif choice == len(genome.flows):
        genome.flows.append(
            random_flow(random.randint(0, len(genome.nodes) - 1), random.randint(0, len(genome.nodes) - 1)))
    else:
        del genome.flows[random.randint(0, len(genome.flows) - 1)]

    return 1


def network_crossover(genome, **args):
    g_mom = args["mom"]
    g_dad = args["dad"]

    sister = g_mom.clone()
    brother = g_dad.clone()
    sister.resetStats()
    brother.resetStats()

    if random.randint(0, 1):
        sister.fflow, brother.fflow = brother.fflow, sister.fflow
    if random.randint(0, 1):
        sister.texp, brother.texp = brother.texp, sister.texp
    # одноточечный кроссовер функций распределения

    cross = random.randint(0, min(len(sister.flows) - 1, len(brother.flows) - 1))

    # формируем геном сестры
    s_flows = sister.flows[:cross] + brother[cross:]
    sister.nets, sister.nodes = translate_nodes_and_nets(s_flows, sister.nodes, brother.nodes, sister.nets,
                                                         brother.nets, lambda x: 's' if x < cross else 'b')
    sister.flows = s_flows

    # формируем геном брата
    b_flows = brother.flows[:cross] + sister[cross:]
    brother.nets, brother.nodes = translate_nodes_and_nets(b_flows, sister.nodes, brother.nodes, sister.nets,
                                                           brother.nets, lambda x: 'b' if x < cross else 's')
    brother.flows = b_flows

    return sister, brother


def translate_nodes_and_nets(flows, sister_nodes, brother_nodes, sister_nets, brother_nets, lambda_flag):
    b_nodes = []
    b_nets = []
    node_dictionary = []

    # транслируем узлы в новые
    for i in xrange(len(flows)):
        flag = lambda_flag(i)
        if [flows[i].node1, flag] not in node_dictionary:
            node_dictionary.append([flows[i].node1, flag])
        flows[i].node1 = node_dictionary.index([flows[i].node1, flag])

        if [flows[i].node2, flag] not in node_dictionary:
            node_dictionary.append([flows[i].node2, flag])
        flows[i].node2 = node_dictionary.index([flows[i].node2, flag])

    net_dictionary = []
    # копируем сетки для узлов
    for i in xrange(len(node_dictionary)):
        flag = node_dictionary[i][1]
        nodes = sister_nodes if flag == 's' else brother_nodes
        nets = sister_nets if flag == 's' else brother_nets
        old_index = nodes[node_dictionary[i][0]]
        net = nets[old_index]
        if [old_index, flag] not in net_dictionary:
            net_dictionary.append([old_index, flag])
            b_nets.append(net)
        b_nodes.append(net_dictionary.index([old_index, flag]))
    return b_nets, b_nodes


def network_initializer(genome, **args):
    """
    Функция создания новой произвольнй сети
    """

    nets = []
    for net in xrange(random.randint(1, 10)):  # TODO
        nets.append([random.choice(cls_ranges.keys()), 'l' if random.randint(0, 1) else 'r'])

    nodes = []
    for node in xrange(random.randint(1, 100)):  # TODO
        nodes.append(random.randint(0, len(nets) - 1))

    flows = []
    for f in xrange(random.randint(1, 10)):  # TODO
        flows.append(random_flow(random.randint(0, len(nodes) - 1), random.randint(0, len(nodes) - 1)))

    fflow = FFlow().random_initialize()

    texp = random.random() * 100  # TODO
    genome = NetworkGenome(nets, nodes, flows, fflow, texp)

    return genome


def network_random_tester(genome):
    score = 0.0
    score = float(random.random(100))
    return score

