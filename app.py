
import streamlit as st
import pandas as pd
from pathlib import Path

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    page_title="Grocery Restocking Agent",
    page_icon="🛒",
    layout="wide"
)

FILE = Path(__file__).parent / "inventory.csv"

COLUMNS = [
    "Product", "Stock", "Threshold",
    "Target Stock", "Unit Price"
]


# ---------------- DATA FUNCTIONS ----------------
def load_inventory():
    if not FILE.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(FILE, index=False)

    df = pd.read_csv(FILE)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = 0 if col != "Product" else ""

    for col in COLUMNS[1:]:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        ).fillna(0)

    return df[COLUMNS]


def save_inventory(df):
    df.to_csv(FILE, index=False)


def analyse_inventory(df):
    result = df.copy()

    result["Status"] = result.apply(
        lambda row: (
            "Critical"
            if row["Stock"] <= row["Threshold"] / 2
            else "Restock"
            if row["Stock"] <= row["Threshold"]
            else "Sufficient"
        ),
        axis=1
    )

    result["Order Quantity"] = (
        result["Target Stock"] - result["Stock"]
    ).clip(lower=0)

    result["Order Cost"] = (
        result["Order Quantity"] * result["Unit Price"]
    )

    return result
df = load_inventory()
result = analyse_inventory(df)
# CONSOLE OUTPUT
print("\nGROCERY RESTOCKING AGENT - RESULTS")
print("-" * 40)

print(f"Total Products: {len(result)}")
print(f"Products to Restock: {(result['Status'] != 'Sufficient').sum()}")
print(f"Critical Products: {(result['Status'] == 'Critical').sum()}")
print(f"Estimated Order Cost: Rs. {result['Order Cost'].sum():,.2f}")

print("\nRESTOCKING RECOMMENDATIONS")
orders = result[result["Status"] != "Sufficient"]

if orders.empty:
    print("All products have sufficient stock.")
else:
    print(orders[
        ["Product", "Stock", "Threshold", "Status",
         "Order Quantity", "Order Cost"]
    ].to_string(index=False))

print("\nInventory monitoring completed.")
print("-" * 40) 
st.title("🛒 Grocery Restocking Agent")
st.write(
    "Monitor grocery stock and get automatic "
    "restocking recommendations."
)

total_products = len(result)
critical = (result["Status"] == "Critical").sum()
restock = (result["Status"] != "Sufficient").sum()
estimated_cost = result["Order Cost"].sum()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Products", total_products)
c2.metric("Products to Restock", int(restock))
c3.metric("Critical Products", int(critical))
c4.metric("Estimated Order Cost", f"₹{estimated_cost:,.2f}")

st.divider()

# ---------------- INVENTORY TABLE ----------------
st.subheader("📦 Inventory Monitoring")

search = st.text_input("🔍 Search product by name")

filtered = result[
    result["Product"].astype(str).str.contains(
        search, case=False, na=False
    )
]

if filtered.empty:
    st.info("No matching products found.")
else:
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )

# ---------------- CHART ----------------
st.subheader("📊 Stock Level Comparison")

if not result.empty:
    chart_data = result.set_index("Product")[
        ["Stock", "Threshold"]
    ]
    st.bar_chart(chart_data)
else:
    st.info("Add products to display the chart.")

# ---------------- RESTOCKING ----------------
st.subheader("🔔 Restocking Recommendations")

orders = result[result["Status"] != "Sufficient"]

if orders.empty:
    st.success("All products have sufficient stock.")
else:
    st.dataframe(
        orders[
            [
                "Product", "Stock", "Threshold",
                "Status", "Order Quantity", "Order Cost"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

# ---------------- DOWNLOAD REPORT ----------------
st.subheader("📄 Download Report")

st.download_button(
    label="Download Inventory Report (CSV)",
    data=result.to_csv(index=False).encode("utf-8"),
    file_name="grocery_inventory_report.csv",
    mime="text/csv"
)

st.divider()

# ---------------- ADD PRODUCT ----------------
st.subheader("➕ Add New Product")

with st.form("add_product"):
    name = st.text_input("Product name")

    a, b = st.columns(2)
    stock = a.number_input("Current stock", min_value=0, step=1)
    threshold = b.number_input(
        "Stock threshold", min_value=0, step=1
    )

    c, d = st.columns(2)
    target = c.number_input("Target stock", min_value=0, step=1)
    price = d.number_input(
        "Unit price (₹)", min_value=0.0, step=1.0
    )

    add = st.form_submit_button("Add Product")

    if add:
        if not name.strip():
            st.error("Please enter a product name.")
        elif df["Product"].astype(str).str.lower().eq(
            name.strip().lower()
        ).any():
            st.error("This product already exists.")
        elif target < threshold:
            st.error("Target stock must be at least the threshold.")
        else:
            new_row = pd.DataFrame([{
                "Product": name.strip(),
                "Stock": stock,
                "Threshold": threshold,
                "Target Stock": target,
                "Unit Price": price
            }])

            updated = pd.concat(
                [df, new_row], ignore_index=True
            )
            save_inventory(updated)
            st.success(f"{name} added successfully!")
            st.rerun()

# ---------------- UPDATE PRODUCT ----------------
st.subheader("✏️ Update Inventory")

if not df.empty:
    selected = st.selectbox(
        "Select product to update",
        df["Product"].tolist()
    )

    item = df[df["Product"] == selected].iloc[0]

    with st.form("update_product"):
        new_stock = st.number_input(
            "New stock quantity",
            min_value=0,
            step=1,
            value=int(item["Stock"])
        )

        new_threshold = st.number_input(
            "New threshold",
            min_value=0,
            step=1,
            value=int(item["Threshold"])
        )

        new_target = st.number_input(
            "New target stock",
            min_value=0,
            step=1,
            value=int(item["Target Stock"])
        )

        new_price = st.number_input(
            "New unit price (₹)",
            min_value=0.0,
            step=1.0,
            value=float(item["Unit Price"])
        )

        update = st.form_submit_button("Save Changes")

        if update:
            if new_target < new_threshold:
                st.error(
                    "Target stock must be at least the threshold."
                )
            else:
                df.loc[
                    df["Product"] == selected, "Stock"
                ] = new_stock

                df.loc[
                    df["Product"] == selected, "Threshold"
                ] = new_threshold

                df.loc[
                    df["Product"] == selected, "Target Stock"
                ] = new_target

                df.loc[
                    df["Product"] == selected, "Unit Price"
                ] = new_price

                save_inventory(df)
                st.success(f"{selected} updated successfully!")
                st.rerun()
else:
    st.info("Add a product before updating inventory.")

# ---------------- DELETE PRODUCT ----------------
st.subheader("🗑️ Delete Product")

if not df.empty:
    delete_name = st.selectbox(
        "Select product to delete",
        df["Product"].tolist()
    )

    confirm = st.checkbox(
        f"Confirm deletion of {delete_name}"
    )

    if st.button("Delete Selected Product"):
        if confirm:
            updated = df[df["Product"] != delete_name]
            save_inventory(updated)
            st.success(f"{delete_name} deleted.")
            st.rerun()
        else:
            st.warning("Please tick the confirmation box first.")

st.caption(
    "Prototype: Restocking recommendations are rule-based. "
    "Supplier orders are not placed automatically."
)
