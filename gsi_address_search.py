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
    from qgis.gui import *
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


#    def log_message(self, msg):
#        QgsMessageLog.logMessage(msg, 'GSI-AddressSearch')


    def initGui(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))

        self.action = QAction(QIcon(os.path.join(current_directory, "img", "Search.gif")), \
        u'住所検索', self.iface.mainWindow())
        self.action.triggered.connect(self.search)

        self.add_point_action = QAction(QIcon(os.path.join(current_directory, "img", "SearchAddPoint.gif")), \
        u'検索ポイント追加', self.iface.mainWindow())
        self.add_point_action.triggered.connect(self.search_add_point)

        self.click_point_address_action = QAction(QIcon(os.path.join(current_directory, "img", "ClickPointAddress.gif")), \
        u'クリック地点住所', self.iface.mainWindow())
        self.click_point_address_action.triggered.connect(self.click_point_address)

        self.menu = QMenu(QCoreApplication.translate('GSI-AddressSearch', u'住所検索（国土地理院API）'))
        self.menu.addActions([self.action, self.add_point_action, self.click_point_address_action])
        self.iface.pluginMenu().addMenu(self.menu)
        self.iface.addToolBarIcon(self.action)
        self.iface.addToolBarIcon(self.add_point_action)
        self.iface.addToolBarIcon(self.click_point_address_action)

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

        map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        crs_wgs84 = QgsCoordinateReferenceSystem('EPSG:4326') # WGS 84 / UTM zone 33N
        transformer = QgsCoordinateTransform(crs_wgs84, map_crs, QgsProject.instance())

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
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('GSI-AddressSearch', u"検索ポイント追加 エラー"), QCoreApplication.translate('GSI-AddressSearch', u"ジオコーディングサービスでエラーが発生しました。:<br><strong>%s</strong>" % e))
                return

            if not results:
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('GSI-AddressSearch', u"検索ポイント追加 結果なし"), QCoreApplication.translate('GSI-AddressSearch', u"ジオコーディングサービスから検索結果を得られませんでした。: <strong>%s</strong>." % gasdlg.address.text()))
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
        
        map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        crs_wgs84 = QgsCoordinateReferenceSystem('EPSG:4326') # WGS 84 / UTM zone 33N
        transformer = QgsCoordinateTransform(crs_wgs84, map_crs, QgsProject.instance())

        point = transformer.transform(QgsPointXY(point)) 

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


    def click_point_address(self):
        sb = self.iface.mainWindow().statusBar()
        sb.showMessage(u"住所を調べたい場所をクリックしてください。")
        ct = ClickPointAddressTool(self.iface, self.iface.mapCanvas());
        self.previous_map_tool = self.iface.mapCanvas().mapTool()
        self.iface.mapCanvas().setMapTool(ct)


class ClickPointAddressTool(QgsMapTool):

    def __init__(self, iface, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface


    def canvasPressEvent(self, event):

        x = event.pos().x()
        y = event.pos().y()
        pres_pt = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)

        map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        crs_wgs84 = QgsCoordinateReferenceSystem('EPSG:4326') # WGS 84 / UTM zone 33N
        transformer = QgsCoordinateTransform(map_crs, crs_wgs84, QgsProject.instance())

        point = transformer.transform(QgsPointXY(pres_pt)) 

        geo_coder = GsiGeoCoder()

        try:
            results = geo_coder.reverse(point[0], point[1])

            if not results:
                QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('GSI-AddressSearch', "クリック地点住所 結果なし"), unicode(QCoreApplication.translate('GSI-AddressSearch', u"ジオコーディングサービスから検索結果を得られませんでした。: <strong>%s</strong>." % 'lon:' + str(point[0]) + ' lat:' + str(point[1]))))
                return
            else:
                QMessageBox.information(None, u"クリック地点住所", str(results))
                
        except Exception as e:
            QMessageBox.information(self.iface.mainWindow(), QCoreApplication.translate('GSI-AddressSearch', "クリック地点住所 エラー"), unicode(QCoreApplication.translate('GSI-AddressSearch',  u"ジオコーディングサービスでエラーが発生しました。:<br><strong>%s</strong>" % e)))
        return


if __name__ == "__main__":
    pass
