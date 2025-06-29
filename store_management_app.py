
import streamlit as st
import pandas as pd
import requests
import io

# OneDrive shareable link (converted to direct download link)
onedrive_link = "https://1drv.ms/f/c/FF4E79734932A335/Etz73HGaCjBHu29L2M68yOcBjyP9YkwfXtFeJW6ypptjnA?e=BRLNom"

# Function to convert OneDrive share link to direct download link
def get_direct_download_link(share_link):
    if "1drv.ms" in share_link:
        return share_link.replace("redir?", "download?").replace("?", "?download=1&")
    return share_link

# Load inventory from OneDrive
@st.cache_data(ttl=60)
def load_inventory():
    try:
        direct_link = get_direct_download_link(onedrive_link)
        response = requests.get(direct_link)
        if response.status_code == 200:
            df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
            return df
        else:
            st.error("Failed to load inventory from OneDrive.")
            return pd.DataFrame(columns=["Product", "Quantity", "Price"])
    except Exception as e:
        st.error(f"Error loading inventory: {e}")
        return pd.DataFrame(columns=["Product", "Quantity", "Price"])

# Save inventory locally (user must manually upload to OneDrive)
def save_inventory_locally(df):
    df.to_excel("updated_inventory.xlsx", index=False, engine='openpyxl')
    st.info("Inventory saved locally as 'updated_inventory.xlsx'. Please upload it to OneDrive manually.")

# Streamlit UI
st.title("🛒 Store Management App (OneDrive Backend)")

inventory = load_inventory()

# Add new product
st.header("Add New Product")
with st.form("add_product_form"):
    product = st.text_input("Product Name")
    quantity = st.number_input("Quantity", min_value=0, step=1)
    price = st.number_input("Price", min_value=0.0, step=0.01)
    submitted = st.form_submit_button("Add Product")
    if submitted and product:
        new_entry = pd.DataFrame([[product, quantity, price]], columns=["Product", "Quantity", "Price"])
        inventory = pd.concat([inventory, new_entry], ignore_index=True)
        save_inventory_locally(inventory)
        st.success(f"Added {product} to inventory.")

# Update or delete product
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
            save_inventory_locally(inventory)
            st.success(f"Updated {selected_product}.")
    with col2:
        if st.button("Delete Product"):
            inventory = inventory.drop(selected_row).reset_index(drop=True)
            save_inventory_locally(inventory)
            st.warning(f"Deleted {selected_product}.")

# Display inventory
st.header("📦 Current Inventory")
st.dataframe(inventory)
