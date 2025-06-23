import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QGroupBox, QLabel, QSizePolicy
)
from PyQt5.QtGui import QFont
from interfaces.Single_ui import UniCycleInterface
from interfaces.Multi_ui import MultiCycleInterface
from interfaces.Segmented_ui import Pipeline1Interface
from interfaces.Forwarding_ui import Pipeline2Interface


class MainSimulatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de CPUs - Arquitectura RISC-V")
        self.setFixedSize(500, 400)

        self._fuente_titulo = QFont("Arial", 14, QFont.Bold)
        self._fuente_botones = QFont("Segoe UI", 11)

        self._inicializar_ui()

        # Ventanas hijas
        self.ventana_uniciclo = None
        self.ventana_multiciclo = None
        self.ventana_pipeline1 = None
        self.ventana_pipeline2 = None

    def _inicializar_ui(self):
        self.widget_central = QWidget()
        self.setCentralWidget(self.widget_central)

        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)
        self.widget_central.setLayout(layout_principal)


        grupo_opciones = QGroupBox("")
        layout_botones = QVBoxLayout()
        layout_botones.setSpacing(12)

        # Botones de selección
        self.btn_uniciclo = QPushButton("Uniciclo")
        self.btn_multiciclo = QPushButton("Multiciclo")
        self.btn_pipeline1 = QPushButton("Pipeline Básico")
        self.btn_pipeline2 = QPushButton("Pipeline con Forwarding")

        for btn in [self.btn_uniciclo, self.btn_multiciclo, self.btn_pipeline1, self.btn_pipeline2]:
            btn.setFont(self._fuente_botones)
            btn.setMinimumHeight(40)
            layout_botones.addWidget(btn)

        self.btn_uniciclo.clicked.connect(self.abrir_uniciclo)
        self.btn_multiciclo.clicked.connect(self.abrir_multiciclo)
        self.btn_pipeline1.clicked.connect(self.abrir_pipeline1)
        self.btn_pipeline2.clicked.connect(self.abrir_pipeline2)

        grupo_opciones.setLayout(layout_botones)
        layout_principal.addWidget(grupo_opciones)

    # --- Métodos para abrir interfaces específicas ---
    def abrir_uniciclo(self):
        if not self.ventana_uniciclo:
            self.ventana_uniciclo = UniCycleInterface()
        self.ventana_uniciclo.show()

    def abrir_multiciclo(self):
        if not self.ventana_multiciclo:
            self.ventana_multiciclo = MultiCycleInterface()
        self.ventana_multiciclo.show()

    def abrir_pipeline1(self):
        if not self.ventana_pipeline1:
            self.ventana_pipeline1 = Pipeline1Interface()
        self.ventana_pipeline1.show()

    def abrir_pipeline2(self):
        if not self.ventana_pipeline2:
            self.ventana_pipeline2 = Pipeline2Interface()
        self.ventana_pipeline2.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainSimulatorWindow()
    ventana.show()
    sys.exit(app.exec_())
