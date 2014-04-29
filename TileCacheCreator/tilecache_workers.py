
###############################################################################################
#
#   OWNER:          (C) Trevor Wiens
#   REVISION:       $Rev: 1 $
#   REV DATE:       $Date: 2014-04-23 $
#   REV AUTHOR:     $Author: tsw $
#   DEVELOPERS:     Trevor Wiens
#   PURPOSE:        This module does the following:
#                   - main worker objects to create tiles and update interface
#                   as thread to prevent QGIS from freezing
#   NOTE:           Much of the geographic code in this module is based on either
#                   gdal2tiles.py by Klokan Petr Pridal (2008) or TileLayer Plugin
#                   by Minoru Akagi for QGIS 2.x
#   LICENSE:        GPL 2 or later
#
###############################################################################################

from qgis.core import *
from PyQt4 import QtCore, QtGui
import traceback, time, os, math, sys
from owslib.wms import WebMapService

#
# function to create tiles
#

class cacheCreator(QtCore.QObject):
    
    def __init__( self, dirName, sourceName, sourceURL, layerType, sourceLayer,
        minZoom, maxZoom, bbox, imageFormat, *args, **kwargs ):
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.zoomCount = maxZoom - minZoom + 1
        self.tileCount = 0
        self.zoomProcessed = 0
        self.tileProcessed = 0
        self.zoomPercentage = 0
        self.tilePercentage = 0
        self.abort = False
        self.dirName = dirName
        self.sourceName = sourceName
        self.sourceURL = sourceURL
        self.layerType = layerType
        self.minZoom = minZoom
        self.maxZoom = maxZoom 
        self.bbox = bbox
        self.imageFormat = imageFormat
        self.R = 6378137
        self.tileSize = 256
        self.ver = '1.1.1'
        self.wmsLayer = sourceLayer
        self.wmsStyle = ''
        self.crs = 'EPSG:3857'
        self.originShift = 2 * math.pi * self.R / 2.0
        self.killed = False
        
    def run( self ):
        try:
            self.status.emit('Task started!')
            # do something
            curZoom = self.minZoom
            while curZoom <= self.maxZoom:
                if self.abort is True:
                    self.killed.emit()
                    break
                # start work here
                self.createTiles(curZoom)
                # reset counter variables for tiles
                self.tileProcessed = 0
                self.tilePercentage = 0
                # finish work here
                curZoom = curZoom + 1
                # update zoom progress
                self.calculate_zoom_progress()
            self.status.emit('Task finished!')
        except Exception, e:
            import traceback
            self.error.emit(e, traceback.format_exc())
            self.finished.emit(False)
        else:
            self.finished.emit(True)


    def kill( self ):
        self.abort = True

    #
    # calculate_zoom_progress - update zoom progress bar
    
    def calculate_zoom_progress( self ):
        self.zoomProcessed = self.zoomProcessed + 1
        percentage_new = (self.zoomProcessed * 100) / self.zoomCount
        if percentage_new > self.zoomPercentage:
            self.zoomPercentage = percentage_new
            self.zoomProgress.emit(self.zoomPercentage)

    #
    # calculate_tile_progress - update tile progress bar

    def calculate_tile_progress( self ):
        self.tileProcessed = self.tileProcessed + 1
        percentage_new = (self.tileProcessed * 100) / self.tileCount
        if percentage_new > self.tilePercentage:
            self.tilePercentage = percentage_new
            self.tileProgress.emit(self.tilePercentage)

    #
    # createTiles - create all tiles for a specified zoom level

    def createTiles( self, curZoom ):
        # determine number of tiles at this zoom level
        tileList = self.getTileList(curZoom)
        self.tileCount = len(tileList)
        ## start debugging code
        #f = open('tilelist.log',"a")
        #f.write('zoom = %d\n' % curZoom)
        #f.write(str(tileList)+'\n')
        #f.close()
        ## end debugging code
        # connect to service
        if self.layerType == 'WMS' or self.layerType == 'tWMS':
            # connect to wms
            self.wms = WebMapService('http://%s' % self.sourceURL, version = self.ver)
            # iterate over tile list and create tiles as needed
            for tile in tileList:
                x = self.createTile( tile, curZoom )
                self.calculate_tile_progress()

    #
    # getTileList -convert current zoom and bounding box into list of tiles

    def getTileList( self, curZoom ):
        
        # convert lon & lat to EPSG:3857 metres x & y respectively
        minX, minY = lonlat2mercator(self.bbox[0],self.bbox[1])
        maxX, maxY = lonlat2mercator(self.bbox[2],self.bbox[3])
        # convert EPSG:3857 metres to pixels
        res = (2 * math.pi * self.R) / (self.tileSize * 2**curZoom)
        pMinX = (minX + self.originShift) / res
        pMinY = (minY + self.originShift) / res
        pMaxX = (maxX + self.originShift) / res
        pMaxY = (maxY + self.originShift) / res
        # convert pixels to tiles
        tMinX = int( math.ceil( pMinX / float(self.tileSize) ) - 1 )
        tMinY = int( math.ceil( pMinY / float(self.tileSize) ) - 1 )
        tMaxX = int( math.ceil( pMaxX / float(self.tileSize) ) - 1 )
        tMaxY = int( math.ceil( pMaxY / float(self.tileSize) ) - 1 )
        # create tile list
        tileList = []
        for tileY in range(tMinY, tMaxY+1):
            for tileX in range(tMinX, tMaxX+1):
                tileList.append(['%d' % tileY,'%d' % tileX])
        return(tileList)

    #
    # createTile - creates a tile from a WMS service

    def createTile( self, tile, curZoom ):

        # get tiles
        tileX = int(tile[1])
        tileY = int(tile[0])
        # get EPSG:3857 bounding box of tile
        res = (2 * math.pi * self.R) / (self.tileSize * 2**curZoom)
        minX = tileX * self.tileSize * res - self.originShift
        minY = tileY * self.tileSize * res - self.originShift
        maxX = (tileX + 1) * self.tileSize * res - self.originShift
        maxY = (tileY + 1) * self.tileSize * res - self.originShift
        mBbox = [minX,minY,maxX,maxY]
        ## start debugging code
        #f = open('coords.log', 'a')
        #f.write('zoom=%d\n' % curZoom)
        #f.write(str(mBbox)+'\n')
        #f.write('x:%s, y:%s\n' % (tileX, tileY))
        #f.close()
        ## end debugging code
        # create directory structure if needed
        ofDir = os.path.join(self.dirName,'%d' % curZoom, str(tile[1]))
        ## start debugging code
        #f = open('filepathinfo.log','a')
        #f.write('%s \n' % ofDir)
        #f.close()
        ## end debugging code
        if not os.path.exists(ofDir):
            os.makedirs(ofDir)
        # get file name with full path
        if self.imageFormat == 'image/jpeg':
            ofName = os.path.join(ofDir,'%s.jpg' % tile[0])
        elif self.imageFormat == 'image/png':
            ofName = os.path.join(ofDir,'%s.png' % tile[0])
        else:
            ofName = os.path.join(ofDir,'%s.gif' % tile[0])
        # if file doesn't exist, create it
        if not os.path.exists(ofName):
            ## debugging code starts here
            #f = open('wmsinfo.log','a')
            #f.write('fname=%s\n' % ofName)
            #f.write('layers=[%s]\n' % self.wmsLayer)
            #f.write('styles=[%s]\n' % self.wmsStyle)
            #f.write('srs=%s\n' % self.crs)
            #f.write('bbox=%s\n' % str(mBbox))
            #f.write('size=(%d,%d)\n' % (self.tileSize, self.tileSize))
            #f.write('format=%s\n' % self.imageFormat)
            #f.write('transparent=False\n')
            #f.write('timeout=10\n\n')
            #f.close()
            ## debugging code ends here
            img = self.wms.getmap(layers=[self.wmsLayer], styles=[self.wmsStyle], srs=self.crs, \
                                bbox=mBbox, size=(self.tileSize, self.tileSize), \
                                format=self.imageFormat, transparent=False, timeout=10 )
            out = open(ofName, 'wb')
            out.write(img.read())
            out.close()
        return(0)

    zoomProgress = QtCore.pyqtSignal(int)
    tileProgress = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(Exception, basestring)
    finished = QtCore.pyqtSignal(bool)


#
# Geometry Functions
#

def lonlat2mercator( lon, lat ):

    R = 6378137
    x = R * lon * math.pi / 180
    y = R * math.log(math.tan(math.pi / 4 + (lat * math.pi / 180) / 2))

    return(x,y)

def bbox2mercator( bbox ):

    mBbox = []

    mBbox[0],mBbox[1] = lonlat2mercator(bbox[0],bbox[1])
    mBbox[2],mBbox[3] = lonlat2mercator(bbox[2],bbox[3])

    return(mBbox)

def mercator2lonlat( x, y ):

    lon = (x * 180) / (math.pi * R)
    lp1 = (y * 180) / (math.pi * R)
    lat = 180 / math.pi * (2 * math.atan( math.exp( lp1 * math.pi / 180.0)) - math.pi / 2.0)

    return(lon,lat)

def bbox2lonlat( bbox ):

    llBbox = []

    llBbox[0],llBbox[1] = mercator2lonlat(bbox[0],bbox[1])
    llBbox[2],llBbox[3] = mercator2lonlat(bbox[2],bbox[3])

    return(llBbox)


