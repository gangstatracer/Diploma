#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pyevolve
from pyevolve import GSimpleGA
from pyevolve import Selectors
from pyevolve import DBAdapters

from genetic_engine import network_initializer

pyevolve.logEnable()
genome = network_initializer(None)
ga = GSimpleGA.GSimpleGA(genome)
ga.selector.set(Selectors.GRouletteWheel)
ga.setGenerations(10)
ga.setPopulationSize(4)
ga.terminationCriteria.set(GSimpleGA.ConvergenceCriteria)
csv_adapter = DBAdapters.DBFileCSV(identify="run1", filename="stats.csv")
ga.setDBAdapter(csv_adapter)
ga.evolve(freq_stats=3)
print ga.bestIndividual()
