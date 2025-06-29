
import cv2
from pyzbar import pyzbar
import pandas as pd
import os

# Constants
EXCEL_FILE = "updated_inventory.xlsx"
DEFAULT_PRICE = 9.99

# Load or create inventory
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
else:
    df = pd.DataFrame(columns=["Barcode", "Product Name", "Price", "Stock"])

# Ensure correct data types
df["Barcode"] = df["Barcode"].astype(str)

def process_barcode(barcode):
    global df
    barcode = str(barcode)
    if barcode in df["Barcode"].values:
        df.loc[df["Barcode"] == barcode, "Stock"] += 1
        print(f"Updated stock for barcode {barcode}")
    else:
        new_product = {
            "Barcode": barcode,
            "Product Name": f"Product_{barcode}",
            "Price": DEFAULT_PRICE,
            "Stock": 1
        }
        df = pd.concat([df, pd.DataFrame([new_product])], ignore_index=True)
        print(f"Added new product for barcode {barcode}")

    df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
    print(f"Inventory saved to {EXCEL_FILE}")

def scan_barcodes():
    cap = cv2.VideoCapture(0)
    print("Press 'q' to quit.")
    scanned = set()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            if barcode_data not in scanned:
                process_barcode(barcode_data)
                scanned.add(barcode_data)

        cv2.imshow("Barcode Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    scan_barcodes()
