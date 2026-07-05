import sys
import os
import traceback
from dataclasses import fields, is_dataclass
from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QTabWidget,
    QLabel,
    QDoubleSpinBox,
    QGroupBox,
    QMessageBox,
    QCheckBox,
    QFormLayout,
    QLineEdit,
    QScrollArea,
    QFileDialog,
    QComboBox,
    QToolBox,
    QTextBrowser,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from solidification_tool.core.inputs import SolidificationInputs
from solidification_tool.core.defaults import get_inputs
from solidification_tool.core.engine import run_simulation
from solidification_tool.visualization.figures import show_all

# Persistence
from solidification_tool.io_utils.results_io import save_results, load_results


# -------------------------
# Helpers
# -------------------------

def _parse_float_list(text: str) -> list[float]:
    """Accepts: '1,2,3' or '1 2 3' or '1, 2, 3'."""
    s = text.strip()
    if not s:
        return []
    s = s.replace(",", " ")
    parts = [p for p in s.split() if p]
    return [float(p) for p in parts]


def _list_to_text(xs: list[float]) -> str:
    return ", ".join(f"{x:g}" for x in xs)


def _safe_set_pixmap(label: QLabel, path: str, height: int = 220):
    """Load a pixmap if available; otherwise hide the label."""
    if not path or not os.path.exists(path):
        label.setVisible(False)
        return
    pm = QPixmap(path)
    if pm.isNull():
        label.setVisible(False)
        return
    label.setPixmap(pm.scaledToHeight(height, Qt.SmoothTransformation))
    label.setAlignment(Qt.AlignCenter)


# -------------------------
# Pages
# -------------------------

class WelcomePage(QWidget):
    go_inputs = Signal()
    go_compute = Signal()

    def __init__(self, banner_path: str | None = None):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("Solidifying It")
        title.setStyleSheet("font-size: 30px; font-weight: 800;")
        subtitle = QLabel("Directional solidification toolkit: heat → IMS → PDAS/SDAS → CET")
        subtitle.setStyleSheet("font-size: 14px; color: #666;")

        banner = QLabel()
        _safe_set_pixmap(banner, banner_path or "")

        quick = QLabel(
            "Quick start:\n"
            "  1) Set your constants on Inputs\n"
            "  2) Run the coupled model on Compute + Plot\n"
            "  3) Use Replot to change plot styling without recompute\n"
        )
        quick.setStyleSheet("font-size: 13px;")

        # Big action buttons
        btn_row = QHBoxLayout()
        self.btn_inputs = QPushButton("Set Inputs")
        self.btn_inputs.setMinimumHeight(44)
        self.btn_inputs.clicked.connect(self.go_inputs.emit)

        self.btn_compute = QPushButton("Compute + Plot")
        self.btn_compute.setMinimumHeight(44)
        self.btn_compute.clicked.connect(self.go_compute.emit)

        btn_row.addWidget(self.btn_inputs)
        btn_row.addWidget(self.btn_compute)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(banner)
        layout.addSpacing(8)
        layout.addWidget(quick)
        layout.addSpacing(12)
        layout.addLayout(btn_row)
        layout.addStretch(1)


class HelpPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)

        browser.setHtml(
            """
            <h2>Help & Support</h2>
            <h3>Model Overview</h3>
            <ul>
              <li><b>Heat transfer</b>: produces V and G for the imposed thermal condition.</li>
              <li><b>IMS stability</b>: finds stability boundaries and undercooling behavior.</li>
              <li><b>PDAS/SDAS</b>: spacing correlations vs. stability limits.</li>
              <li><b>CET</b>: columnar-to-equiaxed transition estimate.</li>
            </ul>
            <h3>Troubleshooting</h3>
            <ul>
              <li><b>Run disabled</b>: check Inputs page for list length mismatch or parse errors.</li>
              <li><b>Plots empty</b>: ensure the simulation completed; try Run again and check console.</li>
              <li><b>Replot does nothing</b>: replot only affects plot settings, not the simulation results.</li>
            </ul>
            <h3>Units</h3>
            <ul>
              <li>G: K/m</li>
              <li>V: m/s</li>
              <li>D: m²/s</li>
            </ul>
            """
        )

        layout.addWidget(browser, 1)


