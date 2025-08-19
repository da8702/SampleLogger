import win32print

# ZPL for 1.05 x 0.50 inch, 300 dpi label, barcode and large centered text
zpl = """
^XA
^PW315
^LL150
^FO60,30^BY2
^BCN,60,N,N,N
^FDDA001^FS
^FO83,100^A0N,30,30^FDDA001^FS
^XZ
"""

printer_name = win32print.GetDefaultPrinter()
print(f"Sending to printer: {printer_name}")

hPrinter = win32print.OpenPrinter(printer_name)
try:
    hJob = win32print.StartDocPrinter(hPrinter, 1, ("Zebra Test Label", None, "RAW"))
    win32print.StartPagePrinter(hPrinter)
    win32print.WritePrinter(hPrinter, zpl.encode())
    win32print.EndPagePrinter(hPrinter)
    win32print.EndDocPrinter(hPrinter)
    print("Test label sent!")
finally:
    win32print.ClosePrinter(hPrinter)
