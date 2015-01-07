#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase
from fx import FHF, FX


class TestFX(TestCase):
    def test_random(self):
        f = FX(1, 100, int, [[0.2, 42], [1.0, 9]])
        counts = {}
        for i in xrange(10000):
            r = f.random()
            if counts.has_key(r):
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


