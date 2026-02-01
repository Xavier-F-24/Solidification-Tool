import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QTabWidget, QLabel, QDoubleSpinBox, QGroupBox, QMessageBox
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# import your pipeline entry points
from solidification_tool.main import run_simulation, show_all


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Solidification Tool")

        self._central = QWidget()
        self.setCentralWidget(self._central)

        root = QHBoxLayout(self._central)

        # -------- Left panel (controls) --------
        left = QVBoxLayout()
        root.addLayout(left, 0)

        controls = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls)

        self.wanted_g = QDoubleSpinBox()
        self.wanted_g.setRange(1e-12, 1e12)
        self.wanted_g.setDecimals(6)
        self.wanted_g.setValue(1e5)
        self.wanted_g.setSingleStep(1e4)

        controls_layout.addWidget(QLabel("Wanted_G"))
        controls_layout.addWidget(self.wanted_g)

        self.run_btn = QPushButton("Run simulation")
        self.run_btn.clicked.connect(self.run_and_plot)
        controls_layout.addWidget(self.run_btn)

        left.addWidget(controls)
        left.addStretch(1)

        # -------- Right panel (plots) --------
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

    def clear_tabs(self):
        while self.tabs.count():
            w = self.tabs.widget(0)
            self.tabs.removeTab(0)
            w.deleteLater()

    def add_figures_as_tabs(self, fig_dict):
        """
        fig_dict: dict[str, list[Figure]]
        """
        for group_name, figs in fig_dict.items():
            for i, fig in enumerate(figs):
                canvas = FigureCanvas(fig)
                tab_name = group_name if len(figs) == 1 else f"{group_name} ({i+1})"
                self.tabs.addTab(canvas, tab_name)

    def run_and_plot(self):
        try:
            # Run compute
            results = run_simulation()

            # Build plots
            wanted_g = float(self.wanted_g.value())
            fig_dict = show_all(results, Wanted_G=wanted_g)

            # Refresh UI
            self.clear_tabs()
            self.add_figures_as_tabs(fig_dict)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1200, 700)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
