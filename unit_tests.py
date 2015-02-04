#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase

from scapy.all import *
from scapy.layers.inet import IP, UDP, TCP, ICMP

from flow import FlowUDP, FlowTCP, FlowICMP, FlowSock
from fx import *
from genetic_engine import NetworkGenome, network_initializer, translate_nodes_and_nets, delete_node, network_mutator
from nets_manager import Translator


class TestFX(TestCase):
    def test_random(self):
        f = FX(1, 100, int, [[0.2, 42], [1.0, 9]])
        counts = {}
        for i in xrange(10000):
            r = f.random()
            if r in counts.keys():
                counts[r] += 1
            else:
                counts[r] = 1
        assert len(counts) == 2
        assert 0.23 < float(counts[42]) / counts[9] < 0.27

    def test_mutation(self):
        f = FX(1, 100, int, [[0.2, 42], [1.0, 9]])
        old_points = []
        for p in f.points:
            old_points.append(p[:])
        f.mutation()
        success = False
        if len(f.points) != len(old_points):
            success = True
        else:
            for i in xrange(len(f.points)):
                if (f.points[i][0] != old_points[i][0]) or (f.points[i][1] != old_points[i][1]):
                    success = True
                if not (0.0 <= f.points[i][0] <= 1.0):
                    raise ValueError("Некорректное изменение вероятности")
                if not (f.v_from <= f.points[i][1] <= f.v_to):
                    raise ValueError("Некорректное изменение значения вероятности")
                if f.points[-1][0] != 1.0:
                    raise ValueError("Последняя точка всегда 1.0")
        assert success

    def test_copy(self):
        ftp = FTP([[0, 20]])
        ftp2 = FTP([[1, 3]])
        ftp.copy(ftp2)
        assert ftp2.points[0][1] == 20
        ftp2.points[0][1] = 3

        assert ftp.points[0][1] == 20
        assert ftp.v_delta == ftp2.v_delta

    def test_clone(self):
        ftp = FTP([[0, 20]])
        ftp2 = ftp.clone()
        assert isinstance(ftp2, FTP)


class TestTranslator(TestCase):
    def test_ip_generate(self):
        nets = [('a', 'l'), ('b', 'r')]
        nodes = [0, 1]
        t = Translator(nets, nodes)
        assert len(t.node2ip[0].split('.')) == 4
        assert t.node2pos[1] == 'r'
        assert t.ip2pos[t.node2ip[0]] == 'l'
        pat = re.compile("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}")
        assert pat.match(t.node2ip[1])


class TestFlowSock(TestCase):
    def test_copy(self):
        ftp = FTP([[1.0, 0.1]])
        flp = FLP([[1.0, 100]])
        fttl = FTTL([[1.0, 1]])
        ftf = FTF([[1.0, 100]])
        fhf = FHF([[0.5, 1]])
        f = FlowSock(9999, 42, 0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf, fhf)
        g = FlowSock(19, 20, 2, 3, ftp, flp, fttl, ftp, flp, fttl, ftf, fhf)
        f.copy(g)
        assert g.port1 == 9999
        g.fhf.points = []
        assert len(f.fhf.points) > 0

    def test_clone(self):
        ftp = FTP([[1.0, 0.1]])
        flp = FLP([[1.0, 100]])
        fttl = FTTL([[1.0, 1]])
        ftf = FTF([[1.0, 100]])
        fhf = FHF([[0.5, 1]])
        f = FlowSock(9999, 42, 0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf, fhf)
        g = f.clone()
        f.port1 = 12
        assert g.port1 == 9999
        g.fhf.points = []
        assert len(f.fhf.points) > 0


class TestFlowUdp(TestCase):
    def test_generate(self):
        ftp = FTP([[1.0, 0.1]])
        flp = FLP([[1.0, 100]])
        fttl = FTTL([[1.0, 1]])
        ftf = FTF([[1.0, 100]])
        fhf = FHF([[0.5, 1]])
        f = FlowUDP(9999, 42, 0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf, fhf)

        nets = [('a', 'l'), ('b', 'r')]
        nodes = [0, 1]
        t = Translator(nets, nodes)

        packs = f.generate(translator=t, t0=0)
        assert len(packs) > 0
        for p in packs:
            assert isinstance(p, IP)
            assert isinstance(p.payload, UDP)


