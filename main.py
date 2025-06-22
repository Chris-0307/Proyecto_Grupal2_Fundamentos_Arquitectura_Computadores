import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget, QTextEdit, QHBoxLayout, QSpinBox
from PyQt5.QtCore import QTimer
from pipeline1 import SegmentedCPU1
from pipeline2 import SegmentedCPU2


class PipelineCPUWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline CPU Simulator")
        self.setFixedSize(800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        delay_layout = QHBoxLayout()
        self.delay_label = QLabel("Delay (ms):")
        delay_layout.addWidget(self.delay_label)
        self.delay_spinbox = QSpinBox(self)
        self.delay_spinbox.setRange(0, 1000)
        self.delay_spinbox.setValue(100)
        delay_layout.addWidget(self.delay_spinbox)
        layout.addLayout(delay_layout)

        self.start_button = QPushButton("Start Simulation")
        self.start_button.clicked.connect(self.start_simulation)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Simulation")
        self.stop_button.clicked.connect(self.stop_simulation)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        self.step_button = QPushButton("Step-by-Step Execution")
        self.step_button.clicked.connect(self.run_step)
        layout.addWidget(self.step_button)

        self.return_button = QPushButton("Return")
        self.return_button.clicked.connect(self.close)
        layout.addWidget(self.return_button)

        self.fetched_text = QTextEdit()
        self.decoded_text = QTextEdit()
        self.executed_text = QTextEdit()
        self.memory_access_text = QTextEdit()
        self.write_back_text = QTextEdit()
        for label, box in [
            ("Fetched", self.fetched_text),
            ("Decoded", self.decoded_text),
            ("Executed", self.executed_text),
            ("Memory Access", self.memory_access_text),
            ("Write Back", self.write_back_text)
        ]:
            layout.addWidget(QLabel(label))
            box.setReadOnly(True)
            layout.addWidget(box)

        self.messages_text = QTextEdit()
        self.messages_text.setReadOnly(True)
        layout.addWidget(self.messages_text)

        self.execution_time_label = QLabel("Execution Time (s):")
        layout.addWidget(self.execution_time_label)
        self.execution_time_text = QTextEdit()
        self.execution_time_text.setReadOnly(True)
        layout.addWidget(self.execution_time_text)

        self.timer = QTimer()
        self.timer.timeout.connect(self.run_cycle)
        self.cpu = None
        self.start_time = None

    def start_simulation(self):
        cycle_time = self.delay_spinbox.value() / 1000.0
        self.cpu = SegmentedCPU1(cycle_time)
        self.cpu.messageChanged.connect(self.update_messages)
        self.reset()
        self.timer.start(self.delay_spinbox.value())
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.start_time = time.time()

    def stop_simulation(self):
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_execution_time()

    def run_cycle(self):
        if not self.cpu.run_cycle():
            self.stop_simulation()
        self.update_ui()

    def run_step(self):
        if not self.cpu.run_cycle():
            self.step_button.setEnabled(False)
        self.update_ui()

    def reset(self):
        if self.cpu:
            self.cpu.reset()
            self.update_ui()

    def update_ui(self):
        self.messages_text.append(f"PC: {self.cpu.PC}")
        self.update_execution_time()

    def update_messages(self, message):
        parts = message.split(': ')
        if len(parts) == 2:
            category, content = parts
            mapping = {
                "Fetched": self.fetched_text,
                "Decoded": self.decoded_text,
                "Executed": self.executed_text,
                "Memory Access": self.memory_access_text,
                "Write Back": self.write_back_text
            }
            if category in mapping:
                mapping[category].clear()
                mapping[category].append(content)

    def update_execution_time(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.execution_time_text.setPlainText(f"{elapsed:.2f}")


class Pipeline2CPUWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline2 CPU Simulator")
        self.setFixedSize(800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        delay_layout = QHBoxLayout()
        self.delay_label = QLabel("Delay (ms):")
        delay_layout.addWidget(self.delay_label)
        self.delay_spinbox = QSpinBox(self)
        self.delay_spinbox.setRange(0, 1000)
        self.delay_spinbox.setValue(100)
        delay_layout.addWidget(self.delay_spinbox)
        layout.addLayout(delay_layout)

        self.start_button = QPushButton("Start Simulation")
        self.start_button.clicked.connect(self.start_simulation)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Simulation")
        self.stop_button.clicked.connect(self.stop_simulation)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        self.step_button = QPushButton("Step-by-Step Execution")
        self.step_button.clicked.connect(self.run_step)
        layout.addWidget(self.step_button)

        self.return_button = QPushButton("Return")
        self.return_button.clicked.connect(self.close)
        layout.addWidget(self.return_button)

        self.fetched_text = QTextEdit()
        self.decoded_text = QTextEdit()
        self.executed_text = QTextEdit()
        self.memory_access_text = QTextEdit()
        self.write_back_text = QTextEdit()
        for label, box in [
            ("Fetched", self.fetched_text),
            ("Decoded", self.decoded_text),
            ("Executed", self.executed_text),
            ("Memory Access", self.memory_access_text),
            ("Write Back", self.write_back_text)
        ]:
            layout.addWidget(QLabel(label))
            box.setReadOnly(True)
            layout.addWidget(box)

        self.messages_text = QTextEdit()
        self.messages_text.setReadOnly(True)
        layout.addWidget(self.messages_text)

        self.execution_time_label = QLabel("Execution Time (s):")
        layout.addWidget(self.execution_time_label)
        self.execution_time_text = QTextEdit()
        self.execution_time_text.setReadOnly(True)
        layout.addWidget(self.execution_time_text)

        self.timer = QTimer()
        self.timer.timeout.connect(self.run_cycle)
        self.cpu = None
        self.start_time = None

    def start_simulation(self):
        cycle_time = self.delay_spinbox.value() / 1000.0
        self.cpu = SegmentedCPU2(cycle_time)
        self.cpu.messageChanged.connect(self.update_messages)
        self.reset()
        self.timer.start(self.delay_spinbox.value())
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.start_time = time.time()

    def stop_simulation(self):
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_execution_time()

    def run_cycle(self):
        if not self.cpu.run_cycle():
            self.stop_simulation()
        self.update_ui()

    def run_step(self):
        if not self.cpu.run_cycle():
            self.step_button.setEnabled(False)
        self.update_ui()

    def reset(self):
        if self.cpu:
            self.cpu.reset()
            self.update_ui()

    def update_ui(self):
        self.messages_text.append(f"PC: {self.cpu.PC}")
        self.update_execution_time()

    def update_messages(self, message):
        parts = message.split(': ')
        if len(parts) == 2:
            category, content = parts
            mapping = {
                "Fetched": self.fetched_text,
                "Decoded": self.decoded_text,
                "Executed": self.executed_text,
                "Memory Access": self.memory_access_text,
                "Write Back": self.write_back_text
            }
            if category in mapping:
                mapping[category].clear()
                mapping[category].append(content)

    def update_execution_time(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.execution_time_text.setPlainText(f"{elapsed:.2f}")


class CPUWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Procesador Segmentado")
        self.setFixedSize(600, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        self.pipeline_button = QPushButton("Interfaz Pipeline 1")
        self.pipeline_button.clicked.connect(self.show_pipeline_interface)
        layout.addWidget(self.pipeline_button)

        self.pipeline2_button = QPushButton("Interfaz Pipeline 2")
        self.pipeline2_button.clicked.connect(self.show_pipeline2_interface)
        layout.addWidget(self.pipeline2_button)

        self.pipeline_window = None
        self.pipeline2_window = None

    def show_pipeline_interface(self):
        if self.pipeline_window is None:
            self.pipeline_window = PipelineCPUWindow()
        self.pipeline_window.show()

    def show_pipeline2_interface(self):
        if self.pipeline2_window is None:
            self.pipeline2_window = Pipeline2CPUWindow()
        self.pipeline2_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CPUWindow()
    window.show()
    sys.exit(app.exec_())
