from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QTextEdit, QGroupBox, QGridLayout, QSizePolicy
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer
import time
from pipeline2 import PipelineCPU2


class Pipeline2Interface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Avanzado - Con Forwarding")
        self.setFixedSize(900, 640)

        self.cpu = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._ejecutar_ciclo)
        self.inicio_tiempo = None
        self.fuente_mono = QFont("Courier New", 9)

        self._configurar_ui()

    def _configurar_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout_principal = QVBoxLayout()
        self.central_widget.setLayout(self.layout_principal)

        self._crear_seccion_controles()
        self._crear_etapas_pipeline()
        self._crear_consola_mensajes()
        self._crear_seccion_tiempo()

    def _crear_seccion_controles(self):
        box = QGroupBox("Controles de Simulación")
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Retardo (ms):"))
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(0, 1000)
        self.spin_delay.setValue(100)
        layout.addWidget(self.spin_delay)

        self.btn_iniciar = QPushButton("▶ Iniciar")
        self.btn_iniciar.clicked.connect(self._iniciar_simulacion)
        layout.addWidget(self.btn_iniciar)

        self.btn_detener = QPushButton("⏹ Detener")
        self.btn_detener.clicked.connect(self._detener_simulacion)
        self.btn_detener.setEnabled(False)
        layout.addWidget(self.btn_detener)

        self.btn_paso = QPushButton("⏭ Paso")
        self.btn_paso.clicked.connect(self._ejecutar_paso)
        layout.addWidget(self.btn_paso)

        self.btn_volver = QPushButton("↩ Volver")
        self.btn_volver.clicked.connect(self.close)
        layout.addWidget(self.btn_volver)

        box.setLayout(layout)
        self.layout_principal.addWidget(box)

    def _crear_etapas_pipeline(self):
        box = QGroupBox("Etapas del Pipeline con Forwarding")
        grid = QGridLayout()
        self.etapas = {}

        nombres = ["Fetched", "Decoded", "Executed", "Memory Access", "Write Back"]
        for i, nombre in enumerate(nombres):
            etiqueta = QLabel(nombre)
            area = QTextEdit()
            area.setReadOnly(True)
            area.setFont(self.fuente_mono)
            area.setFixedHeight(70)
            area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            grid.addWidget(etiqueta, i, 0)
            grid.addWidget(area, i, 1)
            self.etapas[nombre] = area

        box.setLayout(grid)
        self.layout_principal.addWidget(box)

    def _crear_consola_mensajes(self):
        box = QGroupBox("Consola de Mensajes")
        layout = QVBoxLayout()

        self.txt_mensajes = QTextEdit()
        self.txt_mensajes.setFont(self.fuente_mono)
        self.txt_mensajes.setReadOnly(True)
        layout.addWidget(self.txt_mensajes)

        box.setLayout(layout)
        self.layout_principal.addWidget(box)

    def _crear_seccion_tiempo(self):
        box = QGroupBox("Duración Total de la Simulación")
        layout = QHBoxLayout()

        self.label_tiempo = QLabel("Tiempo (s):")
        self.txt_tiempo = QTextEdit()
        self.txt_tiempo.setReadOnly(True)
        self.txt_tiempo.setFont(self.fuente_mono)
        self.txt_tiempo.setFixedHeight(30)
        self.txt_tiempo.setFixedWidth(100)

        layout.addWidget(self.label_tiempo)
        layout.addWidget(self.txt_tiempo)

        box.setLayout(layout)
        self.layout_principal.addWidget(box)

    # ----------------- Lógica -----------------

    def _iniciar_simulacion(self):
        duracion = self.spin_delay.value() / 1000.0
        self.cpu = PipelineCPU2(duracion)
        self.cpu.messageChanged.connect(self._actualizar_etapas)

        self.cpu.reset()
        self.timer.start(self.spin_delay.value())
        self.inicio_tiempo = time.time()
        self.btn_iniciar.setEnabled(False)
        self.btn_detener.setEnabled(True)

    def _detener_simulacion(self):
        self.timer.stop()
        self.btn_iniciar.setEnabled(True)
        self.btn_detener.setEnabled(False)
        self._actualizar_tiempo()

    def _ejecutar_ciclo(self):
        if not self.cpu.run_cycle():
            self._detener_simulacion()
        self._actualizar_ui()

    def _ejecutar_paso(self):
        if not self.cpu.run_cycle():
            self.btn_paso.setEnabled(False)
        self._actualizar_ui()

    def _actualizar_ui(self):
        self.txt_mensajes.append(f"PC actual: {self.cpu.PC}")
        self._actualizar_tiempo()

    def _actualizar_etapas(self, mensaje):
        if ": " in mensaje:
            categoria, contenido = mensaje.split(": ", 1)
            if categoria in self.etapas:
                self.etapas[categoria].clear()
                self.etapas[categoria].append(contenido)

    def _actualizar_tiempo(self):
        if self.inicio_tiempo:
            transcurrido = time.time() - self.inicio_tiempo
            self.txt_tiempo.setPlainText(f"{transcurrido:.2f}")
