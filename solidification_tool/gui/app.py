
import sys
import traceback

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QTabWidget, QLabel, QDoubleSpinBox, QGroupBox, QMessageBox , QCheckBox
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

# import your pipeline entry points
from solidification_tool.main import run_simulation, show_all


class SimulationWorker(QObject):
    """
    Worker that runs heavy computation off the UI thread.
    IMPORTANT: Do NOT touch Qt widgets in here.
    """
    finished = Signal(object)   # will emit SimulationResults (or whatever your results type is)
    error = Signal(str)

    def __init__(self):
        super().__init__()

    @Slot()
    def run(self):
        try:
            results = run_simulation()
            self.finished.emit(results)
        except Exception:
            # send full traceback as text (super useful for debugging)
            self.error.emit(traceback.format_exc())


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
        self.wanted_g.setRange(1e-6, 1e9)
        self.wanted_g.setDecimals(6)
        self.wanted_g.setValue(1e5)
        self.wanted_g.setSingleStep(1e4)

        controls_layout.addWidget(QLabel("Wanted_G"))
        controls_layout.addWidget(self.wanted_g)

        self.run_btn = QPushButton("Run simulation")
        self.run_btn.clicked.connect(self.start_simulation_thread)
        controls_layout.addWidget(self.run_btn)

        # little status readout (nice during threading)
        self.status_label = QLabel("Ready")
        controls_layout.addWidget(self.status_label)

        left.addWidget(controls)
        left.addStretch(1)

                # --- toggles ---
        self.cb_show_pdas = QCheckBox("Show PDAS")
        self.cb_show_pdas.setChecked(True)
        controls_layout.addWidget(self.cb_show_pdas)

        self.cb_show_sdas = QCheckBox("Show SDAS")
        self.cb_show_sdas.setChecked(True)
        controls_layout.addWidget(self.cb_show_sdas)

        # Replot button (no recompute)
        self.replot_btn = QPushButton("Replot (no recompute)")
        self.replot_btn.clicked.connect(self.replot_only)
        self.replot_btn.setEnabled(False)   # enabled after first run
        controls_layout.addWidget(self.replot_btn)

        self.wanted_g.editingFinished.connect(self.replot_only)

        self.cb_show_pdas.stateChanged.connect(self.replot_only)
        self.cb_show_sdas.stateChanged.connect(self.replot_only)

        # -------- Right panel (plots) --------
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # Thread bookkeeping
        self._thread = None
        self._worker = None
        self._latest_results = None

        self.statusBar().showMessage("Ready")

    def clear_tabs(self):
        while self.tabs.count():
            widget = self.tabs.widget(0)

            # If this widget is a Matplotlib canvas, close its figure
            if hasattr(widget, "figure"):
                plt.close(widget.figure)

            self.tabs.removeTab(0)
            widget.deleteLater()

    def add_figures_as_tabs(self, fig_dict):
        """
        fig_dict: dict[str, list[matplotlib.figure.Figure]]
        """
        for group_name, figs in fig_dict.items():
            for i, fig in enumerate(figs):
                canvas = FigureCanvas(fig)
                tab_name = group_name if len(figs) == 1 else f"{group_name} ({i+1})"
                self.tabs.addTab(canvas, tab_name)

                # Attach cursor readout for PDAS/SDAS plot
                if group_name == "pdas_sdas":
                    self.attach_cursor_readout(canvas, label_prefix="Stability: ")
                    self.attach_cursor_annotation(canvas)

    def replot_only(self):
        """
        Rebuild figures from the latest stored results.
        No simulation recompute.
        """
        if self._latest_results is None:
            return  # nothing to plot yet

        try:
            wanted_g = float(self.wanted_g.value())
            show_pdas = self.cb_show_pdas.isChecked()
            show_sdas = self.cb_show_sdas.isChecked()

            fig_dict = show_all(
                self._latest_results,
                Wanted_G=wanted_g,
                show_pdas=show_pdas,
                show_sdas=show_sdas
            )

            self.clear_tabs()
            self.add_figures_as_tabs(fig_dict)
            self.status_label.setText("Replotted")
        except Exception as e:
            QMessageBox.critical(self, "Replot Error", str(e))
            self.status_label.setText("Replot error")

    # ---------------- Cursor defs ----------------------
    
    def attach_cursor_readout(self, canvas, label_prefix=""):
        """
        Attach a mouse-move handler that updates the status bar with (x,y).
        """
        def on_move(event):
            if event.inaxes is None or event.xdata is None or event.ydata is None:
                self.statusBar().showMessage("Ready")
                return

            # log-log plots: xdata/ydata are already in data units
            g = event.xdata
            v = event.ydata
            self.statusBar().showMessage(
                f"{label_prefix}G={g:.3e} K/m, V={v:.3e} m/s"
            )

        canvas.mpl_connect("motion_notify_event", on_move)

    def attach_cursor_annotation(self, canvas, fmt="G={g:.2e}\nV={v:.2e}"):
        fig = canvas.figure
        ax = fig.axes[0] if fig.axes else None
        if ax is None:
            return

        ann = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="white", alpha=0.8),
            fontsize=9,
            visible=False,
        )

        def on_move(event):
            if event.inaxes != ax or event.xdata is None or event.ydata is None:
                ann.set_visible(False)
                canvas.draw_idle()
                return

            g = event.xdata
            v = event.ydata
            ann.xy = (g, v)
            ann.set_text(fmt.format(g=g, v=v))
            ann.set_visible(True)
            canvas.draw_idle()

        canvas.mpl_connect("motion_notify_event", on_move)

    # ---------------- Threaded workflow ----------------

    def start_simulation_thread(self):
        # prevent double-click launching multiple threads
        self.run_btn.setEnabled(False)
        self.status_label.setText("Running simulation...")

        # Create thread + worker
        self._thread = QThread()
        self._worker = SimulationWorker()
        self._worker.moveToThread(self._thread)

        # Wire signals
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self.on_simulation_finished)
        self._worker.error.connect(self.on_simulation_error)

        # Cleanup (important: avoid zombie threads)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._worker.error.connect(self._thread.quit)
        self._worker.error.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        # Start
        self._thread.start()

    @Slot(object)
    def on_simulation_finished(self, results):
        """
        Back on UI thread: safe to touch widgets, build figures, update tabs.
        """
        self._latest_results = results

        self.replot_btn.setEnabled(True)


        try:
            wanted_g = float(self.wanted_g.value())
            fig_dict = show_all(results, Wanted_G=wanted_g)

            self.clear_tabs()
            self.add_figures_as_tabs(fig_dict)

            self.status_label.setText("Done")
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))
            self.status_label.setText("Plot error")
        finally:
            self.run_btn.setEnabled(True)

    @Slot(str)
    def on_simulation_error(self, tb_text):
        """
        Back on UI thread: show error nicely.
        """
        QMessageBox.critical(self, "Simulation Error", tb_text)
        self.status_label.setText("Error")
        self.run_btn.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1200, 700)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


"""
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
        
        #fig_dict: dict[str, list[Figure]]
        
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
"""