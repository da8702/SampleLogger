import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QStackedWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QStatusBar, QPushButton, QDialog,
    QFormLayout, QLineEdit, QComboBox, QTextEdit, QDateEdit, QMessageBox,
    QRadioButton, QButtonGroup, QSpinBox, QGroupBox, QHBoxLayout,
    QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import QDate

NAV_ITEMS = [
    "Dashboard",
    "Cohorts",
    "Samples",
    "Print Barcodes",
    "Lookup Sample",
    "Export/Import"
]

SAMPLE_TYPES = ["serum", "plasma", "peritoneal fluid", "whole blood"]
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'bloodlogger.db')

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SampleLogger")
        self.resize(1000, 600)
        self._init_ui()

    def _init_ui(self):
        # Sidebar navigation
        self.nav_list = QListWidget()
        self.nav_list.addItems(NAV_ITEMS)
        self.nav_list.setFixedWidth(180)
        self.nav_list.currentRowChanged.connect(self.display_page)

        # Main content area (stacked widget)
        self.stack = QStackedWidget()
        self.pages = {}
        for item in NAV_ITEMS:
            if item == "Samples":
                page = self._create_samples_page()
            elif item == "Cohorts":
                page = self._create_cohorts_page()
            else:
                page = QWidget()
                layout = QVBoxLayout()
                label = QLabel(f"<h2>{item}</h2><p>Placeholder for {item} page.</p>")
                layout.addWidget(label)
                layout.addStretch()
                page.setLayout(layout)
            self.stack.addWidget(page)
            self.pages[item] = page

        # Layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.nav_list)
        main_layout.addWidget(self.stack)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        # Default to Dashboard
        self.nav_list.setCurrentRow(0)

    def _create_samples_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel("<h2>Samples</h2><p>Placeholder for Samples page.</p>")
        layout.addWidget(label)
        add_btn = QPushButton("Add Sample")
        add_btn.clicked.connect(self.open_add_sample_dialog)
        layout.addWidget(add_btn)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def open_add_sample_dialog(self):
        dialog = AddSampleDialog(self)
        if dialog.exec_():
            self.status.showMessage("Sample added to database.")
        else:
            self.status.showMessage("Sample addition cancelled.")

    def _create_cohorts_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel("<h2>Cohorts</h2><p>Placeholder for Cohorts page.</p>")
        layout.addWidget(label)
        add_btn = QPushButton("Create Cohort")
        add_btn.clicked.connect(self.open_create_cohort_dialog)
        layout.addWidget(add_btn)
        layout.addStretch()
        page.setLayout(layout)
        return page

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
                    conn.commit()
                self.status.showMessage(f"Cohort '{data['name']}' and {len(data['sample_ids'])} samples created.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create cohort: {e}")
                self.status.showMessage("Error creating cohort.")
        else:
            self.status.showMessage("Cohort creation cancelled.")

    def display_page(self, index):
        self.stack.setCurrentIndex(index)
        self.status.showMessage(f"Viewing {NAV_ITEMS[index]}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
