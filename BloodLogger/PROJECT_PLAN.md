# BloodLogger Project: Detailed Plan

---

## 1. Project Overview

A desktop application for logging, tracking, and managing blood samples in a lab, with integrated barcode generation, printing (Zebra ZD621), and scanning for rapid sample lookup.

---

## 2. Major Components

### A. User Interface (UI)
- **Framework:** Python (Tkinter, PyQt, or Kivy; recommend PyQt for modern look)
- **Main Screens:**
  - Dashboard/Home
  - Cohort Management (add/view/edit/delete cohorts)
  - Animal/Sample Management (add/view/edit/delete samples within cohorts)
  - Barcode Printing (batch and single)
  - Sample Lookup (by scanning or manual entry)
  - Data Export/Import

### B. Database
- **Type:** SQLite (single file, e.g., `bloodlogger.db`)
- **Schema:**
  - **Cohorts Table:**  
    - id (PK), name, description, date_created, etc.
  - **Samples Table:**  
    - id (PK), cohort_id (FK), animal_id, species, sex, notes, barcode_value, date_added, etc.
  - **(Optional) Users Table:**  
    - For multi-user support

### C. Barcode Generation
- **Library:** python-barcode (for Code128), or Pillow for custom images
- **Barcode Content:** Unique sample/animal ID (e.g., `A001`, UUID)
- **Label Content:** Barcode, human-readable ID, optional cohort/sample info

### D. Barcode Printing (Zebra ZD621)
- **Method:** Generate ZPL (Zebra Programming Language) commands
- **Send to Printer:** Use `pywin32` or `win32print` to send ZPL as a raw print job on Windows

### E. Barcode Scanning
- **Integration:** Barcode scanner acts as keyboard input
- **Workflow:** Focused input field in app; scanned code triggers lookup

### F. Data Export/Import
- **Formats:** CSV, Excel, or JSON
- **Purpose:** Backup, sharing, or analysis

### G. Error Handling & Logging
- **User-friendly error messages**
- **Logging for debugging and audit trail**

---

## 3. Detailed Workflow

### A. Adding a Cohort
1. User clicks "Add Cohort"
2. Enters cohort details (name, description, date, etc.)
3. Cohort saved to database

### B. Adding Samples/Animals
1. User selects cohort
2. Clicks "Add Sample"
3. Enters sample details (animal ID, species, sex, etc.)
4. Unique barcode value generated (e.g., UUID or sequential)
5. Sample saved to database

### C. Barcode Generation & Printing
1. User selects samples to print
2. App generates ZPL for each sample (barcode + label)
3. App sends ZPL to Zebra ZD621 printer
4. Labels printed and attached to samples

### D. Sample Lookup
1. User scans barcode (or enters ID manually)
2. App receives input, queries database for sample
3. App displays sample and cohort info

### E. Data Export/Import
1. User selects export/import option
2. App reads/writes data in chosen format

---

## 4. Technical Details

### A. Python Libraries
- **UI:** PyQt5 or PyQt6 (`pip install PyQt5`)
- **Database:** sqlite3 (built-in)
- **Barcode:** python-barcode (`pip install python-barcode`), Pillow (`pip install pillow`)
- **Printing:** pywin32 (`pip install pywin32`)
- **CSV/Excel:** pandas (`pip install pandas`), openpyxl (`pip install openpyxl`)

### B. ZPL Example for Barcode
```zpl
^XA
^FO50,50^BY2
^BCN,100,Y,N,N
^FD>A001^FS
^FO50,160^A0N,30,30^FDAnimal ID: A001^FS
^XZ
```
- Replace `A001` with the sample’s barcode value.

### C. Sending ZPL to Printer (Python)
```python
import win32print

printer_name = win32print.GetDefaultPrinter()
zpl = "^XA...^XZ"  # Your ZPL string

hPrinter = win32print.OpenPrinter(printer_name)
try:
    hJob = win32print.StartDocPrinter(hPrinter, 1, ("BloodLogger Label", None, "RAW"))
    win32print.StartPagePrinter(hPrinter)
    win32print.WritePrinter(hPrinter, zpl.encode())
    win32print.EndPagePrinter(hPrinter)
    win32print.EndDocPrinter(hPrinter)
finally:
    win32print.ClosePrinter(hPrinter)
```

### D. Barcode Scanning
- Barcode scanner acts as keyboard input.
- App listens for input in a focused field.
- On Enter, triggers lookup.

---

## 5. File/Folder Structure (Suggested)

```
BloodLogger/
│
├── main.py                # Entry point
├── db/
│   └── bloodlogger.db     # SQLite database
├── ui/
│   ├── main_window.py     # Main UI logic
│   └── ...                # Other UI components
├── barcode/
│   ├── generator.py       # Barcode generation logic
│   └── printer.py         # ZPL and printing logic
├── data/
│   └── exports/           # Exported files
├── utils/
│   └── logger.py          # Logging/error handling
├── requirements.txt       # Python dependencies
└── README.md              # Project overview
```

---

## 6. Future Features (Optional)
- User authentication
- Audit trail/history
- Cloud sync/backup
- Mobile app for lookup

---

## 7. Development Roadmap

1. **Set up Git repo and project structure**
2. **Implement database schema and connection**
3. **Build basic UI (add/view cohorts and samples)**
4. **Integrate barcode generation**
5. **Integrate Zebra printer (ZPL)**
6. **Implement sample lookup by barcode**
7. **Add data export/import**
8. **Testing and error handling**
9. **Documentation and packaging**

---

## 8. References

- [PyQt5 Documentation](https://doc.qt.io/qtforpython/)
- [python-barcode](https://pypi.org/project/python-barcode/)
- [Zebra ZPL Programming Guide](https://www.zebra.com/content/dam/zebra/manuals/en-us/printer/zpl-zbi2-pm-en.pdf)
- [DB Browser for SQLite](https://sqlitebrowser.org/)

---

**End of Plan**
