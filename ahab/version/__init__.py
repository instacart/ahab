# coding: utf-8
# © 2015 Instacart
import pkg_resources


def version():
    try:
        parent = '.'.join(__package__.split('.')[0:-1])
        distribution = pkg_resources.get_distribution(parent)
        return distribution.version
    except:
        return '19700101'
