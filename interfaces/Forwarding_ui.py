from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QTextEdit, QGroupBox, QGridLayout, QSizePolicy, QTableWidget, QTableWidgetItem
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer
import time
from ForwardingPipeline import ForwardingPipeline


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
        self._aplicar_estilos()

    def _aplicar_estilos(self):
        # Colores personalizados
        fondo_general = "#F5F0CD"
        fondo_secundario = "#578FCA"
        encabezado = "#3674B5"
        acento = "#FADA7A"

        # Fondo general de la ventana
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {fondo_general};
            }}
            QGroupBox {{
                background-color: {fondo_secundario};
                font-weight: bold;
                border: 2px solid {encabezado};
                border-radius: 8px;
                margin-top: 10px;
            }}
            QGroupBox:title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: white;
                background-color: {encabezado};
            }}
            QPushButton {{
                background-color: {encabezado};
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {acento};
                color: black;
            }}
            QLabel {{
                font-weight: bold;
            }}
            QTextEdit {{
                background-color: white;
                border: 1px solid gray;
                border-radius: 5px;
            }}
            QSpinBox {{
                background-color: white;
                border-radius: 5px;
            }}
        """)

    def _configurar_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout_principal = QVBoxLayout()
        self.central_widget.setLayout(self.layout_principal)

        self._crear_seccion_controles()
        self._crear_etapas_pipeline()
        self._crear_consola_mensajes()
        self._crear_seccion_tiempo()
        self._crear_seccion_metricas()

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

        nombres = ["Fetch", "Decode", "Execute", "Memory", "WriteBack"]
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

    def _crear_seccion_metricas(self):
        box = QGroupBox("Métricas de Ejecución (Últimas 10)")
        layout = QVBoxLayout()

        self.tabla_metricas = QTableWidget(10, 3)  # 10 filas, 3 columnas
        self.tabla_metricas.setHorizontalHeaderLabels(["CPI", "Ciclos", "Instrucciones"])
        self.tabla_metricas.verticalHeader().setVisible(False)
        self.tabla_metricas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.addWidget(self.tabla_metricas)
        box.setLayout(layout)
        self.layout_principal.addWidget(box)

        self.historial_metricas = []

    # ----------------- Lógica -----------------

    def _iniciar_simulacion(self):
        delay_s = self.spin_delay.value() / 1000.0
        self.cpu = ForwardingPipeline(delay_s)
        self.cpu.statusSignal.connect(self._actualizar_etapas)

        self.cpu.initialize_pipeline()
        self.timer.start(self.spin_delay.value())
        self.inicio_tiempo = time.time()
        self.btn_iniciar.setEnabled(False)
        self.btn_detener.setEnabled(True)

    def _detener_simulacion(self):
        self.timer.stop()
        self.btn_iniciar.setEnabled(True)
        self.btn_detener.setEnabled(False)
        self._actualizar_tiempo()
        total_inst = self.cpu.total_inst
        total_ciclos = self.cpu.total_cycles
        cpi = total_ciclos / total_inst
        self._guardar_metricas(cpi, total_ciclos, total_inst)

    def _ejecutar_ciclo(self):
        if not self.cpu.advance_Fpipeline():
            self._detener_simulacion()
        self._actualizar_ui()

    def _ejecutar_paso(self):
        if not self.cpu.advance_Fpipeline():
            self.btn_paso.setEnabled(False)
        self._actualizar_ui()

    def _actualizar_ui(self):
        self.txt_mensajes.append(f"PC actual: {self.cpu.pc}")
        self._actualizar_tiempo()

    def _actualizar_etapas(self, mensaje):
        if ": " in mensaje:
            etapa, contenido = mensaje.split(": ", 1)
            if etapa in self.etapas:
                self.etapas[etapa].clear()
                self.etapas[etapa].append(contenido)

    def _actualizar_tiempo(self):
        if self.inicio_tiempo:
            transcurrido = time.time() - self.inicio_tiempo
            self.txt_tiempo.setPlainText(f"{transcurrido:.2f}")

    def _guardar_metricas(self, cpi, ciclos, instrucciones):
        if len(self.historial_metricas) >= 10:
            self.historial_metricas.pop(0)
        self.historial_metricas.append((round(cpi, 2), ciclos, instrucciones))
        self._actualizar_tabla_metricas()

    def _actualizar_tabla_metricas(self):
        self.tabla_metricas.clearContents()
        for fila, (cpi, ciclos, inst) in enumerate(self.historial_metricas):
            self.tabla_metricas.setItem(fila, 0, QTableWidgetItem(str(cpi)))
            self.tabla_metricas.setItem(fila, 1, QTableWidgetItem(str(ciclos)))
            self.tabla_metricas.setItem(fila, 2, QTableWidgetItem(str(inst)))