# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GSI-AddressSearch
                                  A QGIS plugin
                              -------------------
        copyright            : Kohei Hara
 ***************************************************************************/
"""

from .networkaccessmanager import NetworkAccessManager
import sys, os, json

NAM = NetworkAccessManager()

class GsiGeoCoderException(Exception):
    pass

class GsiGeoCoder():

    url = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q={address}'
    r_url = 'https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress?lon={lon}&lat={lat}'

    def geocode(self, address):
        try: 
            url = self.url.format(**{'address': address.decode('utf8')})
            results = NAM.request(url, blocking=True)[1].decode('utf8')
            if not results:
                return
            results = json.loads(results)
            return [(rec['properties']['title'], (str(rec['geometry']['coordinates'][0]), str(rec['geometry']['coordinates'][1]))) for rec in results]
        except Exception as e:
            raise GsiGeoCoderException(str(e))

    def reverse(self, lon, lat):
        try: 
            url = self.r_url.format(**{'lon': lon, 'lat': lat})
            results = NAM.request(url, blocking=True)[1].decode('utf8')
            if not results:
                return
            results = json.loads(results)
            return results['results']['lv01Nm']
        except Exception as e:
            raise GsiGeoCoderException(str(e))
