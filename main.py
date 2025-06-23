import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QGroupBox
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
        self.setFixedSize(950, 200)
        self.setStyleSheet("background-color: #3674B5;")  # Fondo principal

        self._fuente_titulo = QFont("Arial", 16, QFont.Bold)
        self._fuente_botones = QFont("Segoe UI", 13)

        self._inicializar_ui()

        self.ventana_uniciclo = None
        self.ventana_multiciclo = None
        self.ventana_pipeline1 = None
        self.ventana_pipeline2 = None

    def _inicializar_ui(self):
        self.widget_central = QWidget()
        self.setCentralWidget(self.widget_central)

        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(30)
        self.widget_central.setLayout(layout_principal)

        grupo_opciones = QGroupBox("")
        grupo_opciones.setStyleSheet("""
            QGroupBox {
                background-color: #F5F0CD;
                border: 2px solid #FADA7A;
                border-radius: 10px;
            }
        """)

        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(20)

        # Crear y aplicar estilo a los botones
        self.btn_uniciclo = self._crear_boton("Uniciclo")
        self.btn_multiciclo = self._crear_boton("Multiciclo")
        self.btn_pipeline1 = self._crear_boton("Pipeline Básico")
        self.btn_pipeline2 = self._crear_boton("Pipeline con Forwarding")

        for btn in [self.btn_uniciclo, self.btn_multiciclo, self.btn_pipeline1, self.btn_pipeline2]:
            layout_botones.addWidget(btn)

        self.btn_uniciclo.clicked.connect(self.abrir_uniciclo)
        self.btn_multiciclo.clicked.connect(self.abrir_multiciclo)
        self.btn_pipeline1.clicked.connect(self.abrir_pipeline1)
        self.btn_pipeline2.clicked.connect(self.abrir_pipeline2)

        grupo_opciones.setLayout(layout_botones)
        layout_principal.addWidget(grupo_opciones)

    def _crear_boton(self, texto):
        btn = QPushButton(texto)
        btn.setFont(self._fuente_botones)
        btn.setMinimumHeight(60)
        btn.setMinimumWidth(160)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #578FCA;
                color: #FFFFFF;
                border: 2px solid #FADA7A;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #FADA7A;
                color: #3674B5;
            }
        """)
        return btn

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
