from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QTextEdit, QGroupBox, QGridLayout, QSizePolicy, QTableWidget,
    QTableWidgetItem, QMessageBox
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap, QFont
import os
import time
from multiciclo import MultiCycleCPU


class MultiCycleInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multiciclo - Simulador CPU RISC-V")
        self.setFixedSize(950, 700)

        self.cpu = MultiCycleCPU()
        self.cpu.messageChanged.connect(self._mostrar_mensajes)

        self.temporizador = QTimer()
        self.temporizador.timeout.connect(self._ejecutar_ciclo)

        self.historial = []
        self._fuente_mono = QFont("Courier New", 9)

        self._configurar_ui()

    def _configurar_ui(self):
        self.widget_central = QWidget()
        self.setCentralWidget(self.widget_central)
        self.layout_principal = QVBoxLayout(self.widget_central)
        self.layout_principal.setContentsMargins(10, 10, 10, 10)
        self.layout_principal.setSpacing(12)

        self._crear_controles()
        self._crear_vistas_estado()
        self._crear_tabla_historial()

    def _crear_controles(self):
        box = QGroupBox("Controles de Simulación")
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Retardo (ms):"))
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(0, 100)
        self.spin_delay.setValue(30)
        layout.addWidget(self.spin_delay)

        layout.addWidget(QLabel("Datos a mostrar:"))
        self.spin_memoria = QSpinBox()
        self.spin_memoria.setRange(1, 1024)
        self.spin_memoria.setValue(27)
        layout.addWidget(self.spin_memoria)

        self.btn_iniciar = QPushButton("▶ Iniciar")
        self.btn_iniciar.clicked.connect(self._iniciar_simulacion)
        layout.addWidget(self.btn_iniciar)

        self.btn_detener = QPushButton("⏹ Detener")
        self.btn_detener.clicked.connect(self._detener_simulacion)
        self.btn_detener.setEnabled(False)
        layout.addWidget(self.btn_detener)

        self.btn_paso = QPushButton("⏭ Paso")
        self.btn_paso.clicked.connect(self._paso_manual)
        layout.addWidget(self.btn_paso)

        self.btn_reiniciar = QPushButton("🔄 Reiniciar")
        self.btn_reiniciar.clicked.connect(self._reiniciar)
        layout.addWidget(self.btn_reiniciar)

        self.btn_volver = QPushButton("↩ Volver")
        self.btn_volver.clicked.connect(self.close)
        layout.addWidget(self.btn_volver)

        box.setLayout(layout)
        self.layout_principal.addWidget(box)

    def _crear_vistas_estado(self):
        grid = QGridLayout()

        self._vista_pc = self._crear_textbox("Contador de Programa (PC)", grid, 0, 0)
        self._vista_fsm = self._crear_textbox("Estado de la FSM", grid, 0, 1)
        self._vista_memoria = self._crear_textbox("Memoria", grid, 1, 0)
        self._vista_registros = self._crear_textbox("Registros", grid, 1, 1)

        self._vista_fsm.setFixedHeight(70)
        self._vista_pc.setFixedHeight(70)



        box = QGroupBox("Estado Actual del Procesador")
        box.setLayout(grid)
        self.layout_principal.addWidget(box)

    def _crear_textbox(self, titulo, grid, fila, columna):
        etiqueta = QLabel(titulo)
        textbox = QTextEdit()
        textbox.setReadOnly(True)
        textbox.setFont(self._fuente_mono)
        textbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid.addWidget(etiqueta, fila * 2, columna)
        grid.addWidget(textbox, fila * 2 + 1, columna)
        return textbox

    def _crear_tabla_historial(self):
        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["Tipo", "Ciclos", "Duración"])
        self.tabla.setFixedHeight(150)
        self.tabla.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        box = QGroupBox("Historial de Ejecuciones")
        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        box.setLayout(layout)
        self.layout_principal.addWidget(box)

    # ----------- Lógica de ejecución -----------

    def _iniciar_simulacion(self):
        self.cpu.reset()
        self.temporizador.start(self.spin_delay.value() * 10)
        self.cpu.start_time = time.time()
        self.btn_iniciar.setEnabled(False)
        self.btn_detener.setEnabled(True)
        self.btn_paso.setEnabled(False)

    def _detener_simulacion(self):
        self.temporizador.stop()
        self.btn_iniciar.setEnabled(True)
        self.btn_detener.setEnabled(False)
        self.btn_paso.setEnabled(True)

    def _ejecutar_ciclo(self):
        if not self.cpu.run_cycle():
            self._detener_simulacion()
        self._actualizar_vistas()

    def _paso_manual(self):
        if not self.cpu.run_cycle():
            self.btn_paso.setEnabled(False)
        self._actualizar_vistas()

    def _reiniciar(self):
        self.cpu.reset()
        self.btn_paso.setEnabled(True)
        self._actualizar_vistas()

    def _mostrar_mensajes(self, mensaje):
        self._vista_pc.append(mensaje)
        self._vista_fsm.append(mensaje)
        self._vista_registros.append(mensaje)
        self._vista_memoria.append(mensaje)

    def _actualizar_vistas(self):
        tiempo = time.time() - self.cpu.start_time if self.cpu.start_time else 0

        self._vista_pc.setPlainText(f"PC: {self.cpu.PC}")
        self._vista_fsm.setPlainText(f"FSM: {self.cpu.state}")
        self._vista_registros.setPlainText(str(self.cpu.registers))

        n = self.spin_memoria.value()
        self._vista_memoria.setPlainText(str(self.cpu.data_memory[:n]))


        self._registrar_historial("Multiciclo", self.cpu.PC, tiempo)

    def _registrar_historial(self, tipo, ciclos, duracion):
        if len(self.historial) >= 5:
            self.historial.pop(0)
            self.tabla.removeRow(0)

        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)
        self.tabla.setItem(fila, 0, QTableWidgetItem(tipo))
        self.tabla.setItem(fila, 1, QTableWidgetItem(str(ciclos)))
        self.tabla.setItem(fila, 2, QTableWidgetItem(f"{duracion:.2f}s"))

        self.historial.append((tipo, ciclos, duracion))
