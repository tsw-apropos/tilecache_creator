# -*- coding: utf-8 -*-
"""
/***************************************************************************
 tileCacheCreator
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
 This script initializes the plugin, making it known to QGIS.
"""
def name():
    return "tileCacheCreator"
def description():
    return "Create disk tile cache for offline use"
def version():
    return "Version 0.5"
def icon():
    return "icon.png"
def qgisMinimumVersion():
    return "2.2"
def author():
    return "Apropos Information Systems Inc."
def email():
    return "info@aproposinfosystems.com"

def classFactory(iface):
    # load TileCacheCreator class from file TileCacheCreator
    from tilecachecreator import tileCacheCreator
    return tileCacheCreator(iface)
