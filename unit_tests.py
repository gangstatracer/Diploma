#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase

from scapy.all import *
from scapy.layers.inet import IP, UDP, TCP, ICMP

from flow import FlowUDP, FlowTCP, FlowICMP, FlowSock
from fx import *
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
        old_points = f.points[:]
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


