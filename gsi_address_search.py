# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GSI-AddressSearch
                                  A QGIS plugin
                              -------------------
        copyright            : Kohei Hara
 ***************************************************************************/
"""

import sys, os


# Import the PyQt and QGIS libraries
try:
    from qgis.core import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5 import uic
    QT_VERSION=5
    os.environ['QT_API'] = 'pyqt5'
    from urllib.request import URLError
except:
    from PyQt4.QtCore import *
    from PyQt4.QtCore import QSettings as QgsSettings
    from PyQt4.QtGui import *
    from PyQt4 import uic
    QT_VERSION=4
    from urllib2 import URLError

# Import the code for the dialog
from .gsi_address_search_dialog import GsiAddressSearchDialog
from .target_select_dialog import TargetSelectDialog

from .gsi_geo_coder import *


class GsiAddressSearch:

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()


#    def logMessage(self, msg):
#        QgsMessageLog.logMessage(msg, 'GsiAddressSearch')


    def initGui(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))

        self.action = QAction(QIcon(os.path.join(current_directory, "images", "Search.gif")), \
        u'住所検索', self.iface.mainWindow())
        self.action.triggered.connect(self.search)

        self.menu = QMenu(QCoreApplication.translate('GsiAddressSearch', u'住所検索（国土地理院API）'))
        self.menu.addActions([self.action])
        self.iface.pluginMenu().addMenu(self.menu)
        self.iface.addToolBarIcon(self.action)

        self.previous_map_tool = self.iface.mapCanvas().mapTool()


    def unload(self):
        self.iface.removePluginMenu(u'住所検索（国土地理院API）', self.action)
        self.iface.removeToolBarIcon(self.action)
        if self.previous_map_tool:
            self.iface.mapCanvas().setMapTool(self.previous_map_tool)


    def search(self):
        if self.previous_map_tool:
            self.iface.mapCanvas().setMapTool(self.previous_map_tool)

        geo_coder = GsiGeoCoder()
        
        gasdlg = GsiAddressSearchDialog()
        gasdlg.show()
        result = gasdlg.exec_()

        if result == 1 :
            try:
                result = geo_coder.geocode(unicode(gasdlg.address.text()).encode('utf-8'))
            except Exception as e:
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('GsiAddressSearch', u"住所検索 エラー"), QCoreApplication.translate('GsiAddressSearch', u"ジオコーディングサービスでエラーが発生しました。:<br><strong>%s</strong>" % e))
                return

            if not result:
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('GsiAddressSearch', u"住所検索 結果なし"), QCoreApplication.translate('GsiAddressSearch', u"ジオコーディングサービスから検索結果を得られませんでした。: <strong>%s</strong>." % gasdlg.address.text()))
                return

            locations = {}
            for location, point in result:
                locations[location] = point

            if len(locations) == 1:
                self.locate(point)
            else:
                all_str = QCoreApplication.translate('GsiAddressSearch', 'All')
                tsdlg = TargetSelectDialog()
                tsdlg.placesComboBox.addItem(all_str)
                tsdlg.placesComboBox.addItems(locations.keys())
                tsdlg.show()
                result = tsdlg.exec_()

                if result == 1 :
                    if tsdlg.placesComboBox.currentText() == all_str:
                        for location in locations:
                            self.locate(locations[location])
                    else:
                        point = locations[unicode(tsdlg.placesComboBox.currentText())]
                        self.locate(point)
            return


    def locate(self, point):

        self.set_canvas_center_lon_and_lat(point[0], point[1])

        # if scale:
        #     self.canvas.zoomScale(scale)

        self.canvas.refresh()


    def set_canvas_center_lon_and_lat(self, lon, lat):

        point = QgsPoint(float(lon), float(lat))

        try:
            map_crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        except:
            map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        
        crs_wgs84 = QgsCoordinateReferenceSystem()
        crs_wgs84.createFromSrid(4326) # WGS 84 / UTM zone 33N
        
        try:
            transformer = QgsCoordinateTransform(crs_wgs84, map_crs)
        except:
            transformer = QgsCoordinateTransform(crs_wgs84, map_crs, QgsProject.instance())

        try:
            point = transformer.transform(point)
        except:
            point = transformer.transform(QgsPointXY(point)) 

        self.canvas.setCenter(point)


if __name__ == "__main__":
    pass
