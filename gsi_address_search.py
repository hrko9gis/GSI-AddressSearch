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

from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem

# Import the code for the dialog
from .gsi_address_search_dialog import GsiAddressSearchDialog
from .target_select_dialog import TargetSelectDialog
from .add_target_select_dialog import AddTargetSelectDialog

from .gsi_geo_coder import *


class GsiAddressSearch:

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.layerid = ''
        self.layer = None
        try:
            self.registry = QgsMapLayerRegistry.instance()
        except:
            self.registry = QgsProject.instance()


#    def logMessage(self, msg):
#        QgsMessageLog.logMessage(msg, 'GSI-AddressSearch')


    def initGui(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))

        self.action = QAction(QIcon(os.path.join(current_directory, "img", "Search.gif")), \
        u'住所検索', self.iface.mainWindow())
        self.action.triggered.connect(self.search)

        self.add_point_action = QAction(QIcon(os.path.join(current_directory, "img", "SearchAddPoint.gif")), \
        u'検索ポイント追加', self.iface.mainWindow())
        self.add_point_action.triggered.connect(self.search_add_point)

        self.menu = QMenu(QCoreApplication.translate('GSI-AddressSearch', u'住所検索（国土地理院API）'))
        self.menu.addActions([self.action, self.add_point_action])
        self.iface.pluginMenu().addMenu(self.menu)
        self.iface.addToolBarIcon(self.action)
        self.iface.addToolBarIcon(self.add_point_action)

        self.previous_map_tool = self.iface.mapCanvas().mapTool()


    def unload(self):
        self.iface.removePluginMenu('GSI-AddressSearch', self.action)
        self.iface.removePluginMenu('GSI-AddressSearch', self.add_point_action)
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeToolBarIcon(self.add_point_action)
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
                results = geo_coder.geocode(unicode(gasdlg.address.text()).encode('utf-8'))
            except Exception as e:
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('GSI-AddressSearch', u"住所検索 エラー"), QCoreApplication.translate('GSI-AddressSearch', u"ジオコーディングサービスでエラーが発生しました。:<br><strong>%s</strong>" % e))
                return

            if not results:
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('GSI-AddressSearch', u"住所検索 結果なし"), QCoreApplication.translate('GSI-AddressSearch', u"ジオコーディングサービスから検索結果を得られませんでした。: <strong>%s</strong>." % gasdlg.address.text()))
                return

            locations = {}
            for location, point in results:
                locations[location] = point

            if len(locations) == 1:
                self.locate(point)
            else:
                locations = dict(sorted(locations.items()))
            
                all_str = QCoreApplication.translate('GSI-AddressSearch', 'All')
                tsdlg = TargetSelectDialog()
                tsdlg.placesComboBox.addItem(all_str)
                tsdlg.placesComboBox.addItems(locations.keys())
                tsdlg.show()
                results = tsdlg.exec_()

                if results == 1 :
                    if tsdlg.placesComboBox.currentText() == all_str:
                        for location in locations:
                            self.locate(locations[location])
                    else:
                        point = locations[unicode(tsdlg.placesComboBox.currentText())]
                        self.locate(point)
            return


    def locate(self, point):

        self.set_canvas_center_lon_lat(point[0], point[1])

        # if scale:
        #     self.canvas.zoomScale(scale)

        self.canvas.refresh()


    def set_canvas_center_lon_lat(self, lon, lat):

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


    def search_add_point(self):
        if self.previous_map_tool:
            self.iface.mapCanvas().setMapTool(self.previous_map_tool)

        geo_coder = GsiGeoCoder()
        
        gasdlg = GsiAddressSearchDialog()
        gasdlg.show()
        result = gasdlg.exec_()

        if result == 1 :
            try:
                results = geo_coder.geocode(unicode(gasdlg.address.text()).encode('utf-8'))
            except Exception as e:
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('GSI-AddressSearch', u"住所検索 エラー"), QCoreApplication.translate('GSI-AddressSearch', u"ジオコーディングサービスでエラーが発生しました。:<br><strong>%s</strong>" % e))
                return

            if not results:
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('GSI-AddressSearch', u"住所検索 結果なし"), QCoreApplication.translate('GSI-AddressSearch', u"ジオコーディングサービスから検索結果を得られませんでした。: <strong>%s</strong>." % gasdlg.address.text()))
                return

            locations = {}
            for location, point in results:
                locations[location] = point

            locations = dict(sorted(locations.items()))
            
            atsdlg = AddTargetSelectDialog()
            
            model = QStandardItemModel(len(locations), 1)

            for idx, location in enumerate(locations):
                model.setItem(idx, 0, QStandardItem(location))

            atsdlg.listView.setModel(model)
            
            atsdlg.show()
            result = atsdlg.exec_()
            
            if result == 1 :
                
                self.add_map_layer()
                
                features = []
                
                for index in atsdlg.listView.selectedIndexes():
                    item =  model.itemFromIndex(index)
                    title = item.text()
                    feature = self.get_layer_feature(title, locations[title][0], locations[title][1])
                    features.append(feature)
                
                self.add_layer_features(features)
            
                if title :
                    self.locate(locations[title])
            
            return


    def add_map_layer(self):
    
        if not self.registry.mapLayer(self.layerid) :
        
            try:
                crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
            except:
                crs = self.iface.mapCanvas().mapSettings().destinationCrs()

            self.layer = QgsVectorLayer("Point?crs=" + crs.authid(), "GSI-Points", "memory")

            self.provider = self.layer.dataProvider()
            self.provider.addAttributes([QgsField("title", QVariant.String)])

            self.layer.updateFields()

            label_settings = QgsPalLayerSettings()
            label_settings.fieldName = "title"
            format = QgsTextFormat()
            format.setColor(QColor(0, 0, 0))
            bufferSettings = QgsTextBufferSettings()
            bufferSettings.color = QColor(255,255,255)
            bufferSettings.setSize(1)
            bufferSettings.setEnabled(True)
            format.setBuffer(bufferSettings)
            label_settings.setFormat(format)
            self.layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
            self.layer.setLabelsEnabled(True)

            self.registry.addMapLayer(self.layer)
            
            self.layerid = self.layer.id()


    def get_layer_feature(self, title, lon, lat):
        
        point = QgsPoint(float(lon), float(lat))
        
        try:
            fields = self.layer.pendingFields()
        except:
            fields = self.layer.fields()

        feature = QgsFeature(fields)
        try:
            feature.setGeometry(QgsGeometry.fromPoint(point))
        except:
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point)))

        feature['title'] = title
        
        return feature


    def add_layer_features(self, features):
        self.layer.startEditing()
        self.layer.addFeatures(features)
        self.layer.commitChanges()


if __name__ == "__main__":
    pass
