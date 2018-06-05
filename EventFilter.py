# -*- coding: utf-8 -*-

# Import the PyQt and QGIS libraries

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import math


class EventFilter(QObject):
   
    def __init__(self, iface, vertexList, enableAction, combobox, spinbox):
        QObject.__init__(self)
        self.iface = iface
        self.mapCanvas = iface.mapCanvas()
        self.vertexList = vertexList
        self.enableAction = enableAction
        self.combobox = combobox
        self.spinbox = spinbox

        #snapping hack
        self.storeOtherSnapping = None # mantém as opções de encaixe da camada quando o snap está suspenso ou None se o snappig não estiver suspenso
        self.otherSnappingStored = False

        # snap layers list
        self.snapper = None # o snapper usado para obter pontos estourados da tela do mapa. Não podemos usar
        self.updateSnapper()
        self.mapCanvas.layersChanged.connect(self.updateSnapper)
        self.mapCanvas.scaleChanged.connect(self.updateSnapper)
        QgsProject.instance().readProject.connect(self.updateSnapper)
        QgsProject.instance().snapSettingsChanged.connect(self.updateSnapper) # TODO : não funciona ! Veja http://hub.qgis.org/issues/9465

    def close(self):
        self.mapCanvas.layersChanged.disconnect(self.updateSnapper)
        self.mapCanvas.scaleChanged.disconnect(self.updateSnapper)
        QgsProject.instance().readProject.disconnect(self.updateSnapper)
        QgsProject.instance().snapSettingsChanged.disconnect(self.updateSnapper)

    def updateSnapper(self):
        """
            Atualiza self.snapper para levar em consideração as alterações de camadas, camadas não exibidas por causa da escala * TODO * e da entrada do usuário * / TODO *
            @note: é uma pena que não podemos obter QgsMapCanvasSnapper (). mSnapper que substituiria todo o código abaixo (eu acho)
        """
        snapperList = []
        scale = self.iface.mapCanvas().mapRenderer().scale()
        curLayer = self.iface.legendInterface().currentLayer()
        layers = self.iface.mapCanvas().layers()
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer and layer.hasGeometryType():
                if not layer.hasScaleBasedVisibility() or layer.minimumScale() < scale <= layer.maximumScale():
                    (layerid, enabled, snapType, tolUnits, tol, avoidInt) = QgsProject.instance().snapSettingsForLayer(layer.id())                    
                    if not enabled:
                        continue
                    snapLayer = QgsSnapper.SnapLayer()
                    snapLayer.mLayer = layer
                    snapLayer.mSnapTo = snapType
                    snapLayer.mTolerance = tol
                    snapLayer.mUnitType = tolUnits
                    # colocar camada atual no topo
                    if layer is curLayer:
                        snapperList.insert(0, snapLayer)
                    else:
                        snapperList.append(snapLayer)

        self.snapper = QgsSnapper(self.mapCanvas.mapRenderer())
        self.snapper.setSnapLayers(snapperList)
        self.snapper.setSnapMode(QgsSnapper.SnapWithResultsWithinTolerances)


    ############################
    ##### EVENT MANAGEMENT #####
    ############################

    def eventFilter(self, obj, event):
        # Nós só executamos isso se o evento for espontâneo,
        # significa que foi gerado pelo sistema operacional.
        # Desta forma, o evento que criamos abaixo não será processado (o que seria um loop inifinite)
        if not event.spontaneous():
            return QObject.eventFilter(self, obj, event)

        # MOVEU MOUSE OU CLICK ESQUERDO
        if ( (  (event.type() == QEvent.MouseMove and event.button() != Qt.MidButton) or
                (event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton) or
                (event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton) ) ):
            
            # Obter as pressões
            (self.vertexList.snapPoint, self.vertexList.snapSegment) = self._toMapSnap( event.pos() )

           # Defina a posição atual do mouse (seja de snapPoint, de snapSegment ou de transformação de coordenadas regulares)
            if self.vertexList.snapPoint is not None:
                curPoint = QgsPoint(self.vertexList.snapPoint)
            elif self.vertexList.snapSegment is not None:
                curPoint = self.vertexList.snapSegment[0]
            else:
                curPoint = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates( event.pos() )

            curPoint = self._constrain(curPoint)
            self.vertexList.updateCurrentPoint(curPoint)


            # Um modo perpendicular ou paralelo
	    
            if event.type() == QEvent.MouseButtonPress or event.type() == QEvent.MouseButtonRelease:
                #B2a. Modo de entrada de imprensão do mouse
                modifiedEvent = QMouseEvent( event.type(), self._toPixels(curPoint), event.button(), event.buttons(), event.modifiers() )
                QCoreApplication.sendEvent(obj,modifiedEvent)
                
            else:
                #B2B. Modo de entrada de movimento do mouse
                modifiedEvent = QMouseEvent( event.type(), self._toPixels(curPoint), event.button(), event.buttons(), event.modifiers() )
                QCoreApplication.sendEvent(obj,modifiedEvent)

	    # No modo de entrada (B), registramos os últimos pontos para seguir o cálculo relativo em caso de mousePress
	    if event.type() == QEvent.MouseButtonRelease:
		self.vertexList.newPoint()

            
            # Ao retornar True, informamos ao eventSystem que o evento não deve ser enviado mais (desde que um novo evento tenha sido enviado por meio de QCoreApplication)
            return True

        # KEYPRESS
        elif event.type() == QEvent.KeyPress:
            # remove último ponto
            if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
                self.vertexList.removeLastPoint()
                return False
            # Se inputWidget interceptou o evento, isso será True (evento não propagado ainda)
            return event.isAccepted()

        # CLIQUE DIREITO
        elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.RightButton:
            # cancelar a digitalização ao clicar com o botão direito
            self.vertexList.empty()
            self.vertexList.snapSegment = None # segmento quebrado na posição atual (se houver)
            self.vertexList.snapPoint = None # ponto encaixado na posição atual (se houver)
            QCoreApplication.sendEvent(obj,event)
            return True

        # DE OUTRA FORMA
        else:
            # No caso de não gerenciarmos esse tipo de evento, retornamos a implementação normal
            return QObject.eventFilter(self, obj, event)


    ########################
    ##### CONSTRAINING #####
    ########################

    def _constrain(self, point):
        
        previousPoint = self.vertexList.previousPoint()
    
        dist, distAcum = None, None
	
        #################
        # Restrição de distância
        if len(self.vertexList)>1:
            
            dist = math.sqrt(point.sqrDist(previousPoint))
	    line = QgsGeometry.fromPolyline(self.vertexList)
	    distAcum = line.length()
	
        if dist != None and self.enableAction.isChecked():
            if self.combobox.currentText() == "Dist. vertice":
                QToolTip.showText(self.mapCanvas.mapToGlobal(self.mapCanvas.mouseLastXY()), str(dist), self.mapCanvas)
            elif self.combobox.currentText() == "Dist. total":
                QToolTip.showText(self.mapCanvas.mapToGlobal(self.mapCanvas.mouseLastXY()), str(distAcum), self.mapCanvas)
        else:
            QToolTip.hideText()

        return point
        

    #####################################
    ##### COORDINATE TRANSFORMATIONS ####
    #####################################

    def _toMapSnap(self, qpoint):
        """
        retorna o ponto instantâneo atual (se houver) e o segmento instantâneo atual (se houver) nas coordenadas do mapa
        O segmento instantâneo atual é retornado como (ponto de snap no segmento, startPoint, endPoint)
        """
        ok, snappingResults = self.snapper.snapPoint(qpoint, [])
        for result in snappingResults:
            if result.snappedVertexNr != -1:
                return QgsPoint(result.snappedVertex), None
        if len(snappingResults):
            output = (QgsPoint(snappingResults[0].snappedVertex), QgsPoint(snappingResults[0].beforeVertex), QgsPoint(snappingResults[0].afterVertex))
            return None, output
        else:
            return None, None

    def _toPixels(self, qgspoint):
        """
        Dado um ponto nas coordenadas do projeto, retorna um ponto nas coordenadas de tela (pixel)
        """
        try:
            p = self.iface.mapCanvas().getCoordinateTransform().transform( qgspoint )
            return QPoint( int(p.x()), int(p.y()) )
        except ValueError:
            # isso acontece às vezes no carregamento, parece que o mapCanvas não está pronto e retorna um ponto na NaN; NaN
            return QPoint()


