# -*- coding: utf-8 -*-
"""
/***************************************************************************
 tileCacheCreatorDialog
                                 A QGIS plugin
 Create local disk tile cache for offline use
                             -------------------
        begin                : 2014-04-21
        copyright            : (C) 2014 by Apropos Information Systems Inc.
        email                : tsw.web@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   any later version.                                                    *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4 import QtCore, QtGui
from qgis.core import *
from qgis.gui import *
from ui_tilecachecreator import Ui_TileCacheCreator
from tilecache_workers import cacheCreator
import os, sys
from owslib.wms import WebMapService

class tileCacheCreatorDialog(QtGui.QDialog, Ui_TileCacheCreator):
    
    def __init__(self, iface):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        
        # make connections
        # main action buttons
        QtCore.QObject.connect(self.btnUpdate, QtCore.SIGNAL("clicked()"), self.updateFromLayer)
        QtCore.QObject.connect(self.btnCanvas, QtCore.SIGNAL("clicked()"), self.updateFromCanvas)
        # selecting files, directories & layers
        QtCore.QObject.connect(self.tbConfigFile, QtCore.SIGNAL("clicked()"), self.getConfig)
        QtCore.QObject.connect(self.tbCacheDir, QtCore.SIGNAL("clicked()"), self.getCacheDir)
        QtCore.QObject.connect(self.tbGetLayers, QtCore.SIGNAL("clicked()"), self.getLayers)
        # keeping min and max values appropriate in relation to each other
        QtCore.QObject.connect(self.spMinZoom, QtCore.SIGNAL("valueChanged(int)"), self.minZoomChange)
        QtCore.QObject.connect(self.spMaxZoom, QtCore.SIGNAL("valueChanged(int)"), self.maxZoomChange)
        # control enabled state on create and update buttons
        QtCore.QObject.connect(self.leTileCacheConfig, QtCore.SIGNAL("textChanged(QString)"), self.enableRunButtons)
        QtCore.QObject.connect(self.leTileCacheDir, QtCore.SIGNAL("textChanged(QString)"), self.enableRunButtons)
        QtCore.QObject.connect(self.leSourceName, QtCore.SIGNAL("textChanged(QString)"), self.enableRunButtons)
        QtCore.QObject.connect(self.leURL, QtCore.SIGNAL("textChanged(QString)"), self.enableRunButtons)
        QtCore.QObject.connect(self.leLayer, QtCore.SIGNAL("textChanged(QString)"), self.enableRunButtons)
        # connect UI buttons to run actions
        QtCore.QObject.connect(self.pbBuild, QtCore.SIGNAL("clicked()"), self.createCache)
        QtCore.QObject.connect(self.pbSaveConfig, QtCore.SIGNAL("clicked()"), self.saveConfig)

        # setup layer list
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        layerNames = []
        for name, layer in layerMap.iteritems():
            layerNames.append(unicode(layer.name()))
        self.cmbExtents.clear()
        self.cmbExtents.addItems(layerNames)
        self.pbZoomProgress.setRange( 0, 100 )
        self.pbTileProgress.setRange( 0, 100 )

        self.layerType = 'NotValid'
        self.imageFormat = 'image/jpeg'

    #
    # getLayers - get service type and layer info

    def getLayers( self ):

        layerList = []
        # check to see if valid service and get layer list
        try:
            wms = WebMapService("http://%s" % self.leURL.text(), version='1.1.1')
            if 'WMS' in wms.identification.type:
                self.rdoWMS.setChecked(True)
                layerList = list(wms.contents)
                self.layerType = 'WMS'
        except:
            self.rdoNotValid.setChecked(True)
            self.layerType = 'NotValid'
        # let user select layer
        if layerList <> []:
            layerName = QtGui.QInputDialog.getItem(self, 'Select Layer', 'Layer Name:', layerList)[0]
            if layerName <> '':
                self.leLayer.setText(layerName)

        
    #
    # updateExtents - updates extent values using lon / lat values 

    def updateExtents( self, boundBox ):
        # get project or layer crs
        crsSrc = self.iface.mapCanvas().mapRenderer().destinationCrs()
        # set destination crs
        crsDest = QgsCoordinateReferenceSystem(4326)
        # set tranformation
        cTr = QgsCoordinateTransform(crsSrc,crsDest)
        # transform coordinates to lat / lon
        ll = cTr.transform( QgsPoint(boundBox.xMinimum(),boundBox.yMinimum()) )
        ur = cTr.transform( QgsPoint(boundBox.xMaximum(),boundBox.yMaximum()) )
        # update extents
        self.spnXmin.setValue( ll.x() )
        self.spnYmin.setValue( ll.y() )
        self.spnXmax.setValue( ur.x() ) 
        self.spnYmax.setValue( ur.y() )

    #
    # updateCanvas - update extent of tile cache using map canvas
        
    def updateFromCanvas( self ):
        canvas = self.iface.mapCanvas()
        boundBox = canvas.extent()
        self.updateExtents( boundBox )

    #
    # updateFromLayer - update extent of tile cache using layer
    
    def updateFromLayer( self ):
        mLayerName = self.cmbExtents.currentText()
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        for name, layer in layerMap.iteritems():
            if layer.name() == mLayerName:
                if layer.isValid():
                    bbox = layer.extent()
                    self.updateExtents(bbox)

    #
    # getConfig - get or set config file
    
    def getConfig( self ):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Get Config File', '.', '*.tcc')
        if fname <> '' and os.path.splitext(fname)[1] == '':
            fname = fname + '.tcc'
        self.leTileCacheConfig.setText(fname)
        # read file if it exists
        if os.path.exists(fname):
            self.readConfig(fname)

    #
    # geCacheDir - get base directory to place tile cache

    def getCacheDir( self ):
        dname = QtGui.QFileDialog.getExistingDirectory(self, 'Select Cache Directory')
        if dname <> '':
            self.leTileCacheDir.setText(dname)

    #
    # readConfig - load values from TileCacheCreator config file
    
    def readConfig( self, fname ):
        f = open(fname,'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            if 'cacheDir' in line:
                self.leTileCacheDir.setText(line[line.index('=')+1:].strip())
            elif 'sourceName' in line:
                self.leSourceName.setText(line[line.index('=')+1:].strip())
            elif 'sourceURL' in line:
                self.leURL.setText(line[line.index('=')+1:].strip())
            elif 'layerType' in line:
                self.layerType = line[line.index('=')+1:].strip()
                if self.layerType == 'WMS':
                    self.rdoWMS.setChecked(True)
                else:
                    self.rdoNotValid.setChecked(True)
                    self.layerType = 'NotValid'
            elif 'wmsLayer' in line:
                self.leLayer.setText(line[line.index('=')+1:].strip())
            elif 'minZoom' in line:
                self.spMinZoom.setValue(int(line[line.index('=')+1:]))
            elif 'maxZoom' in line:
                self.spMaxZoom.setValue(int(line[line.index('=')+1:]))
            if 'extents' in line:
                eList = line[line.index('=')+1:].split(',')
                self.spnXmin.setValue(float(eList[0]))
                self.spnYmin.setValue(float(eList[1]))
                self.spnXmax.setValue(float(eList[2]))
                self.spnYmax.setValue(float(eList[3]))
            elif 'imageFormat' in line:
                self.imageFormat = line[line.index('=')+1:].strip()
                if self.imageFormat == 'image/jpeg':
                    self.rdoJPG.setChecked(True)
                elif self.imageFormat == 'image/png':
                    self.rdoPNG.setChecked(True)
                else:
                    self.rdoGIF.setChecked(True)
                    self.imageFormat = 'image/gif'
    #
    # saveConfig - write values to TileCacheCreator config file

    def saveConfig( self ):
        cacheDir = self.leTileCacheDir.text()
        if not os.path.exists(cacheDir):
            os.makedirs(cacheDir)
        fname = self.leTileCacheConfig.text()
        f = open(fname,'w')
        f.write('cacheDir=%s\n' %  cacheDir)
        f.write('sourceName=%s\n' % self.leSourceName.text())
        f.write('sourceURL= %s\n' % self.leURL.text())
        f.write('layerType=%s\n' % self.layerType)
        f.write('wmsLayer=%s\n' % self.leLayer.text())
        f.write('minZoom=%d\n' % self.spMinZoom.value())
        f.write('maxZoom=%d\n' % self.spMaxZoom.value())
        f.write('extents=%f,%f,%f,%f\n' % (self.spnXmin.value(),
            self.spnYmin.value(), self.spnXmax.value(),
            self.spnYmax.value()))
        f.write('imageFormat=%s\n' % self.imageFormat)
        f.close() 

    #
    # minZoomChange - when min zoom changes, adjust max zoom to be larger

    def minZoomChange( self ):
        if self.spMinZoom.value() >= self.spMaxZoom.value():
            self.spMaxZoom.setValue(self.spMinZoom.value()+1)

    #
    # maxZoomChange - when max zoom changes, adjust min zoom to be smaller

    def maxZoomChange( self ):
        if self.spMinZoom.value() >= self.spMaxZoom.value():
            self.spMinZoom.setValue(self.spMaxZoom.value()-1)

    #
    # enableRunButtons - enable / disable run buttons if all fields have values or not

    def enableRunButtons( self ):
        if self.leTileCacheConfig.text() <> "" \
        and self.leTileCacheDir.text() <> "" and self.leSourceName.text() <> "" \
        and self.leURL.text() <> "" and self.leLayer.text() <> "":
            self.pbBuild.setEnabled(True)
            self.pbSaveConfig.setEnabled(True)
        else:
            self.pbBuild.setDisabled(True)
            self.pbSaveConfig.setDisabled(True)

    #
    # createCache - run cache creation processes
            
    def createCache( self ):
        

        # configure the QgsMessageBar
        messageBar = self.iface.messageBar().createMessage('Building TileCache...', )
        # connect messageBar to self
        self.messageBar = messageBar

        # set interface interactivity appropriately
        self.setInterfaceForRun()

        bbox = [self.spnXmin.value(),self.spnYmin.value(),self.spnXmax.value(),self.spnYmax.value()]

        cacheDir = self.leTileCacheDir.text()
        # create worker instance
        worker = cacheCreator(cacheDir, self.leSourceName.text(),self.leURL.text(),
            self.layerType, self.leLayer.text(), self.spMinZoom.value(),
            self.spMaxZoom.value(), bbox, self.imageFormat)

        # connect cancel to worker kill
        self.pbCancel.clicked.connect(worker.kill)
            
        # start the worker in a new thread
        thread = QtCore.QThread(self)
        worker.moveToThread(thread)
        # connect things together
        worker.finished.connect(self.creationFinished)
        worker.error.connect(self.creationError)
        worker.zoomProgress.connect(self.pbZoomProgress.setValue)
        worker.tileProgress.connect(self.pbTileProgress.setValue)
        thread.started.connect(worker.run)
        # run
        thread.start()
        # manage thread and worker
        self.thread = thread
        self.worker = worker

    #
    # creationFinished - wrap up tasks
    
    def creationFinished( self, ret ):
        # clean up the worker and thread
        self.worker.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()
        # remove widget from message bar
        self.iface.messageBar().popWidget(self.messageBar)
        if ret == True:
            # report the result
            self.iface.messageBar().pushMessage('Cache building completed', duration=10)
        else:
            # notify the user that something went wrong
            self.iface.messageBar().pushMessage('Something went wrong! See the message log for more information.', level=QgsMessageBar.CRITICAL, duration=10)
        self.setInterfaceAfterRun()
        # write config file for TileLayer plugin
        tsvConfig = self.leTileCacheDir.text()+'.tsv'
        source = self.leSourceName.text()
        fpath = 'file:///' + self.leTileCacheDir.text() + '/{z}/{x}/{y}'
        if self.rdoJPG.isChecked():
            fpath = fpath + '.jpg'
        elif self.rdoPNG.isChecked():
            fpath = fpath + '.png'
        else:
            fpath = fpath + '.gif'
        minZoom = self.spMinZoom.value()
        maxZoom = self.spMaxZoom.value()
        f = open(tsvConfig,'w')
        f.write('%s\t%s\t%s\t%d\t%d\t%d\t%f\t%f\t%f\t%f\n' % \
            (source,source,fpath,0,minZoom,maxZoom,self.spnXmin.value(),\
            self.spnYmin.value(),self.spnXmax.value(),self.spnYmax.value()) )
        f.close()
        
    #
    # creationError - notify user of error
    
    def creationError(self, e, exception_string):
        QgsMessageLog.logMessage('Worker thread raised an exception:\n'.format(exception_string), level=QgsMessageLog.CRITICAL)
        self.setInterfaceAfterRun()

    #
    # setInterfaceForRun - disable some buttons during running and enable others
    
    def setInterfaceForRun( self ):
        # set button visibility
        self.pbCancel.setEnabled(True)
        self.pbClose.setDisabled(True)
        self.pbSaveConfig.setDisabled(True)
        self.pbBuild.setDisabled(True)

    #
    # setInterfaceAfterRun - disable some buttons after running and enable others
    
    def setInterfaceAfterRun( self ):
        # renable buttons
        self.pbCancel.setDisabled(True)
        self.pbClose.setEnabled(True)
        self.pbSaveConfig.setEnabled(True)
        self.pbBuild.setEnabled(True)
        # reset progress bars
        self.pbZoomProgress.setValue(0)
        self.pbTileProgress.setValue(0)
