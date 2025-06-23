from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget, QTextEdit,
    QSpinBox, QHBoxLayout, QGridLayout, QGroupBox, QSizePolicy
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
import time
from uniciclo import UniCycleCPU


class UniCycleInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulación Uniciclo - CPU RISC-V")
        self.setFixedSize(900, 650)

        fuente_mono = QFont("Courier New")
        fuente_mono.setPointSize(10)

        self.cpu = None
        self.inicio_tiempo = None
        self.temporizador = QTimer()
        self.temporizador.timeout.connect(self.ejecutar_ciclo)

        # --- Layout Principal
        self.widget_central = QWidget()
        self.setCentralWidget(self.widget_central)
        self.layout_general = QVBoxLayout()
        self.layout_general.setContentsMargins(15, 15, 15, 15)
        self.layout_general.setSpacing(10)
        self.widget_central.setLayout(self.layout_general)

        self._crear_controles_superiores()
        self._crear_seccion_etapas(fuente_mono)
        self._crear_seccion_mensajes(fuente_mono)
        self._crear_seccion_tiempo(fuente_mono)

    def _crear_controles_superiores(self):
        box = QGroupBox("Controles de Simulación")
        layout = QHBoxLayout()

        # Retardo
        layout.addWidget(QLabel("Retardo (ms):"))
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(0, 1000)
        self.delay_spinbox.setValue(100)
        layout.addWidget(self.delay_spinbox)

        # Botones
        self.btn_iniciar = QPushButton("▶ Iniciar")
        self.btn_iniciar.clicked.connect(self.iniciar_simulacion)
        layout.addWidget(self.btn_iniciar)

        self.btn_detener = QPushButton("⏹ Detener")
        self.btn_detener.clicked.connect(self.detener_simulacion)
        self.btn_detener.setEnabled(False)
        layout.addWidget(self.btn_detener)

        self.btn_paso = QPushButton("⏭ Paso")
        self.btn_paso.clicked.connect(self.ejecutar_paso)
        layout.addWidget(self.btn_paso)

        self.btn_volver = QPushButton("↩ Menú")
        self.btn_volver.clicked.connect(self.close)
        layout.addWidget(self.btn_volver)

        box.setLayout(layout)
        self.layout_general.addWidget(box)

    def _crear_seccion_etapas(self, fuente):
        box = QGroupBox("Etapas del Pipeline")
        grid = QGridLayout()
        self.secciones = {}

        nombres = ["Fetched", "Decoded", "Executed", "Memory Access", "Write Back"]
        for i, nombre in enumerate(nombres):
            etiqueta = QLabel(nombre)
            area = QTextEdit()
            area.setFont(fuente)
            area.setReadOnly(True)
            area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            area.setFixedHeight(60)
            grid.addWidget(etiqueta, i, 0)
            grid.addWidget(area, i, 1)
            self.secciones[nombre] = area

        box.setLayout(grid)
        self.layout_general.addWidget(box)

    def _crear_seccion_mensajes(self, fuente):
        box = QGroupBox("Consola de Mensajes")
        layout = QVBoxLayout()

        self.texto_mensajes = QTextEdit()
        self.texto_mensajes.setFont(fuente)
        self.texto_mensajes.setReadOnly(True)
        layout.addWidget(self.texto_mensajes)

        box.setLayout(layout)
        self.layout_general.addWidget(box)

    def _crear_seccion_tiempo(self, fuente):
        box = QGroupBox("Duración Total")
        layout = QHBoxLayout()

        self.label_tiempo = QLabel("Tiempo de Ejecución (s):")
        layout.addWidget(self.label_tiempo)

        self.texto_tiempo = QTextEdit()
        self.texto_tiempo.setFont(fuente)
        self.texto_tiempo.setReadOnly(True)
        self.texto_tiempo.setFixedHeight(30)
        self.texto_tiempo.setFixedWidth(100)
        layout.addWidget(self.texto_tiempo)

        box.setLayout(layout)
        self.layout_general.addWidget(box)

    # ----------------- Lógica -----------------

    def iniciar_simulacion(self):
        retardo = self.delay_spinbox.value() / 1000.0
        self.cpu = UniCycleCPU(retardo)
        self.cpu.messageChanged.connect(self.actualizar_etapas)
        self.reiniciar_cpu()

        self.temporizador.start(self.delay_spinbox.value())
        self.inicio_tiempo = time.time()
        self.btn_iniciar.setEnabled(False)
        self.btn_detener.setEnabled(True)

    def detener_simulacion(self):
        self.temporizador.stop()
        self.btn_iniciar.setEnabled(True)
        self.btn_detener.setEnabled(False)
        self.actualizar_tiempo()

    def ejecutar_ciclo(self):
        if not self.cpu.run_cycle():
            self.detener_simulacion()
        self.actualizar_info()

    def ejecutar_paso(self):
        if not self.cpu.run_cycle():
            self.btn_paso.setEnabled(False)
        self.actualizar_info()

    def reiniciar_cpu(self):
        if self.cpu:
            self.cpu.reset()
            self.actualizar_info()

    def actualizar_info(self):
        self.texto_mensajes.append(f"PC actual: {self.cpu.PC}")
        self.actualizar_tiempo()

    def actualizar_etapas(self, mensaje):
        partes = mensaje.split(': ')
        if len(partes) == 2:
            etapa, contenido = partes
            if etapa in self.secciones:
                self.secciones[etapa].clear()
                self.secciones[etapa].append(contenido)

    def actualizar_tiempo(self):
        if self.inicio_tiempo:
            transcurrido = time.time() - self.inicio_tiempo
            self.texto_tiempo.setPlainText(f"{transcurrido:.2f}")
