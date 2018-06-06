# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import resources_rc

from EventFilter import EventFilter
from PointList import PointList


class MeasureFeature(QObject):

    def __init__(self, iface):
        QObject.__init__(self)
        self.iface = iface

    def initGui(self):
        # Criar ação de ativação
		self.enableAction = QAction( QIcon(":/plugins/MeasureFeature/icon.png"), u"Ativar medidas", self.iface.mainWindow())
		self.enableAction.setCheckable(True)
        
        # Cria combobox e adiciona itens.
		self.comboBox = QComboBox(self.iface.mainWindow())
		self.comboBox.setGeometry(QRect(40, 40, 491, 31))
		self.comboBox.setObjectName(("comboBox"))
		self.comboBox.addItem(u"Dist. total")
		self.comboBox.addItem(u"Dist. vertice")
		self.comboBox.setToolTip(u"Opção para medição")

        #Padrões fixados
		self.spinBox = QDoubleSpinBox(self.iface.mainWindow())
		self.spinBox.setDecimals(1)
		self.spinBox.setMinimum(1250)
		self.spinBox.setMaximum(50000.000)
		self.spinBox.setSingleStep(0.100)
		self.tolerancia = self.spinBox.value()
		self.spinBox.setToolTip("Tolerancia") 
		self.enableAction.toggled.connect(self.enableElements)
		self.enableElements(False)

		# pointList: isso armazena todos os pontos
		self.pointList = PointList()

		# EventFilter: este widget filtrará os mouseEvents e os restringirá, se necessário
		self.eventFilter = EventFilter(self.iface, self.pointList, self.enableAction, self.comboBox, self.spinBox)

		# Precisamos da janela de visualização da tela para rastrear o mouse para que mouseMoveEvents aconteça
		self.iface.mapCanvas().viewport().setMouseTracking(True)

		# Nós instalamos o eventFilter na viewport da tela para obter os eventos do mouse
		self.iface.mapCanvas().viewport().installEventFilter( self.eventFilter )

		# Nós instalamos o eventFilter na própria tela para obter os principais eventos
		self.iface.mapCanvas().installEventFilter( self.eventFilter )

		# Adicionar itens de menu e barras de ferramentas
		self.toolbar = self.iface.addToolBar(u'Comprimento de feição')
		self.toolbar.addAction(self.enableAction)

		# Adicionar o botão da barra de ferramentas e item de menu 
		self.toolbar.addWidget(self.comboBox)
		self.toolbar.addWidget(self.spinBox)

		# SINAIS
        # Nós conectamos o sinal mapToolSet para que possamos ativar / desativar a widget
		self.iface.mapCanvas().mapToolSet.connect(self.maptoolChanged)

        # E nós o executamos para definir o estado correto após o carregamento
		self.maptoolChanged()

    def unload(self):
		# remove o event filter
		self.eventFilter.close()
		self.iface.mapCanvas().viewport().removeEventFilter( self.eventFilter )
		self.iface.mapCanvas().removeEventFilter( self.eventFilter )

		# e remova o menu de itens
		self.toolbar.removeAction(self.enableAction)
		del self.toolbar

        # e remova o sinal maptoolchanded isEditTool
		self.iface.mapCanvas().mapToolSet.disconnect( self.maptoolChanged )

    def enableElements(self, b):
        self.spinBox.setEnabled(b)
        self.comboBox.setEnabled(b)

    def maptoolChanged(self):
	    self.eventFilter.active = (self.iface.mapCanvas().mapTool() is not None and self.iface.mapCanvas().mapTool().isEditTool())
