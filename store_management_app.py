
import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from fpdf import FPDF
import smtplib
from email.message import EmailMessage
import tempfile

# Load environment variables for email credentials
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# File to store inventory
inventory_file = "inventory.xlsx"

# Load or initialize inventory
def load_inventory():
    if os.path.exists(inventory_file):
        return pd.read_excel(inventory_file, engine='openpyxl')
    else:
        return pd.DataFrame(columns=["Product", "Category", "Quantity", "Price"])

# Save inventory to Excel
def save_inventory(df):
    df.to_excel(inventory_file, index=False, engine='openpyxl')

# Generate PDF report
def generate_pdf(df, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Inventory Report", ln=True, align='C')
    pdf.ln(10)

    for index, row in df.iterrows():
        line = f"{row['Product']} | {row['Category']} | Qty: {row['Quantity']} | Price: ${row['Price']:.2f}"
        pdf.cell(200, 10, txt=line, ln=True)

    pdf.output(filename)

# Send email with PDF attachment
def send_email_with_attachment(to_email, subject, body, attachment_path):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(body)

    with open(attachment_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(attachment_path)
        msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# Streamlit UI
st.title("🛒 Store Management App")

# Load current inventory
inventory = load_inventory()

# Section to add new product
st.header("Add New Product")
with st.form("add_product_form"):
    product = st.text_input("Product Name")
    category = st.text_input("Category")
    quantity = st.number_input("Quantity", min_value=0, step=1)
    price = st.number_input("Price", min_value=0.0, step=0.01)
    submitted = st.form_submit_button("Add Product")
    if submitted and product:
        new_entry = pd.DataFrame([[product, category, quantity, price]], columns=["Product", "Category", "Quantity", "Price"])
        inventory = pd.concat([inventory, new_entry], ignore_index=True)
        save_inventory(inventory)
        st.success(f"Added {product} to inventory.")

# Section to update or delete products
st.header("Update Inventory")

if not inventory.empty:
    selected_product = st.selectbox("Select Product", inventory["Product"].unique())
    selected_row = inventory[inventory["Product"] == selected_product].index[0]

    new_quantity = st.number_input("Update Quantity", min_value=0, step=1, value=int(inventory.loc[selected_row, "Quantity"]))
    new_price = st.number_input("Update Price", min_value=0.0, step=0.01, value=float(inventory.loc[selected_row, "Price"]))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Update Product"):
            inventory.loc[selected_row, "Quantity"] = new_quantity
            inventory.loc[selected_row, "Price"] = new_price
            save_inventory(inventory)
            st.success(f"Updated {selected_product}.")
    with col2:
        if st.button("Delete Product"):
            inventory = inventory.drop(selected_row).reset_index(drop=True)
            save_inventory(inventory)
            st.warning(f"Deleted {selected_product}.")

# Filter and search
st.header("Search and Filter")
search_term = st.text_input("Search by product name")
category_filter = st.selectbox("Filter by category", ["All"] + sorted(inventory["Category"].dropna().unique().tolist()))

filtered_inventory = inventory.copy()
if search_term:
    filtered_inventory = filtered_inventory[filtered_inventory["Product"].str.contains(search_term, case=False)]
if category_filter != "All":
    filtered_inventory = filtered_inventory[filtered_inventory["Category"] == category_filter]

# Highlight low stock
def highlight_low_stock(val):
    return 'background-color: #ffcccc' if val < 5 else ''

st.header("📦 Current Inventory")
st.dataframe(filtered_inventory.style.applymap(highlight_low_stock, subset=["Quantity"]))

# Inventory chart
st.subheader("📊 Inventory Value Chart")
if not filtered_inventory.empty:
    chart_data = filtered_inventory.copy()
    chart_data["Total Value"] = chart_data["Quantity"] * chart_data["Price"]
    fig, ax = plt.subplots()
    ax.bar(chart_data["Product"], chart_data["Total Value"])
    ax.set_ylabel("Total Value ($)")
    ax.set_title("Inventory Value per Product")
    st.pyplot(fig)

# Export to PDF and email
st.header("📄 Export & Email Report")
email_address = st.text_input("Recipient Email")
if st.button("Generate PDF and Send Email"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        generate_pdf(filtered_inventory, tmpfile.name)
        if EMAIL_ADDRESS and EMAIL_PASSWORD:
            try:
                send_email_with_attachment(email_address, "Inventory Report", "Attached is the latest inventory report.", tmpfile.name)
                st.success("Email sent successfully!")
            except Exception as e:
                st.error(f"Failed to send email: {e}")
        else:
            st.warning("Email credentials not set in environment variables.")
