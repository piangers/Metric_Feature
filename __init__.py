# -*- coding: utf-8 -*-

def classFactory(iface):
    # load CadInput class from file CadInput
    from Metric import Metric
    return Metric(iface)
