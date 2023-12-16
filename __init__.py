# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GSI-AddressSearch
                                  A QGIS plugin
                              -------------------
        copyright            : Kohei Hara
 ***************************************************************************/
"""

def classFactory(iface):
    from .gsi_address_search import GsiAddressSearch
    return GsiAddressSearch(iface)


