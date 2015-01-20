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
        self.mutator.set(network_mutator)
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
    """
    В сети может мутировать:
    1) какой либо поток (в т.ч добавиться новый или пропасть старый)
    2) время жизни
    3) количество узлов
    # TODO: список обдумать
    """
    if args["pmut"] <= 0.0:
        return 0
    list_size = len(genome)
    mutations = args["pmut"] * list_size

    if mutations < 1.0:
        mutations = 0
        for it in xrange(list_size):
            if Util.randomFlipCoin(args["pmut"]):
                genome[it] = 1  # TODO rand_init(genome, it)
            mutations += 1

    else:
        for it in xrange(int(round(mutations))):
            which_gene = 1  # TODO rand_randint(0, list_size - 1)
            genome[which_gene] = 1  # TODO rand_init(genome, which_gene)

    return mutations


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
        if not contains(node_dictionary, flows[i].node1, flag):
            node_dictionary.append([flows[i].node1, flag])
        flows[i].node1 = index_of(node_dictionary, flows[i].node1, flag)

        if not contains(node_dictionary, flows[i].node2, flag):
            node_dictionary.append([flows[i].node2, flag])
        flows[i].node2 = index_of(node_dictionary, flows[i].node2, flag)

    net_dictionary = []
    # копируем сетки для узлов
    for i in xrange(len(node_dictionary)):
        flag = node_dictionary[i][1]
        nodes = sister_nodes if flag == 's' else brother_nodes
        nets = sister_nets if flag == 's' else brother_nets
        old_index = nodes[node_dictionary[i][0]]
        net = nets[old_index]
        if contains(net_dictionary, old_index, flag):
            b_nodes.append(index_of(net_dictionary, old_index, flag))
        else:
            net_dictionary.append([old_index, flag])
            b_nets.append(net)
        b_nodes.append(index_of(net_dictionary, old_index, flag))

    return b_nets, b_nodes


def index_of(lst, element, flag):
    for i in xrange(len(lst)):
        if lst[i][0] == element and lst[i][1] == flag:
            return i
    return -1


def contains(lst, element, flag):
    for i in lst:
        if i[0] == element and i[1] == flag:
            return True
    return False


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
    for f in xrange(random.randint(0, 10)):  # TODO
        flows.append(random_flow(random.randint(0, len(nodes) - 1), random.randint(0, len(nodes) - 1)))

    fflow = FFlow().random_initialize()

    texp = random.random() * 100  # TODO
    genome = NetworkGenome(nets, nodes, flows, fflow, texp)

    return genome


def network_random_tester(genome):
    score = 0.0
    score = float(random.random(100))
    return score

