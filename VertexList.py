# -*- coding: utf-8 -*-

from qgis.core import QgsPoint, QgsRectangle

class VertexList(list):
    
    def __init__(self):
        list.__init__(self)

        self.snapPoint = None
        self.snapSegment = None

#_________________________________________________

    def empty(self):
        self[:] = []

    def updateCurrentPoint(self, point):
        if len(self)>0:
            self[0] = point
        else:
            self.insert(0, point)

    def newPoint(self):
        self.insert(0, self[0])
 
    def removeLastPoint(self):
        print len(self)
        if len(self)>1:
            del self[1]
#_________________________________________________

    def currentPoint(self):
        if len(self):
            return self[0]
        else:
            return None

    def previousPoint(self):
        if len(self) > 1:
            return self[1]
        else:
            return None

    def penultimatePoint(self):
        if len(self) > 2:
            return self[2]
        else:
            return None


