#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
import genetic_engine
from nets_manager import Translator
from scapy.all import *


def get_network_packs(genome):
    left = []
    right = []
    translator = Translator(genome.nets, genome.nodes)
    for f in genome.flows:
        packs = f.generate(translator, 0)
        for p in packs:
            del p.chksum
            p.src = p['IP'].src
            p.dst = p['IP'].dst
        left.extend([p for p in packs if translator.ip2pos[p['IP'].src] == 'l'])
        right.extend([p for p in packs if translator.ip2pos[p['IP'].src] == 'r'])

    left.sort(key=lambda pack: pack['IP'].time)
    right.sort(key=lambda pack: pack['IP'].time)

    return left, right


def network_packets_count_tester(genome):
    genetic_engine.check_genome(genome)
    left, right = get_network_packs(genome)
    if len(left) > 0:
        send(left, iface='eth1')
    if len(right) > 0:
        send(right, iface='eth0')
    name = """/home/tmp/""" + str(uuid.uuid1())
    f = open(name, 'w')
    f.write(str(genome))
    f.close()
    if len(left) > 0:
        wrpcap(name + '--left' + '.cap', left)
    if len(right) > 0:
        wrpcap(name + '--right' + '.cap', right)
    return len(left) + len(right)


def network_listener(left_count, right_count):
    left_sniffed = sniff(iface='eth0', count=left_count)
    right_sniffed = sniff(iface='eth1', count=right_count)
    return left_sniffed, right_sniffed
