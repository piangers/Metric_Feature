# -*- coding: utf-8 -*-


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import math


class EventFilter(QObject):
   
    def __init__(self, iface, pointList, enableAction, combobox, spinbox):
        QObject.__init__(self)
        self.iface = iface
        self.mapCanvas = iface.mapCanvas()
        self.pointList = pointList
        self.enableAction = enableAction
        self.combobox = combobox
        self.spinbox = spinbox
        # Tratamento para o plugin funcionar somente com a active layer
        self.active = False

    def close(self):
        pass

    
    ###################
    ##### EVENTOS #####
    ###################

    def eventFilter(self, obj, event):
        # Nós só executamos isso se o evento for espontâneo, significa que foi gerado pelo sistema operacional.
        # Desta forma, o evento que criamos abaixo não será processado (o que seria um loop inifinito)
        if not event.spontaneous():
            return QObject.eventFilter(self, obj, event)
            
        # MOVEU MOUSE OU CLICK ESQUERDO
        if ( (  (event.type() == QEvent.MouseMove and event.button() != Qt.MidButton) or
                (event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton) or
                (event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton) )
                and self.active == True ):
            curPoint = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates( event.pos() )
            curPoint = self.updateMeasure(curPoint)
            
            self.pointList.updateCurrentPoint(curPoint)

            # Modo de entrada do mouse
            modifiedEvent = QMouseEvent( event.type(), self.toPixels(curPoint), event.button(), event.buttons(), event.modifiers() )
            QCoreApplication.sendEvent(obj,modifiedEvent)
                
           
	    # No modo de entrada (B), registramos os últimos pontos para seguir o cálculo relativo em caso de mousePress
	    if event.type() == QEvent.MouseButtonRelease:
		    self.pointList.newPoint()   
            # Ao retornar True, informamos ao eventSystem que o evento não deve ser enviado mais (desde que um novo evento tenha sido enviado por meio de QCoreApplication)
            return True

        elif event.type() == QEvent.KeyPress:
            # remove último ponto
            if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
                self.pointList.removeLastPoint()
                return False
            # Se inputWidget interceptou o evento, isso será True (evento não propagado ainda)
            return event.isAccepted()

        # CLIQUE DIREITO
        elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.RightButton:
            # cancelar a digitalização ao clicar com o botão direito
            self.pointList.empty()
            QCoreApplication.sendEvent(obj,event)
            return True

        # DE OUTRA FORMA
        else:
            return QObject.eventFilter(self, obj, event)


    ###############################
    ##### ATUALIZANDO MEDIDAS #####
    ###############################

    def updateMeasure(self, point): 
        previousPoint = self.pointList.previousPoint()
        dist, distAcum = None, None
	
        #################
        # Restrição de distância
        if len(self.pointList)>1:
            dist = math.sqrt(point.sqrDist(previousPoint))

	    line = QgsGeometry.fromPolyline(self.pointList)
	    distAcum = line.length()
	
        if dist != None and self.enableAction.isChecked():
            if self.combobox.currentText() == "Dist. vertice":                
                # Configura a cor referente a distância Parcial
                color = 'red'
                if dist >= self.spinbox.value():
					color = 'green'
                txt = "<p style='background-color:{color}'><b>{distance}</b></p>".format(color=color, distance="%.2f" % dist)	
                # Configura a apresentação tooltip no mouse	 
                QToolTip.showText(self.mapCanvas.mapToGlobal(self.mapCanvas.mouseLastXY()), txt, self.mapCanvas)

            elif self.combobox.currentText() == "Dist. total":
                # Configura a cor referente a distância Total
                color = 'red'
                if distAcum >= self.spinbox.value():
					color = 'green'
                txt = "<p style='background-color:{color}'><b>{distance}</b></p>".format(color=color, distance="%.2f" % distAcum)	
                # Configura a apresentação tooltip no mouse				 
                QToolTip.showText(self.mapCanvas.mapToGlobal(self.mapCanvas.mouseLastXY()), txt, self.mapCanvas)
        else:
            QToolTip.hideText()

        return point
        
    #######################################
    ##### TRANSFORMAÇÃO DE COORDENADAS ####
    #######################################

    def toPixels(self, qgspoint):
        """
        Dado um ponto nas coordenadas do projeto, retorna um ponto nas coordenadas de tela (pixel)
        """
        try:
            p = self.iface.mapCanvas().getCoordinateTransform().transform( qgspoint )
            return QPoint( int(p.x()), int(p.y()) )
        except ValueError:
            # isso acontece às vezes no carregamento, parece que o mapCanvas não está pronto e retorna um ponto na NaN
            return QPoint()