class TestFlowTCP(TestCase):
    def test_generate(self):
        ftp = FTP([[1.0, 0.1]])
        flp = FLP([[1.0, 100]])
        fttl = FTTL([[1.0, 1]])
        ftf = FTF([[1.0, 100]])
        fhf = FHF([[0.5, 1]])
        f = FlowTCP(9999, 42, 0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf, fhf)

        nets = [('a', 'l'), ('b', 'r')]
        nodes = [0, 1]
        t = Translator(nets, nodes)

        packs = f.generate(translator=t, t0=0)
        assert len(packs) > 0
        for p in packs:
            assert isinstance(p, IP)
            assert isinstance(p.payload, TCP)


class TestFlowICMP(TestCase):
    def test_generate(self):
        ftp = FTP([[1.0, 0.1]])
        flp = FLP([[1.0, 100]])
        fttl = FTTL([[1.0, 1]])
        ftf = FTF([[1.0, 100]])
        fhf = FHF([[0.5, 1]])
        f = FlowICMP(0, 8, 0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf, fhf)

        nets = [('a', 'l'), ('b', 'r')]
        nodes = [0, 1]
        t = Translator(nets, nodes)

        packs = f.generate(translator=t, t0=0)
        assert len(packs) > 0
        for p in packs:
            assert isinstance(p, IP)
            assert isinstance(p.payload, ICMP)

    def test_clone(self):
        ftp = FTP([[1.0, 0.1]])
        flp = FLP([[1.0, 100]])
        fttl = FTTL([[1.0, 1]])
        ftf = FTF([[1.0, 100]])
        fhf = FHF([[0.5, 1]])
        f = FlowICMP(0, 1, 0, 1, ftp, flp, fttl, ftp, flp, fttl, ftf, fhf)
        g = f.clone()
        f.type1 = 12
        assert g.type1 == 0
        g.fhf.points = []
        assert len(f.fhf.points) > 0