class InputsPage(QWidget):
    """Editor for SolidificationInputs with presets + sectioned layout."""

    inputs_changed = Signal()

    def __init__(self):
        super().__init__()
        self._widgets: dict[str, QWidget] = {}

        root = QVBoxLayout(self)

        # ---- Top row: presets + defaults + validation ----
        top = QHBoxLayout()

        top.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Default (get_inputs)",
            "Quick demo (scaled-down)",
            "Custom",
        ])
        self.preset_combo.currentIndexChanged.connect(self.apply_preset)
        top.addWidget(self.preset_combo)

        self.btn_load_defaults = QPushButton("Load defaults")
        self.btn_load_defaults.clicked.connect(self.load_defaults)
        top.addWidget(self.btn_load_defaults)

        top.addStretch(1)

        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: #b00020;")
        top.addWidget(self.validation_label)

        root.addLayout(top)

        # ---- Scroll area with QToolBox sections ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        root.addWidget(scroll, 1)

        content = QWidget()
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)

        self.toolbox = QToolBox()
        content_layout.addWidget(self.toolbox)
        content_layout.addStretch(1)

        if not is_dataclass(SolidificationInputs):
            raise TypeError("SolidificationInputs must be a dataclass")

        # Heuristic grouping (edit as you learn what you want where)
        groups: dict[str, list[str]] = {
            "Heat Transfer": [
                "G_0",
                "nG",
                "V_0",
                "nV",
                "T_f",
                "k_l",
                "L",
                "rho",
                "c_p",
                "h",
            ],
            "Alloy / IMS": [
                "C_0",
                "C_f",
                "k",
                "m",
                "D",
                "Gamma",
                "d_0",
            ],
            "Spacing Laws": [
                "A_pdas",
                "b_pdas",
                "A_sdas",
                "b_sdas",
            ],
            "CET": [
                "G_crit",
                "V_crit",
                "phi_min",
                "phi_max",
                "nphi",
            ],
        }

        # Any leftover fields not explicitly listed
        all_fields = [f.name for f in fields(SolidificationInputs)]
        listed = {n for names in groups.values() for n in names}
        leftovers = [n for n in all_fields if n not in listed]
        if leftovers:
            groups["Other"] = leftovers

        # Build widgets into grouped pages
        for group_name, field_names in groups.items():
            page = QWidget()
            form = QFormLayout(page)
            form.setLabelAlignment(Qt.AlignRight)

            for name in field_names:
                f = next((ff for ff in fields(SolidificationInputs) if ff.name == name), None)
                if f is None:
                    continue

                anno = f.type

                # list-like
                if anno == list or str(anno).startswith("list"):
                    w = QLineEdit()
                    w.setPlaceholderText("comma-separated, e.g. 1.0, 2.0, 3.0")
                    w.textChanged.connect(self._on_any_change)
                    self._widgets[name] = w
                    form.addRow(QLabel(name), w)
                    continue

                spin = QDoubleSpinBox()
                spin.setDecimals(10)
                spin.setRange(-1e300, 1e300)
                spin.setSingleStep(1.0)
                spin.valueChanged.connect(self._on_any_change)
                self._widgets[name] = spin
                form.addRow(QLabel(name), spin)

            self.toolbox.addItem(page, group_name)

        # Load default inputs at startup
        self.load_defaults()

    def _on_any_change(self):
        self.validate()
        # If user edits anything, it's custom now
        if self.preset_combo.currentText() != "Custom":
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentText("Custom")
            self.preset_combo.blockSignals(False)
        self.inputs_changed.emit()

    def apply_preset(self):
        name = self.preset_combo.currentText()

        try:
            if name.startswith("Default"):
                self.set_inputs(get_inputs())
                return

            if name.startswith("Quick demo"):
                inp = get_inputs()
                # Gentle demo scaling (keeps numbers sane for first-time UI)
                inp.G_0 = float(getattr(inp, "G_0", 1e5))
                inp.V_0 = float(getattr(inp, "V_0", 1e-3))
                self.set_inputs(inp)
                return

            # Custom: do nothing
        except Exception as e:
            QMessageBox.critical(self, "Preset Error", str(e))

    def load_defaults(self):
        try:
            defaults = get_inputs()
            self.set_inputs(defaults)
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentText("Default (get_inputs)")
            self.preset_combo.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(self, "Load Defaults Error", str(e))

    def set_inputs(self, inputs: SolidificationInputs):
        for f in fields(SolidificationInputs):
            name = f.name
            if name not in self._widgets:
                continue
            val = getattr(inputs, name)
            w = self._widgets[name]
            if isinstance(w, QDoubleSpinBox):
                w.blockSignals(True)
                w.setValue(float(val))
                w.blockSignals(False)
            elif isinstance(w, QLineEdit):
                w.blockSignals(True)
                w.setText(_list_to_text(list(val)))
                w.blockSignals(False)
        self.validate()
        self.inputs_changed.emit()

    def get_inputs(self) -> SolidificationInputs:
        kwargs: dict[str, Any] = {}
        for f in fields(SolidificationInputs):
            name = f.name
            if name not in self._widgets:
                # If you add a field but didn't map it into a section, it lands in "Other".
                continue
            w = self._widgets[name]
            if isinstance(w, QDoubleSpinBox):
                kwargs[name] = float(w.value())
            elif isinstance(w, QLineEdit):
                kwargs[name] = _parse_float_list(w.text())
        return SolidificationInputs(**kwargs)

    def validate(self) -> bool:
        try:
            inputs = self.get_inputs()
        except Exception as e:
            self.validation_label.setText(f"Parse error: {e}")
            return False

        list_names = [n for n in ["C_0", "C_f", "k", "m", "D"] if hasattr(inputs, n)]
        lengths = {n: len(getattr(inputs, n)) for n in list_names}

        if any(lengths[n] == 0 for n in list_names):
            self.validation_label.setText("List inputs (C_0, C_f, k, m, D) must be non-empty.")
            return False

        if len(set(lengths.values())) > 1:
            msg = "List lengths must match: " + ", ".join(f"{n}={lengths[n]}" for n in list_names)
            self.validation_label.setText(msg)
            return False

        self.validation_label.setText("")
        return True


