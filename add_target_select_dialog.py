# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GSI-AddressSearch
                                  A QGIS plugin
                              -------------------
        copyright            : Kohei Hara
 ***************************************************************************/
"""

import os

# Import the PyQt and QGIS libraries
try:
    from qgis.core import Qgis
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5 import uic
    QT_VERSION=5
    os.environ['QT_API'] = 'pyqt5'
except:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    from PyQt4 import uic
    QT_VERSION=4

class AddTargetSelectDialog(QDialog):

  def __init__(self):
    super(AddTargetSelectDialog, self).__init__()
    uic.loadUi(os.path.join(os.path.dirname(__file__), 'add_target_select_dialog_base.ui'), self)
