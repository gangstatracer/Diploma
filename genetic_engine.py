#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import uuid

from pyevolve import GenomeBase
from scapy.utils import wrpcap

from flow import Flow, random_flow
from fx import FFlow
from nets_manager import cls_ranges, Translator, directions


class NetworkGenome(GenomeBase.GenomeBase):
    """
    Класс, представляющий собой модель реальной сети, для эволюционирования в pyevolve
    """

    def __init__(self, nets, nodes, flows, fflow, texp):

        GenomeBase.GenomeBase.__init__(self)

        cls_names = cls_ranges.keys()

        for n in nets:
            if (n[0] not in cls_names) or (n[1] not in directions):
                raise ValueError(n)
        net_range = xrange(len(nets))
        for n in nodes:
            if n not in net_range:
                raise ValueError(n)
        node_range = len(nodes)
        for f in flows:
            if not isinstance(f, Flow):
                raise ValueError(str(f))
            if f.node1 >= node_range or f.node2 >= node_range:
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
        self.mutator.add(node_mutator)
        self.mutator.add(texp_mutator)
        self.mutator.add(flow_mutator)
        self.mutator.add(fflow_mutator)

        self.crossover.set(network_crossover)
        self.evaluator.set(network_packets_count_tester)

    def __repr__(self):
        return str(self.texp) + '||' + str(self.fflow) + '||' + str(self.nets) + '||' + str(self.nodes) + '||' + str(
            self.flows)

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
        if not all(n < len(self.nets) for n in self.nodes):
            raise ValueError
        clone = NetworkGenome(self.nets, self.nodes, self.flows, self.fflow, self.texp)
        self.copy(clone)
        return clone


def delete_node(genome, index):
    flows = []
    nodes = genome.nodes
    nets = []

    for f in genome.flows:
        if f.node1 != index and f.node2 != index:
            flows.append(f)

    # при удалении узла надо поменять индексы в потоках
    for f in flows:
        if f.node1 > index:
            f.node1 -= 1
        if f.node2 > index:
            f.node2 -= 1

    del nodes[index]

    # удаляем неиспользуемые сети
    for net_index in xrange(len(genome.nets)):
        if any(node == net_index for node in nodes):
            nets.append(genome.nets[net_index])
    genome.nets = nets

    genome.nodes = nodes
    genome.flows = flows

    return


def network_mutator(genome, **args):
    choice = random.randint(0, len(genome.nets) + 1) if len(genome.nets) != 1 else random.choice(
        xrange(len(genome.nets) + 1))

    if choice < len(genome.nets):
        if random.randint(0, 1):
            genome.nets[choice] = (random.choice(cls_ranges.keys()), genome.nets[choice][1])
        else:
            genome.nets[choice] = (genome.nets[choice][0], 'l' if random.randint(0, 1) else 'r')

    elif choice == len(genome.nets):
        genome.nets.append([random.choice(cls_ranges.keys()), 'l' if random.randint(0, 1) else 'r'])

    else:
        net_to_del = random.choice(xrange(len(genome.nets)))
        del genome.nets[net_to_del]
        # вместе с сетью нужно удалить узлы и потоки
        while any(net_index == net_to_del for net_index in genome.nodes):
            next_index = next(
                node_index for node_index in xrange(len(genome.nodes)) if genome.nodes[node_index] == net_to_del)
            delete_node(genome, next_index)

    return 1


def node_mutator(genome, **args):
    choice = random.randint(0, len(genome.nodes) + 1) if len(genome.nodes) != 1 else random.choice(
        xrange(len(genome.nodes) + 1))

    if choice < len(genome.nodes):
        old_net = genome.nodes[choice]
        while genome.nodes[choice] == old_net:
            genome.nodes[choice] = random.choice(xrange(len(genome.nets)))

    elif choice == len(genome.nodes):
        genome.nodes.append(random.choice(xrange(len(genome.nets))))
    else:
        delete_node(genome, random.choice(xrange(len(genome.nodes))))
    return 1


def get_random_texp():
    return random.random() * 100


def texp_mutator(genome, **args):
    old = genome.texp
    while old == genome.texp:
        genome.texp = get_random_texp()
    return 1


def fflow_mutator(genome, **kwargs):
    genome.fflow.mutation()
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
    s_flows = sister.flows[:cross] + brother.flows[cross:]
    sister.nets, sister.nodes = translate_nodes_and_nets(s_flows, sister.nodes, brother.nodes, sister.nets,
                                                         brother.nets, lambda x: 's' if x < cross else 'b')
    sister.flows = s_flows

    # формируем геном брата
    b_flows = brother.flows[:cross] + sister.flows[cross:]
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

    if not all(isinstance(item, int) for item in b_nodes):
        raise TypeError
    if not all(item < len(b_nets) for item in b_nodes):
        raise ValueError
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
        nodes.append(random.choice(xrange(len(nets))))

    flows = []
    for f in xrange(random.randint(1, 10)):  # TODO
        flows.append(random_flow(random.randint(0, len(nodes) - 1), random.randint(0, len(nodes) - 1)))

    fflow = FFlow().random_initialize()

    texp = get_random_texp()
    genome = NetworkGenome(nets, nodes, flows, fflow, texp)

    return genome


def network_random_tester(genome):
    score = 0.0
    score = float(random.random(100))
    return score


def network_packets_count_tester(genome):
    res = []
    translator = Translator(genome.nets, genome.nodes)
    for f in genome.flows:
        res.extend(f.generate(translator, 0))
    name = """/home/tmp/""" + str(uuid.uuid1())
    f = open(name, 'w')
    f.write(str(genome))
    f.close()
    wrpcap(name + '.cap', res)
    return len(res)

