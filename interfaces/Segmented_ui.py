from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QTextEdit, QGroupBox, QGridLayout, QSizePolicy, QTableWidget, QTableWidgetItem
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer
import time
from Segmented import SegmentedProcessor


class Pipeline1Interface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Básico - Simulador RISC-V")
        self.setFixedSize(900, 740)

        self.cpu = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._ejecutar_ciclo)
        self.inicio_tiempo = None
        self.fuente_mono = QFont("Courier New", 9)
        self.ciclo_actual = 0

        self._configurar_ui()
        self._aplicar_estilos()

    def _aplicar_estilos(self):
        fondo = "#F5F0CD"
        encabezado = "#3674B5"
        secundario = "#578FCA"
        acento = "#FADA7A"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {fondo};
            }}
            QGroupBox {{
                background-color: {secundario};
                font-weight: bold;
                border: 2px solid {encabezado};
                border-radius: 8px;
                margin-top: 10px;
            }}
            QGroupBox:title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
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
        self._crear_seccion_etapas()
        self._crear_consola_mensajes()
        self._crear_seccion_metricas()
        self._crear_panel_info()

    def _crear_seccion_controles(self):
        box = QGroupBox("Controles del Pipeline")
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

        self.label_tiempo = QLabel("Tiempo: 0.00s")
        layout.addWidget(self.label_tiempo)

        box.setLayout(layout)
        self.layout_principal.addWidget(box)


    def _crear_seccion_etapas(self):
        box = QGroupBox("Etapas del Pipeline")
        grid = QGridLayout()
        self.etapas = {}

        nombres = ["Fetch", "Decode", "Execute", "Memory", "WriteBack"]
        for i, nombre in enumerate(nombres):
            etiqueta = QLabel(nombre)
            area = QTextEdit()
            area.setReadOnly(True)
            area.setFont(self.fuente_mono)
            area.setFixedHeight(35)
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
        self.txt_mensajes.setFixedHeight(35)

        box.setLayout(layout)
        self.layout_principal.addWidget(box)

    def _crear_seccion_tiempo(self):
        box = QGroupBox("Duración de la Simulación")
        layout = QHBoxLayout()

        self.label_tiempo = QLabel("Tiempo (s):")
        self.txt_tiempo = QTextEdit()
        self.txt_tiempo.setReadOnly(True)
        self.txt_tiempo.setFont(self.fuente_mono)
        self.txt_tiempo.setFixedWidth(100)
        self.txt_tiempo.setFixedHeight(20)

        layout.addWidget(self.label_tiempo)
        layout.addWidget(self.txt_tiempo)
        box.setLayout(layout)

        self.layout_principal.addWidget(box)

    def _crear_seccion_metricas(self):
        box = QGroupBox("Métricas de Ejecución (Últimas 10)")
        layout = QVBoxLayout()

        self.tabla_metricas = QTableWidget(10, 3)  # 3 métricas
        self.tabla_metricas.setFixedHeight(100)
        self.tabla_metricas.setHorizontalHeaderLabels(["CPI", "Ciclos", "Instrucciones"])
        self.tabla_metricas.verticalHeader().setVisible(False)

        self.tabla_metricas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.tabla_metricas)


        box.setLayout(layout)
        self.layout_principal.addWidget(box)

        # Historial en memoria
        self.historial_metricas = []

    def _crear_panel_info(self):
        box = QGroupBox("Información en Tiempo Real")
        layout = QVBoxLayout()

        self.label_ciclo = QLabel("Ciclo actual: 0")
        layout.addWidget(self.label_ciclo)

        # Instrucciones por etapa
        self.label_etapas = QLabel("Instrucciones en cada etapa:")
        layout.addWidget(self.label_etapas)
        self.text_etapas = QTextEdit()
        self.text_etapas.setReadOnly(True)
        layout.addWidget(self.text_etapas)
        self.text_etapas.setFixedHeight(75)

        # Memoria de datos
        self.label_mem = QLabel("Contenido actual de memoria de datos:")
        layout.addWidget(self.label_mem)
        self.text_memoria = QTextEdit()
        self.text_memoria.setReadOnly(True)
        layout.addWidget(self.text_memoria)
        self.text_memoria.setFixedHeight(75)

        box.setLayout(layout)
        self.layout_principal.addWidget(box)

    # ----------------- Lógica -----------------

    def _iniciar_simulacion(self):
        delay_segundos = self.spin_delay.value() / 1000.0
        self.cpu = SegmentedProcessor(delay_segundos)
        self.cpu.statusSignal.connect(self._actualizar_etapas)

        self.cpu.initialize()
        self.timer.start(self.spin_delay.value())
        self.inicio_tiempo = time.time()
        self.btn_iniciar.setEnabled(False)
        self.btn_detener.setEnabled(True)

    def _detener_simulacion(self):
        self.timer.stop()
        self.btn_iniciar.setEnabled(True)
        self.btn_detener.setEnabled(False)
        self._actualizar_tiempo()
        # Calcular y guardar métricas
        total_inst = self.cpu.total_instructions
        total_ciclos = self.cpu.total_cycles
        cpi = total_ciclos / total_inst
        self._guardar_metricas(cpi, total_ciclos, total_inst)

    def _ejecutar_ciclo(self):
        if not self.cpu.advance_pipeline():
            self._detener_simulacion()
        self._actualizar_monitor()
        self.ciclo_actual += 1
        self.label_ciclo.setText(f"Ciclo actual: {self.ciclo_actual}")

    def _ejecutar_paso(self):
        if not self.cpu.advance_pipeline():
            self.btn_paso.setEnabled(False)
        self._actualizar_monitor()
        self.ciclo_actual += 1
        self.label_ciclo.setText(f"Ciclo actual: {self.ciclo_actual}")

    def _actualizar_monitor(self):
        self.txt_mensajes.append(f"PC actual: {self.cpu.pc}")
        self._actualizar_tiempo()

        # Mostrar instrucciones en cada etapa (reconstrucción basada en los registros intermedios)
        instrucciones = []

        # Etapas tradicionales mapeadas desde los registros
        etapas_mapeo = {
            "IF": self.cpu.stages.get("IF_ID", {}).get("IR"),
            "ID": self.cpu.stages.get("ID_EX", {}).get("IR"),
            "EX": self.cpu.stages.get("EX_MEM", {}).get("IR"),
            "MEM": self.cpu.stages.get("MEM_WB", {}).get("IR"),
            "WB": self.cpu.stages.get("MEM_WB", {}).get("IR")  # WB usa también MEM_WB
        }

        for etapa, ir in etapas_mapeo.items():
            texto = f"{etapa}: {str(ir) if ir else '—'}"
            instrucciones.append(texto)
        self.text_etapas.setText("\n".join(instrucciones))

        # Mostrar contenido de la memoria de datos
        contenido = ""
        for i, val in enumerate(self.cpu.data_mem[:64]):
            if val != 0:
                contenido += f"mem[{i}] = {val}\n"
        self.text_memoria.setText(contenido if contenido else "(memoria vacía)")

    def _actualizar_etapas(self, mensaje):
        if ": " in mensaje:
            etapa, contenido = mensaje.split(": ", 1)
            if etapa in self.etapas:
                self.etapas[etapa].clear()
                self.etapas[etapa].append(contenido)

    def _actualizar_tiempo(self):
        if self.inicio_tiempo:
            transcurrido = time.time() - self.inicio_tiempo
            self.label_tiempo.setText(f"Tiempo: {transcurrido:.2f}s")

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