class TestNetworkGenome(TestCase):
    def test_clone(self):
        fflow = FFlow([[0.1, 1], [0.3, 2], [0.5, 3], [1.0, 4]])

        ftp = FTP([[0.1, 10], [0.2, 20], [0.8, 40], [1.0, 60]])
        flp1 = FLP([[0.1, 110], [0.3, 220], [0.5, 330], [1.0, 440]])
        flp2 = FLP([[0.1, 110], [0.3, 220], [0.7, 330], [1.0, 440]])
        fttl = FTTL([[0.1, 0], [0.3, 5], [0.5, 15], [1.0, 25]])
        ftf = FTF([[0.2, 1000], [0.3, 2000], [0.6, 3000], [1.0, 4000]])
        fhf = FHF([[0.5, 1]])

        f1 = FlowUDP(9995, 42, 0, 1, ftp, flp1, fttl, ftp, flp2, fttl, ftf, fhf)
        f2 = FlowUDP(9999, 40, 0, 2, ftp, flp2, fttl, ftp, flp1, fttl, ftf, fhf)
        f3 = FlowTCP(123, 456, 1, 2, ftp, flp1, fttl, ftp, flp2, fttl, ftf, fhf)
        f4 = FlowTCP(8899, 9800, 2, 0, ftp, flp2, fttl, ftp, flp1, fttl, ftf, fhf)

        flows = [f1, f2, f3, f4]
        nets = [('a', 'l'), ('b', 'r'), ('a', 'r')]
        nodes = [0, 1, 2, 0]

        o1 = NetworkGenome(nets, nodes, flows, fflow, 42.0)
        o2 = o1.clone()

        assert len(o2.nets) == 3
        o2.nets[1] = ('b', 'l')
        assert o1.nets[1][1] == 'r'

    def test_network_initializer(self):
        net = network_initializer(None)
        assert isinstance(net, NetworkGenome)

    def test_translate_nodes_and_nets(self):

        ftp = FTP([[0.1, 10], [0.2, 20], [0.8, 40], [1.0, 60]])
        flp1 = FLP([[0.1, 110], [0.3, 220], [0.5, 330], [1.0, 440]])
        flp2 = FLP([[0.1, 110], [0.3, 220], [0.7, 330], [1.0, 440]])
        fttl = FTTL([[0.1, 0], [0.3, 5], [0.5, 15], [1.0, 25]])
        ftf = FTF([[0.2, 1000], [0.3, 2000], [0.6, 3000], [1.0, 4000]])
        fhf = FHF([[0.5, 1]])
        f1 = FlowUDP(9995, 42, 0, 1, ftp, flp1, fttl, ftp, flp2, fttl, ftf, fhf)
        f2 = FlowUDP(9999, 40, 1, 0, ftp, flp2, fttl, ftp, flp1, fttl, ftf, fhf)
        f3 = FlowTCP(123, 456, 0, 1, ftp, flp1, fttl, ftp, flp2, fttl, ftf, fhf)
        f4 = FlowTCP(8899, 9800, 1, 0, ftp, flp2, fttl, ftp, flp1, fttl, ftf, fhf)

        flows = [f1, f2, f3, f4]
        nodes = [0, 1]
        s_nets = [('a', 'l'), ('a', 'l')]
        b_nets = [('b', 'r'), ('b', 'r')]
        res_nets, res_nodes = translate_nodes_and_nets(flows, nodes, nodes, s_nets, b_nets,
                                                       lambda x: 's' if x < 2 else 'b')
        assert len(res_nets) == 4
        assert len(res_nodes) == 4

    def test_delete_node(self):
        fflow = FFlow([[0.1, 1], [0.3, 2], [0.5, 3], [1.0, 4]])
        ftp = FTP([[0.1, 10], [0.2, 20], [0.8, 40], [1.0, 60]])
        flp1 = FLP([[0.1, 110], [0.3, 220], [0.5, 330], [1.0, 440]])
        flp2 = FLP([[0.1, 110], [0.3, 220], [0.7, 330], [1.0, 440]])
        fttl = FTTL([[0.1, 0], [0.3, 5], [0.5, 15], [1.0, 25]])
        ftf = FTF([[0.2, 1000], [0.3, 2000], [0.6, 3000], [1.0, 4000]])
        fhf = FHF([[0.5, 1]])
        f1 = FlowUDP(9995, 42, 0, 1, ftp, flp1, fttl, ftp, flp2, fttl, ftf, fhf)
        f2 = FlowUDP(9999, 40, 0, 2, ftp, flp2, fttl, ftp, flp1, fttl, ftf, fhf)
        f3 = FlowTCP(123, 456, 1, 2, ftp, flp1, fttl, ftp, flp2, fttl, ftf, fhf)
        f4 = FlowTCP(8899, 9800, 2, 0, ftp, flp2, fttl, ftp, flp1, fttl, ftf, fhf)
        flows = [f1, f2, f3, f4]
        nets = [('a', 'l'), ('b', 'r'), ('a', 'r')]
        nodes = [0, 1, 2, 0]
        o1 = NetworkGenome(nets, nodes, flows, fflow, 42.0)
        delete_node(o1, 2)
        assert len(o1.nodes) == 3
        assert len(o1.nets) == 2
        assert len(o1.flows) == 1

    def test_network_mutator(self):
        fflow = FFlow([[0.1, 1], [0.3, 2], [0.5, 3], [1.0, 4]])
        ftp = FTP([[0.1, 10], [0.2, 20], [0.8, 40], [1.0, 60]])
        flp1 = FLP([[0.1, 110], [0.3, 220], [0.5, 330], [1.0, 440]])
        flp2 = FLP([[0.1, 110], [0.3, 220], [0.7, 330], [1.0, 440]])
        fttl = FTTL([[0.1, 0], [0.3, 5], [0.5, 15], [1.0, 25]])
        ftf = FTF([[0.2, 1000], [0.3, 2000], [0.6, 3000], [1.0, 4000]])
        fhf = FHF([[0.5, 1]])
        f1 = FlowUDP(9995, 42, 0, 1, ftp, flp1, fttl, ftp, flp2, fttl, ftf, fhf)
        f2 = FlowUDP(9999, 40, 0, 2, ftp, flp2, fttl, ftp, flp1, fttl, ftf, fhf)
        f3 = FlowTCP(123, 456, 1, 2, ftp, flp1, fttl, ftp, flp2, fttl, ftf, fhf)
        f4 = FlowTCP(8899, 9800, 2, 0, ftp, flp2, fttl, ftp, flp1, fttl, ftf, fhf)
        flows = [f1, f2, f3, f4]
        nets = [('a', 'l'), ('b', 'r'), ('a', 'r')]
        nodes = [0, 1, 2, 0]
        o1 = NetworkGenome(nets, nodes, flows, fflow, 42.0)
        old_nets = nets[:]
        network_mutator(o1)
        assert len(o1.nets) != 3 or any(old_nets[i] != o1.nets[i] for i in xrange(3))

    # TODO write mutators tests