class ComputePlotPage(QWidget):
    """Compute + plot tab, now with Save/Load/Export and an Inputs Summary."""

    run_requested = Signal()
    replot_requested = Signal()
    save_run_requested = Signal()
    load_run_requested = Signal()
    export_figures_requested = Signal()

    def __init__(self):
        super().__init__()
        root = QHBoxLayout(self)

        # Left controls
        left = QVBoxLayout()
        root.addLayout(left, 0)

        # Inputs summary
        self.summary_box = QGroupBox("Inputs Summary")
        self.summary_layout = QVBoxLayout(self.summary_box)
        self.summary_label = QLabel("(no inputs loaded)")
        self.summary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.summary_layout.addWidget(self.summary_label)
        left.addWidget(self.summary_box)

        # Compute controls
        controls = QGroupBox("Compute + Plot")
        controls_layout = QVBoxLayout(controls)

        self.wanted_g = QDoubleSpinBox()
        self.wanted_g.setRange(1e-12, 1e12)
        self.wanted_g.setDecimals(6)
        self.wanted_g.setValue(1e5)
        self.wanted_g.setSingleStep(1e4)

        controls_layout.addWidget(QLabel("Wanted_G"))
        controls_layout.addWidget(self.wanted_g)

        self.run_btn = QPushButton("Run simulation")
        self.run_btn.clicked.connect(self.run_requested.emit)
        controls_layout.addWidget(self.run_btn)

        self.replot_btn = QPushButton("Replot (no recompute)")
        self.replot_btn.setEnabled(False)
        self.replot_btn.clicked.connect(self.replot_requested.emit)
        controls_layout.addWidget(self.replot_btn)

        self.status_label = QLabel("Ready")
        controls_layout.addWidget(self.status_label)

        # Toggles
        self.cb_show_pdas = QCheckBox("Show PDAS")
        self.cb_show_pdas.setChecked(True)
        controls_layout.addWidget(self.cb_show_pdas)

        self.cb_show_sdas = QCheckBox("Show SDAS")
        self.cb_show_sdas.setChecked(True)
        controls_layout.addWidget(self.cb_show_sdas)

        self.cb_ims_range = QCheckBox("IMS: plot G range")
        self.cb_ims_range.setChecked(False)
        controls_layout.addWidget(self.cb_ims_range)

        self.gmin = QDoubleSpinBox()
        self.gmin.setRange(1e-12, 1e12)
        self.gmin.setValue(1e3)
        controls_layout.addWidget(QLabel("G min"))
        controls_layout.addWidget(self.gmin)

        self.gmax = QDoubleSpinBox()
        self.gmax.setRange(1e-12, 1e12)
        self.gmax.setValue(1e7)
        controls_layout.addWidget(QLabel("G max"))
        controls_layout.addWidget(self.gmax)

        left.addWidget(controls)

        # Persistence buttons
        io_box = QGroupBox("Run I/O")
        io_layout = QVBoxLayout(io_box)

        self.btn_save_run = QPushButton("Save Run…")
        self.btn_save_run.clicked.connect(self.save_run_requested.emit)
        io_layout.addWidget(self.btn_save_run)

        self.btn_load_run = QPushButton("Load Run…")
        self.btn_load_run.clicked.connect(self.load_run_requested.emit)
        io_layout.addWidget(self.btn_load_run)

        self.btn_export_figs = QPushButton("Export Figures…")
        self.btn_export_figs.clicked.connect(self.export_figures_requested.emit)
        io_layout.addWidget(self.btn_export_figs)

        left.addWidget(io_box)
        left.addStretch(1)

        # Right plot tabs
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # Wiring for “replot when values change”
        self.wanted_g.editingFinished.connect(self.replot_requested.emit)
        self.cb_show_pdas.stateChanged.connect(self.replot_requested.emit)
        self.cb_show_sdas.stateChanged.connect(self.replot_requested.emit)
        self.cb_ims_range.stateChanged.connect(self._toggle_g_range)
        self.cb_ims_range.stateChanged.connect(self.replot_requested.emit)
        self.gmin.editingFinished.connect(self.replot_requested.emit)
        self.gmax.editingFinished.connect(self.replot_requested.emit)

        self._toggle_g_range()

    def _toggle_g_range(self):
        on = self.cb_ims_range.isChecked()
        self.gmin.setEnabled(on)
        self.gmax.setEnabled(on)

    def set_inputs_summary(self, inputs: SolidificationInputs):
        # Small curated snapshot. Expand as you like.
        lines = []
        for key in ["T_f", "k_l", "L", "rho", "c_p", "h"]:
            if hasattr(inputs, key):
                lines.append(f"{key}: {getattr(inputs, key)}")
        # IMS lists
        for key in ["C_0", "C_f", "k", "m", "D"]:
            if hasattr(inputs, key):
                val = getattr(inputs, key)
                try:
                    lines.append(f"{key}: [{', '.join(f'{x:g}' for x in val)}]")
                except Exception:
                    lines.append(f"{key}: {val}")
        self.summary_label.setText("\n".join(lines) if lines else "(inputs loaded)")

    def clear_tabs(self):
        while self.tabs.count():
            widget = self.tabs.widget(0)
            if hasattr(widget, "figure"):
                plt.close(widget.figure)
            self.tabs.removeTab(0)
            widget.deleteLater()

    def add_figures_as_tabs(self, fig_dict):
        for group_name, figs in fig_dict.items():
            for i, fig in enumerate(figs):
                canvas = FigureCanvas(fig)
                tab_name = group_name if len(figs) == 1 else f"{group_name} ({i+1})"
                self.tabs.addTab(canvas, tab_name)

                if group_name == "pdas_sdas":
                    self._attach_cursor_annotation(canvas)

    def _attach_cursor_annotation(self, canvas, fmt="G={g:.2e}\nV={v:.2e}"):
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
            ann.xy = (event.xdata, event.ydata)
            ann.set_text(fmt.format(g=event.xdata, v=event.ydata))
            ann.set_visible(True)
            canvas.draw_idle()

        canvas.mpl_connect("motion_notify_event", on_move)

    def get_plot_settings(self) -> dict[str, Any]:
        wanted_g = float(self.wanted_g.value())
        show_pdas = self.cb_show_pdas.isChecked()
        show_sdas = self.cb_show_sdas.isChecked()

        if self.cb_ims_range.isChecked():
            g_range = (float(self.gmin.value()), float(self.gmax.value()))
        else:
            g_range = []

        return dict(
            Wanted_G=wanted_g,
            show_pdas=show_pdas,
            show_sdas=show_sdas,
            ims_g_range=g_range,
        )


