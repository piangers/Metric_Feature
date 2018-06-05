# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import resources_rc

from EventFilter import EventFilter
from VertexList import VertexList


class Metric(QObject):

    def __init__(self, iface):
        QObject.__init__(self)
        self.iface = iface

    def initGui(self):
        # Criar ação de ativação
	self.enableAction = QAction( QIcon(":/plugins/cadinput/icon.png"), u"Ativar medidas", self.iface.mainWindow())
	self.enableAction.setCheckable(True)

        ### CÓDIGO NOVO ###
        self.comboBox = QComboBox(self.iface.mainWindow())

        # Create combobox and add items.
        self.comboBox.setGeometry(QRect(40, 40, 491, 31))
        self.comboBox.setObjectName(("comboBox"))
        self.comboBox.addItem(u"Dist. total")
        self.comboBox.addItem(u"Dist. vertice")
        self.comboBox.setToolTip(u"Opção para medição")
        
        # 2 - CONECTAR O CLIQUE DO BOTÃO COM UM MÉTODO ("SLOT")
        # self.spinBox.valueChanged.connect(self.setTolerancia)
       
        #Padrões fixados
        self.spinBox = QDoubleSpinBox(self.iface.mainWindow())
        self.spinBox.setDecimals(1)
        self.spinBox.setMinimum(125)
        self.spinBox.setMaximum(5000.000)
        self.spinBox.setSingleStep(0.100)
        self.tolerancia = self.spinBox.value()
        self.spinBox.setToolTip("Tolerancia")
        
        self.enableAction.toggled.connect(self.enableElements)
        self.enableElements(False)

        # VertexList: isso armazena todos os pontos
	self.vertexList = VertexList()

        # EventFilter: este widget filtrará os mouseEvents e os restringirá, se necessário
        self.eventFilter = EventFilter(self.iface, self.vertexList, self.enableAction, self.comboBox, self.spinBox)

        # Precisamos da janela de visualização da tela para rastrear o mouse para que mouseMoveEvents aconteça
        self.iface.mapCanvas().viewport().setMouseTracking(True)

        # Nós instalamos o eventFilter na viewport da tela para obter os eventos do mouse
        self.iface.mapCanvas().viewport().installEventFilter( self.eventFilter )

        # Nós instalamos o eventFilter na própria tela para obter os principais eventos
        self.iface.mapCanvas().installEventFilter( self.eventFilter )
        # Create combobox and add items.
        
        # Adicionar itens de menu e barras de ferramentas
	self.toolbar = self.iface.addToolBar(u'Comprimento de feição')
        self.toolbar.addAction(self.enableAction)
        # Adicionar o botão da barra de ferramentas e item de menu 
        self.toolbar.addWidget(self.comboBox)
        self.toolbar.addWidget(self.spinBox)
        

    def unload(self):
        # unload event filter
        self.eventFilter.close()
        self.iface.mapCanvas().viewport().removeEventFilter( self.eventFilter )
        self.iface.mapCanvas().removeEventFilter( self.eventFilter )

        # e remova o menu de itens
	self.toolbar.removeAction(self.enableAction)
        del self.toolbar

    def enableElements(self, b):
        self.spinBox.setEnabled(b)
        self.comboBox.setEnabled(b)
