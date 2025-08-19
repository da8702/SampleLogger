import win32print

# ZPL for 1.05 x 0.50 inch, 300 dpi label, using user template, SampleID DA213
zpl = """
^XA
^MMT
^PW315
^LL150
^LS0
^BY2,3,66^FT90,125^BCN,,Y,N
^FH\\^FD>:DA213^FS
^PQ1,0,1,Y
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