# -------------------------
# Thread worker
# -------------------------

class SimulationWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, inputs: SolidificationInputs, wanted_g: float):
        super().__init__()
        self.inputs = inputs
        self.wanted_g = wanted_g

    @Slot()
    def run(self):
        try:
            # Run compute only; plotting stays on UI thread.
            results = run_simulation(self.inputs, Wanted_G=self.wanted_g)
            self.finished.emit(results)
        except Exception:
            self.error.emit(traceback.format_exc())


# -------------------------
# Main window
# -------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Solidification Tool")

        self._latest_results = None
        self._thread = None
        self._worker = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.pages = QTabWidget()
        layout.addWidget(self.pages, 1)

        # NOTE: put your generated banner here
        self.welcome_page = WelcomePage(banner_path="assets/welcome_bg.png")
        self.inputs_page = InputsPage()
        self.compute_page = ComputePlotPage()
        self.help_page = HelpPage()

        self.pages.addTab(self.welcome_page, "Welcome")
        self.pages.addTab(self.inputs_page, "Inputs")
        self.pages.addTab(self.compute_page, "Compute + Plot")
        self.pages.addTab(self.help_page, "Help")

        # Guided flow buttons
        self.welcome_page.go_inputs.connect(lambda: self.pages.setCurrentIndex(1))
        self.welcome_page.go_compute.connect(lambda: self.pages.setCurrentIndex(2))

        # Wire compute controls
        self.compute_page.run_requested.connect(self.start_simulation_thread)
        self.compute_page.replot_requested.connect(self.replot_only)
        self.compute_page.save_run_requested.connect(self.save_run_dialog)
        self.compute_page.load_run_requested.connect(self.load_run_dialog)
        self.compute_page.export_figures_requested.connect(self.export_figures_dialog)

        # Keep Compute Run button disabled if inputs invalid
        self.inputs_page.inputs_changed.connect(self._sync_run_enabled)
        self.inputs_page.inputs_changed.connect(self._sync_inputs_summary)
        self._sync_run_enabled()
        self._sync_inputs_summary()

        self.statusBar().showMessage("Ready")

    def _sync_inputs_summary(self):
        try:
            self.compute_page.set_inputs_summary(self.inputs_page.get_inputs())
        except Exception:
            pass

    def _sync_run_enabled(self):
        ok = self.inputs_page.validate()
        self.compute_page.run_btn.setEnabled(ok)
        self.welcome_page.btn_compute.setEnabled(ok)

    # --------- Run / plot flow ---------

    def start_simulation_thread(self):
        if not self.inputs_page.validate():
            QMessageBox.warning(self, "Inputs invalid", "Fix Inputs page errors before running.")
            return

        inputs = self.inputs_page.get_inputs()
        wanted_g = float(self.compute_page.wanted_g.value())

        self.compute_page.run_btn.setEnabled(False)
        self.compute_page.status_label.setText("Running simulation…")

        self._thread = QThread()
        self._worker = SimulationWorker(inputs, wanted_g)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self.on_simulation_finished)
        self._worker.error.connect(self.on_simulation_error)

        # cleanup
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._worker.error.connect(self._thread.quit)
        self._worker.error.connect(self._worker.deleteLater)

        self._thread.start()

    @Slot(object)
    def on_simulation_finished(self, results):
        self._latest_results = results
        self.compute_page.replot_btn.setEnabled(True)

        try:
            settings = self.compute_page.get_plot_settings()
            fig_dict = show_all(self._latest_results, **settings)
            self.compute_page.clear_tabs()
            self.compute_page.add_figures_as_tabs(fig_dict)
            self.compute_page.status_label.setText("Done")
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))
            self.compute_page.status_label.setText("Plot error")
        finally:
            self.compute_page.run_btn.setEnabled(True)

    @Slot(str)
    def on_simulation_error(self, tb_text):
        QMessageBox.critical(self, "Simulation Error", tb_text)
        self.compute_page.status_label.setText("Error")
        self.compute_page.run_btn.setEnabled(True)

    def replot_only(self):
        if self._latest_results is None:
            return
        try:
            settings = self.compute_page.get_plot_settings()
            fig_dict = show_all(self._latest_results, **settings)
            self.compute_page.clear_tabs()
            self.compute_page.add_figures_as_tabs(fig_dict)
            self.compute_page.status_label.setText("Replotted")
        except Exception as e:
            QMessageBox.critical(self, "Replot Error", str(e))
            self.compute_page.status_label.setText("Replot error")

    # --------- Save / Load / Export ---------

    def save_run_dialog(self):
        if self._latest_results is None:
            QMessageBox.information(self, "No run", "Run a simulation first.")
            return


        out_dir = QFileDialog.getExistingDirectory(self, "Choose folder to save run")
        if not out_dir:
            return

        try:
            save_results(self._latest_results, out_dir)
            self.statusBar().showMessage(f"Saved run to: {os.path.join(out_dir, 'run.npz')}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def load_run_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load run",
            "",
            "NPZ files (*.npz)"
        )
        if not path:
            return

        try:
            self._latest_results = load_results(path)
            self.compute_page.replot_btn.setEnabled(True)
            self.replot_only()
            self.compute_page.status_label.setText("Loaded")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))

    def export_figures_dialog(self):
        if self._latest_results is None:
            QMessageBox.information(self, "No run", "Run a simulation first.")
            return

        out_dir = QFileDialog.getExistingDirectory(self, "Choose export folder")
        if not out_dir:
            return

        try:
            settings = self.compute_page.get_plot_settings()
            fig_dict = show_all(self._latest_results, **settings)

            for group, figs in fig_dict.items():
                for i, fig in enumerate(figs):
                    suffix = "" if len(figs) == 1 else f"_{i+1}"
                    fig.savefig(os.path.join(out_dir, f"{group}{suffix}.png"), dpi=300, bbox_inches="tight")

            self.statusBar().showMessage(f"Exported figures to: {out_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1280, 760)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
