import sys
import os
import sqlite3
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QStackedWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QStatusBar, QPushButton, QDialog,
    QFormLayout, QLineEdit, QComboBox, QTextEdit, QDateEdit, QMessageBox,
    QRadioButton, QButtonGroup, QSpinBox, QGroupBox, QHBoxLayout,
    QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import QDate
import win32print
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

# Icon paths must be defined before any class/function uses them
ICON_SVG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'Logo.svg'))
ICON_ICO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'Logo.ico'))

ZPL_TEMPLATE = """
CT~~CD,~CC^~CT~
^XA
~TA000
~JSN
^LT0
^MNW
^MTT
^PON
^PMN
^LH0,0
^JMA
^PR4,4
~SD30
^JUS
^LRN
^CI27
^PA0,1,1,0
^XZ
^XA
^MMT
^PW315
^LL150
^LS0
^BY2,3,87^FT78,128^BCN,,Y,N
^FH\\^FD>:{{SAMPLE_ID}}^FS
^PQ1,0,1,Y
^XZ
"""

def print_barcode(sample_id):
    zpl = ZPL_TEMPLATE.replace("{{SAMPLE_ID}}", sample_id)
    printer_name = win32print.GetDefaultPrinter()
    try:
        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Sample Label", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(hPrinter, zpl.encode())
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
        return True
    except Exception as e:
        print(f"Failed to print barcode for {sample_id}: {e}")
        return False

NAV_ITEMS = [
    "Dashboard",
    "Cohorts",
    "Samples",
    "Print Barcodes",
    "Lookup Sample",
    "Export/Import"
]

SAMPLE_TYPES = ["serum", "plasma", "peritoneal fluid", "whole blood"]

def get_db_path():
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    db_dir = os.path.join(exe_dir, 'db')
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, 'bloodlogger.db')
    # Find the template in the right place (PyInstaller or dev)
    if hasattr(sys, '_MEIPASS'):
        template_path = os.path.join(sys._MEIPASS, 'db', 'bloodlogger_template.db')
    else:
        template_path = os.path.join(db_dir, 'bloodlogger_template.db')
    # Only copy if db doesn't exist and template does
    if not os.path.exists(db_path):
        if os.path.exists(template_path):
            shutil.copy(template_path, db_path)
        else:
            raise RuntimeError(f"Template DB not found at {template_path}")
    return db_path

DB_PATH = get_db_path()

# Debug: Print DB path and samples table schema at startup
print(f"[DEBUG] Using database at: {DB_PATH}")
try:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='samples'")
        schema = cur.fetchone()
        print(f"[DEBUG] samples table schema: {schema[0] if schema else 'NOT FOUND'}")
except Exception as e:
    print(f"[DEBUG] Could not read schema: {e}")

class AddSampleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Sample")
        self.setMinimumWidth(350)
        layout = QFormLayout(self)

        self.sample_id = QLineEdit()
        self.experimenter = QLineEdit()
        self.collection_date = QDateEdit()
        self.collection_date.setCalendarPopup(True)
        self.collection_date.setDate(QDate.currentDate())
        self.sample_type = QComboBox()
        self.sample_type.addItems(SAMPLE_TYPES)
        self.time_point = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(60)

        layout.addRow("SampleID", self.sample_id)
        layout.addRow("Experimenter", self.experimenter)
        layout.addRow("Collection Date", self.collection_date)
        layout.addRow("Sample Type", self.sample_type)
        layout.addRow("Sample Time Point", self.time_point)
        layout.addRow("Notes", self.notes)

        self.submit_btn = QPushButton("Add Sample")
        self.submit_btn.clicked.connect(self.submit)
        layout.addRow(self.submit_btn)

        self.result = None

    def submit(self):
        data = {
            "SampleID": self.sample_id.text().strip(),
            "Experimenter": self.experimenter.text().strip(),
            "Collection Date": self.collection_date.date().toString("yyyy-MM-dd"),
            "Sample Type": self.sample_type.currentText(),
            "Sample Time Point": self.time_point.text().strip(),
            "Notes": self.notes.toPlainText().strip()
        }
        if not data["SampleID"] or not data["Experimenter"]:
            QMessageBox.warning(self, "Missing Data", "SampleID and Experimenter are required.")
            return
        # Save to database
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO samples (
                        cohort_id, animal_id, species, sex, notes, barcode_value, date_added
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        None,  # cohort_id is NULL for manual samples
                        data["SampleID"],
                        data["Sample Type"],  # store sample type in 'species' for now
                        data["Experimenter"], # store experimenter in 'sex' for now
                        data["Notes"],
                        data["SampleID"],  # barcode_value = SampleID for now
                        data["Collection Date"]
                    )
                )
                conn.commit()
            # Print barcode after saving
            if print_barcode(data["SampleID"]):
                QMessageBox.information(self, "Barcode Printed", f"Barcode for {data['SampleID']} sent to printer.")
            else:
                QMessageBox.warning(self, "Print Error", f"Failed to print barcode for {data['SampleID']}.")
            self.result = data
            self.accept()
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(self, "Database Error", f"Could not add sample: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

class BaseConfigWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.base_name = QLineEdit()
        self.base_name.setPlaceholderText("Base Name")
        self.num_samples = QSpinBox()
        self.num_samples.setMinimum(1)
        self.num_samples.setMaximum(10000)
        self.num_samples.setValue(1)
        self.start_number = QSpinBox()
        self.start_number.setMinimum(0)
        self.start_number.setMaximum(1000000)
        self.start_number.setValue(0)
        layout.addWidget(QLabel("Base Name:"))
        layout.addWidget(self.base_name)
        layout.addWidget(QLabel("# Samples:"))
        layout.addWidget(self.num_samples)
        layout.addWidget(QLabel("Start #:"))
        layout.addWidget(self.start_number)
        self.setLayout(layout)

    def get_config(self):
        return {
            "base_name": self.base_name.text().strip(),
            "num_samples": self.num_samples.value(),
            "start_number": self.start_number.value()
        }

class ManualSampleIDsDialog(QDialog):
    def __init__(self, num_samples, initial_ids=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Sample IDs")
        self.setMinimumWidth(300)
        self.ids = initial_ids if initial_ids and len(initial_ids) == num_samples else ["" for _ in range(num_samples)]
        layout = QVBoxLayout(self)
        self.fields = []
        for i in range(num_samples):
            field = QLineEdit()
            field.setText(self.ids[i])
            field.setPlaceholderText(f"Sample {i+1} ID")
            layout.addWidget(field)
            self.fields.append(field)
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        layout.addWidget(self.ok_btn)

    def get_ids(self):
        return [f.text().strip() for f in self.fields]

    def accept(self):
        ids = self.get_ids()
        if any(not id for id in ids):
            QMessageBox.warning(self, "Missing Data", "All Sample IDs must be filled in.")
            return
        if len(set(ids)) != len(ids):
            QMessageBox.warning(self, "Duplicate IDs", "Sample IDs must be unique.")
            return
        super().accept()

class CreateCohortDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Cohort")
        self.setMinimumWidth(400)
        self.base_widgets = []
        self.manual_ids = []
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.cohort_name = QLineEdit()
        self.num_samples = QSpinBox()
        self.num_samples.setMinimum(1)
        self.num_samples.setMaximum(10000)
        self.num_samples.setValue(1)
        self.experimenter = QLineEdit()
        self.collection_date = QDateEdit()
        self.collection_date.setCalendarPopup(True)
        self.collection_date.setDate(QDate.currentDate())
        self.sample_type = QComboBox()
        self.sample_type.addItems(SAMPLE_TYPES)
        self.time_point = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(60)
        form.addRow("Cohort Name", self.cohort_name)
        form.addRow("Number of Samples", self.num_samples)
        form.addRow("Experimenter", self.experimenter)
        form.addRow("Collection Date", self.collection_date)
        form.addRow("Sample Type", self.sample_type)
        form.addRow("Sample Time Point", self.time_point)
        form.addRow("Notes", self.notes)
        # Assignment mode
        self.auto_radio = QRadioButton("Automatic Assignment")
        self.manual_radio = QRadioButton("Manual Assignment")
        self.auto_radio.setChecked(True)
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.auto_radio)
        self.mode_group.addButton(self.manual_radio)
        mode_box = QHBoxLayout()
        mode_box.addWidget(self.auto_radio)
        mode_box.addWidget(self.manual_radio)
        form.addRow(QLabel("Assignment Mode"), QWidget())
        form.addRow(mode_box)
        layout.addLayout(form)
        # Automatic assignment section
        self.auto_group = QGroupBox("Automatic Sample Assignment")
        self.auto_layout = QVBoxLayout()
        self.bases_layout = QVBoxLayout()
        self.add_base_btn = QPushButton("Add Base")
        self.add_base_btn.clicked.connect(self.add_base_config)
        self.auto_layout.addWidget(self.add_base_btn)
        self.auto_layout.addLayout(self.bases_layout)
        self.auto_group.setLayout(self.auto_layout)
        layout.addWidget(self.auto_group)
        # Manual assignment section
        self.manual_group = QGroupBox("Manual Sample Assignment")
        self.manual_layout = QVBoxLayout()
        self.edit_ids_btn = QPushButton("Edit Sample IDs...")
        self.edit_ids_btn.clicked.connect(self.open_manual_ids_dialog)
        self.manual_layout.addWidget(self.edit_ids_btn)
        self.manual_group.setLayout(self.manual_layout)
        layout.addWidget(self.manual_group)
        # Preview
        self.preview_label = QLabel()
        layout.addWidget(self.preview_label)
        # Buttons
        self.submit_btn = QPushButton("Create Cohort")
        self.submit_btn.clicked.connect(self.submit)
        layout.addWidget(self.submit_btn)
        # Initial base config
        self.add_base_config()
        # Update preview on changes
        self.num_samples.valueChanged.connect(self.update_num_samples)
        self.auto_radio.toggled.connect(self.update_mode)
        self.manual_radio.toggled.connect(self.update_mode)
        self.update_mode()
        self.update_num_samples()

    def add_base_config(self):
        base_widget = BaseConfigWidget()
        base_widget.base_name.textChanged.connect(self.update_preview)
        base_widget.num_samples.valueChanged.connect(self.update_preview)
        base_widget.start_number.valueChanged.connect(self.update_preview)
        self.bases_layout.addWidget(base_widget)
        self.base_widgets.append(base_widget)
        self.update_preview()

    def remove_base_config(self, base_widget):
        self.bases_layout.removeWidget(base_widget)
        base_widget.setParent(None)
        self.base_widgets.remove(base_widget)
        self.update_preview()

    def open_manual_ids_dialog(self):
        n = self.num_samples.value()
        dlg = ManualSampleIDsDialog(n, self.manual_ids, self)
        if dlg.exec_():
            self.manual_ids = dlg.get_ids()
            self.update_preview()

    def update_num_samples(self):
        # If number of samples changes, reset manual IDs
        n = self.num_samples.value()
        if len(self.manual_ids) != n:
            self.manual_ids = ["" for _ in range(n)]
        self.update_preview()

    def update_mode(self):
        self.auto_group.setVisible(self.auto_radio.isChecked())
        self.manual_group.setVisible(self.manual_radio.isChecked())
        self.update_preview()

    def update_preview(self):
        if self.auto_radio.isChecked():
            ids = []
            for base in self.base_widgets:
                cfg = base.get_config()
                if not cfg["base_name"]:
                    continue
                for i in range(cfg["num_samples"]):
                    ids.append(f"{cfg['base_name']}{cfg['start_number']+i}")
            preview = ", ".join(ids[:10])
            if len(ids) > 10:
                preview += f" ... ({len(ids)} total)"
            self.preview_label.setText(f"Sample IDs: {preview}")
        elif self.manual_radio.isChecked():
            ids = self.manual_ids
            preview = ", ".join([id for id in ids if id][:10])
            if len(ids) > 10:
                preview += f" ... ({len(ids)} total)"
            self.preview_label.setText(f"Sample IDs: {preview}")
        else:
            self.preview_label.setText("")

    def submit(self):
        name = self.cohort_name.text().strip()
        total_samples = self.num_samples.value()
        experimenter = self.experimenter.text().strip()
        collection_date = self.collection_date.date().toString("yyyy-MM-dd")
        sample_type = self.sample_type.currentText()
        time_point = self.time_point.text().strip()
        notes = self.notes.toPlainText().strip()
        if not name:
            QMessageBox.warning(self, "Missing Data", "Cohort Name is required.")
            return
        if self.auto_radio.isChecked():
            sample_ids = []
            base_total = 0
            for base in self.base_widgets:
                cfg = base.get_config()
                if not cfg["base_name"]:
                    continue
                base_total += cfg["num_samples"]
                for i in range(cfg["num_samples"]):
                    sample_ids.append(f"{cfg['base_name']}{cfg['start_number']+i}")
            if not sample_ids:
                QMessageBox.warning(self, "Missing Data", "At least one base with samples is required.")
                return
            if base_total != total_samples:
                QMessageBox.critical(self, "Sample Count Mismatch", f"The sum of samples for all bases ({base_total}) does not match the total Number of Samples ({total_samples}). Please fix this and try again.")
                return
            self.result = {
                "name": name,
                "sample_ids": sample_ids,
                "experimenter": experimenter,
                "collection_date": collection_date,
                "sample_type": sample_type,
                "time_point": time_point,
                "notes": notes
            }
            self.accept()
        elif self.manual_radio.isChecked():
            ids = self.manual_ids
            if any(not id for id in ids):
                QMessageBox.warning(self, "Missing Data", "All Sample IDs must be filled in.")
                return
            if len(set(ids)) != len(ids):
                QMessageBox.warning(self, "Duplicate IDs", "Sample IDs must be unique.")
                return
            if len(ids) != total_samples:
                QMessageBox.critical(self, "Sample Count Mismatch", f"The number of entered Sample IDs ({len(ids)}) does not match the total Number of Samples ({total_samples}). Please fix this and try again.")
                return
            self.result = {
                "name": name,
                "sample_ids": ids,
                "experimenter": experimenter,
                "collection_date": collection_date,
                "sample_type": sample_type,
                "time_point": time_point,
                "notes": notes
            }
            self.accept()
        else:
            QMessageBox.information(self, "Assignment Mode", "Please select an assignment mode.")

class CohortSamplesDialog(QDialog):
    def __init__(self, cohort_name, samples, parent=None, main_window=None):
        super().__init__(parent)
        self.setWindowTitle(f"Samples in Cohort: {cohort_name}")
        self.setMinimumWidth(600)
        self.cohort_name = cohort_name
        self.main_window = main_window  # Reference to MainWindow for refreshing
        self.layout = QVBoxLayout(self)
        label = QLabel(f"<b>Cohort:</b> {cohort_name}")
        self.layout.addWidget(label)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Sample ID", "Sample Type", "Experimenter", "Collection Date", "Notes"
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        self.table.setSortingEnabled(True)
        self.table.cellDoubleClicked.connect(self.edit_sample)
        self.layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_selected_samples)
        btn_layout.addWidget(self.delete_btn)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        self.layout.addLayout(btn_layout)
        self.refresh_table(samples)
    def refresh_table(self, samples=None):
        if samples is None:
            # Query fresh samples for this cohort
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id FROM cohorts WHERE name = ?", (self.cohort_name,))
                result = cur.fetchone()
                if not result:
                    return
                cohort_id = result[0]
                cur.execute("""
                    SELECT animal_id, species, sex, date_added, notes
                    FROM samples WHERE cohort_id = ? ORDER BY id DESC
                """, (cohort_id,))
                samples = cur.fetchall()
        self.table.setRowCount(len(samples))
        for row_idx, row in enumerate(samples):
            for col_idx, value in enumerate(row):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value) if value is not None else ""))
        self.table.resizeColumnsToContents()
    def edit_sample(self, row, col):
        sample_id = self.table.item(row, 0).text()
        dlg = EditSampleDialog(sample_id, self)
        if dlg.exec_():
            self.refresh_table()
            if self.main_window:
                self.main_window.refresh_cohorts_table()
    def delete_selected_samples(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Delete Samples", "No samples selected.")
            return
        sample_ids = [self.table.item(row.row(), 0).text() for row in selected]
        msg = "Are you sure you want to delete the following samples?\n" + ", ".join(sample_ids)
        if QMessageBox.question(self, "Confirm Delete", msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                for sid in sample_ids:
                    cur.execute("DELETE FROM samples WHERE animal_id = ?", (sid,))
                conn.commit()
            self.refresh_table()
            if self.main_window:
                self.main_window.refresh_cohorts_table()

class EditSampleDialog(QDialog):
    def __init__(self, sample_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Sample: {sample_id}")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        # Fetch sample info
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT animal_id, species, sex, date_added, notes, cohort_id FROM samples WHERE animal_id = ?", (sample_id,))
            sample = cur.fetchone()
        if not sample:
            QMessageBox.critical(self, "Error", "Sample not found.")
            self.reject()
            return
        self.sample_id = QLineEdit(sample[0])
        self.sample_type = QComboBox()
        self.sample_type.addItems(SAMPLE_TYPES)
        if sample[1] in SAMPLE_TYPES:
            self.sample_type.setCurrentText(sample[1])
        self.experimenter = QLineEdit(sample[2])
        self.collection_date = QDateEdit()
        self.collection_date.setCalendarPopup(True)
        self.collection_date.setDate(QDate.fromString(sample[3], "yyyy-MM-dd"))
        self.notes = QTextEdit(sample[4] if sample[4] else "")
        self.notes.setFixedHeight(60)
        self.cohort_id = sample[5]
        layout.addRow("Sample ID", self.sample_id)
        layout.addRow("Sample Type", self.sample_type)
        layout.addRow("Experimenter", self.experimenter)
        layout.addRow("Collection Date", self.collection_date)
        layout.addRow("Notes", self.notes)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        self.setLayout(layout)
        self.original_id = sample[0]
        self.result = None
    def save(self):
        new_id = self.sample_id.text().strip()
        sample_type = self.sample_type.currentText()
        experimenter = self.experimenter.text().strip()
        collection_date = self.collection_date.date().toString("yyyy-MM-dd")
        notes = self.notes.toPlainText().strip()
        if not new_id or not experimenter:
            QMessageBox.warning(self, "Missing Data", "Sample ID and Experimenter are required.")
            return
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE samples SET animal_id=?, species=?, sex=?, notes=?, date_added=? WHERE animal_id=?
                    """,
                    (new_id, sample_type, experimenter, notes, collection_date, self.original_id)
                )
                conn.commit()
            self.result = new_id
            self.accept()
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(self, "Database Error", f"Could not update sample: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SampleLogger")
        self.setWindowIcon(QIcon(ICON_ICO_PATH))
        self.resize(1000, 600)
        self._init_ui()

    def _init_ui(self):
        self.stack = QStackedWidget()
        self.pages = {}
        # Dashboard page
        dashboard = QWidget()
        dash_layout = QVBoxLayout()
        dash_layout.addStretch()
        btn_font = QFont()
        btn_font.setPointSize(16)
        btn_font.setBold(True)
        btn_size = (300, 80)
        cohorts_btn = QPushButton("Cohorts")
        cohorts_btn.setFont(btn_font)
        cohorts_btn.setFixedSize(*btn_size)
        cohorts_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.pages["Cohorts"]))
        samples_btn = QPushButton("Samples")
        samples_btn.setFont(btn_font)
        samples_btn.setFixedSize(*btn_size)
        samples_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.pages["Samples"]))
        lookup_btn = QPushButton("Lookup Sample")
        lookup_btn.setFont(btn_font)
        lookup_btn.setFixedSize(*btn_size)
        lookup_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.pages["Lookup Sample"]))
        test_print_btn = QPushButton("Test Print")
        test_print_btn.setFont(btn_font)
        test_print_btn.setFixedSize(*btn_size)
        test_print_btn.clicked.connect(self.test_print_barcode)
        for btn in [cohorts_btn, samples_btn, lookup_btn, test_print_btn]:
            dash_layout.addWidget(btn, alignment=Qt.AlignHCenter)
            dash_layout.addSpacing(30)
        dash_layout.addStretch()
        dashboard.setLayout(dash_layout)
        self.stack.addWidget(dashboard)
        self.pages["Dashboard"] = dashboard
        # Other pages
        for name, create_func in [
            ("Cohorts", self._create_cohorts_page),
            ("Samples", self._create_samples_page),
            ("Lookup Sample", self._create_lookup_sample_page)
        ]:
            page = create_func()
            # Add back button
            back_btn = QPushButton("Back to Dashboard")
            back_btn.setFixedWidth(180)
            back_btn.clicked.connect(lambda _, n="Dashboard": self.stack.setCurrentWidget(self.pages[n]))
            page.layout().insertWidget(0, back_btn)
            self.stack.addWidget(page)
            self.pages[name] = page
        self.setCentralWidget(self.stack)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")
        self.stack.setCurrentWidget(self.pages["Dashboard"])

    def _create_samples_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel("<h2>Samples</h2>")
        layout.addWidget(label)
        self.samples_table = QTableWidget()
        self.samples_table.setColumnCount(5)
        self.samples_table.setHorizontalHeaderLabels([
            "Sample ID", "Sample Type", "Experimenter", "Collection Date", "Cohort Name"
        ])
        self.samples_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.samples_table.setSelectionMode(QTableWidget.MultiSelection)
        self.samples_table.setSortingEnabled(True)
        self.samples_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.samples_table.cellDoubleClicked.connect(self.open_sample_details_dialog)
        layout.addWidget(self.samples_table)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Sample")
        add_btn.clicked.connect(self.open_add_sample_dialog)
        btn_layout.addWidget(add_btn)
        print_btn = QPushButton("Print Barcode")
        print_btn.clicked.connect(self.print_selected_barcodes)
        btn_layout.addWidget(print_btn)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_selected_samples)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()
        page.setLayout(layout)
        self.refresh_samples_table()
        return page

    def print_selected_barcodes(self):
        selected = self.samples_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Print Barcodes", "No samples selected.")
            return
        sample_ids = [self.samples_table.item(row.row(), 0).text() for row in selected]
        for sid in sample_ids:
            print_barcode(sid)
        self.status.showMessage(f"Sent {len(sample_ids)} barcode(s) to printer.")

    def delete_selected_samples(self):
        selected = self.samples_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Delete Samples", "No samples selected.")
            return
        sample_ids = [self.samples_table.item(row.row(), 0).text() for row in selected]
        msg = "Are you sure you want to delete the following samples?\n" + ", ".join(sample_ids)
        if QMessageBox.question(self, "Confirm Delete", msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                for sid in sample_ids:
                    cur.execute("DELETE FROM samples WHERE animal_id = ?", (sid,))
                conn.commit()
            self.refresh_samples_table()
            self.status.showMessage(f"Deleted {len(sample_ids)} sample(s).")

    def _create_cohorts_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel("<h2>Cohorts</h2>")
        layout.addWidget(label)
        self.cohorts_table = QTableWidget()
        self.cohorts_table.setColumnCount(4)
        self.cohorts_table.setHorizontalHeaderLabels([
            "Cohort Name", "Experimenter", "Date Created", "# Samples"
        ])
        self.cohorts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cohorts_table.setSelectionMode(QTableWidget.MultiSelection)
        self.cohorts_table.setSortingEnabled(True)
        self.cohorts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cohorts_table.cellDoubleClicked.connect(self.open_cohort_samples_dialog)
        layout.addWidget(self.cohorts_table)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Create Cohort")
        add_btn.clicked.connect(self.open_create_cohort_dialog)
        btn_layout.addWidget(add_btn)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_selected_cohorts)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()
        page.setLayout(layout)
        self.refresh_cohorts_table()
        return page

    def view_cohort_samples(self):
        selected = self.cohorts_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "View Samples", "No cohort selected.")
            return
        row = selected[0].row()
        cohort_name = self.cohorts_table.item(row, 0).text()
        # Get cohort id by name
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM cohorts WHERE name = ?", (cohort_name,))
            result = cur.fetchone()
            if not result:
                QMessageBox.warning(self, "Error", "Cohort not found in database.")
                return
            cohort_id = result[0]
            cur.execute("""
                SELECT animal_id, species, sex, date_added, notes
                FROM samples WHERE cohort_id = ? ORDER BY id DESC
            """, (cohort_id,))
            samples = cur.fetchall()
        dlg = CohortSamplesDialog(cohort_name, samples, self)
        dlg.exec_()

    def delete_selected_cohorts(self):
        selected = self.cohorts_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Delete Cohorts", "No cohorts selected.")
            return
        cohort_names = [self.cohorts_table.item(row.row(), 0).text() for row in selected]
        msg = "Are you sure you want to delete the following cohorts?\n" + ", ".join(cohort_names) + "\n(All samples in these cohorts will also be deleted.)"
        if QMessageBox.question(self, "Confirm Delete", msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                for name in cohort_names:
                    cur.execute("DELETE FROM cohorts WHERE name = ?", (name,))
                conn.commit()
            self.refresh_cohorts_table()
            self.refresh_samples_table()
            self.status.showMessage(f"Deleted {len(cohort_names)} cohort(s) and their samples.")

    def refresh_samples_table(self):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.animal_id, s.species, s.sex, s.date_added, c.name
                FROM samples s
                LEFT JOIN cohorts c ON s.cohort_id = c.id
                ORDER BY s.id DESC
            """)
            rows = cur.fetchall()
        self.samples_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                self.samples_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value) if value is not None else ""))
        self.samples_table.resizeColumnsToContents()

    def refresh_cohorts_table(self):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, description, date_created FROM cohorts ORDER BY id DESC")
            rows = cur.fetchall()
            # Get sample counts for each cohort
            sample_counts = {}
            for row in rows:
                cur.execute("SELECT COUNT(*) FROM samples WHERE cohort_id = ?", (row[0],))
                sample_counts[row[0]] = cur.fetchone()[0]
        self.cohorts_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            cohort_id, name, experimenter, date_created = row
            count = sample_counts.get(cohort_id, 0)
            for col_idx, value in enumerate([name, experimenter, date_created, count]):
                self.cohorts_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value) if value is not None else ""))
        self.cohorts_table.resizeColumnsToContents()

    def open_add_sample_dialog(self):
        dialog = AddSampleDialog(self)
        if dialog.exec_():
            self.status.showMessage("Sample added to database.")
            self.refresh_samples_table()
        else:
            self.status.showMessage("Sample addition cancelled.")

    def open_create_cohort_dialog(self):
        dialog = CreateCohortDialog(self)
        if dialog.exec_():
            # Save cohort and samples to database
            data = dialog.result
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO cohorts (name, description, date_created) VALUES (?, ?, ?)",
                        (data["name"], data["notes"], data["collection_date"])
                    )
                    cohort_id = cur.lastrowid
                    for sid in data["sample_ids"]:
                        cur.execute(
                            """
                            INSERT INTO samples (
                                cohort_id, animal_id, species, sex, notes, barcode_value, date_added
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                cohort_id,
                                sid,
                                data["sample_type"],
                                data["experimenter"],
                                data["notes"],
                                sid,
                                data["collection_date"]
                            )
                        )
                        # Print barcode for each sample
                        print_barcode(sid)
                    conn.commit()
                self.status.showMessage(f"Cohort '{data['name']}' and {len(data['sample_ids'])} samples created and barcodes printed.")
                self.refresh_cohorts_table()
                self.refresh_samples_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create cohort: {e}")
                self.status.showMessage("Error creating cohort.")
        else:
            self.status.showMessage("Cohort creation cancelled.")

    def display_page(self, index):
        self.stack.setCurrentIndex(index)
        self.status.showMessage(f"Viewing {NAV_ITEMS[index]}")

    def _create_lookup_sample_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel("<h2>Lookup Sample</h2><p>Scan a barcode or enter a SampleID below:</p>")
        layout.addWidget(label)
        self.lookup_input = QLineEdit()
        self.lookup_input.setPlaceholderText("Scan or enter SampleID...")
        self.lookup_input.returnPressed.connect(self.lookup_sample)
        layout.addWidget(self.lookup_input)
        self.lookup_result = QLabel()
        layout.addWidget(self.lookup_result)
        layout.addStretch()
        page.setLayout(layout)
        # Autofocus when page is shown
        def focus_input():
            self.lookup_input.setFocus()
        page.showEvent = lambda event: focus_input()
        return page

    def lookup_sample(self):
        sample_id = self.lookup_input.text().strip()
        if not sample_id:
            self.lookup_result.setText("")
            self.lookup_input.clear()
            self.lookup_input.setFocus()
            return
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM samples WHERE animal_id = ? OR barcode_value = ?", (sample_id, sample_id))
            sample = cur.fetchone()
            if not sample:
                self.lookup_result.setText(f"Sample '{sample_id}' not found.")
                self.lookup_input.clear()
                self.lookup_input.setFocus()
                return
            # Get cohort info
            cohort = None
            if sample[1]:
                cur.execute("SELECT * FROM cohorts WHERE id = ?", (sample[1],))
                cohort = cur.fetchone()
            # Display info
            info = f"<b>Sample ID:</b> {sample[2]}<br>"
            info += f"<b>Sample Type:</b> {sample[3]}<br>"
            info += f"<b>Experimenter:</b> {sample[4]}<br>"
            info += f"<b>Notes:</b> {sample[5]}<br>"
            info += f"<b>Barcode Value:</b> {sample[6]}<br>"
            info += f"<b>Collection Date:</b> {sample[7]}<br>"
            if cohort:
                info += f"<hr><b>Cohort:</b> {cohort[1]}<br>"
                info += f"<b>Experimenter:</b> {cohort[2]}<br>"
                info += f"<b>Date Created:</b> {cohort[3]}<br>"
            self.lookup_result.setText(info)
        self.lookup_input.clear()
        self.lookup_input.setFocus()

    def test_print_barcode(self):
        if print_barcode("Test"):
            self.status.showMessage("Test barcode sent to printer.")
        else:
            self.status.showMessage("Failed to print test barcode.")

    def open_cohort_samples_dialog(self, row, col):
        cohort_name = self.cohorts_table.item(row, 0).text()
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM cohorts WHERE name = ?", (cohort_name,))
            result = cur.fetchone()
            if not result:
                QMessageBox.warning(self, "Error", "Cohort not found in database.")
                return
            cohort_id = result[0]
            cur.execute("""
                SELECT animal_id, species, sex, date_added, notes
                FROM samples WHERE cohort_id = ? ORDER BY id DESC
            """, (cohort_id,))
            samples = cur.fetchall()
        dlg = CohortSamplesDialog(cohort_name, samples, self)
        dlg.exec_()

    def open_sample_details_dialog(self, row, col):
        sample_id = self.samples_table.item(row, 0).text()
        dlg = EditSampleDialog(sample_id, self)
        if dlg.exec_():
            self.refresh_samples_table()

    def edit_cohort_dialog(self, row, col):
        cohort_name = self.cohorts_table.item(row, 0).text()
        dlg = EditPlaceholderDialog(f"Edit Cohort: {cohort_name}", self)
        dlg.exec_()

    def edit_sample_dialog(self, row, col):
        sample_id = self.samples_table.item(row, 0).text()
        dlg = EditPlaceholderDialog(f"Edit Sample: {sample_id}", self)
        dlg.exec_()

    def view_sample_details(self):
        selected = self.samples_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "View Details", "No sample selected.")
            return
        row = selected[0].row()
        sample_id = self.samples_table.item(row, 0).text()
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT animal_id, species, sex, date_added, notes FROM samples WHERE animal_id = ?", (sample_id,))
            sample = cur.fetchone()
        if sample:
            dlg = CohortSamplesDialog(f"Sample: {sample_id}", [sample], self)
            dlg.exec_()

    def eventFilter(self, obj, event):
        # Remove triple-click logic, keep only default event handling
        return super().eventFilter(obj, event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
