import hashlib
import json
import os
import re
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="Creator Concepts Suite", page_icon="🛍️", layout="wide")


class User:
    def __init__(self, name, email):
        self.name = name
        self.__email = email

    def get_email(self):
        return self.__email

    def display_details(self):
        return f"Name: {self.name}\nEmail: {self.__email}"


class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price


class Seller(User):
    def __init__(self, name, email):
        super().__init__(name, email)
        self.products = []
        self._profit = 0

    def add_product(self, product):
        self.products.append(product)

    def add_profit(self, amount):
        self._profit += amount

    def get_profit(self):
        return self._profit

    def display_details(self):
        lines = ["Seller Details", f"Name: {self.name}", f"Email: {self.get_email()}", f"Profit: ₹{self._profit}"]
        for product in self.products:
            lines.append(f"- {product.name} (₹{product.price})")
        return "\n".join(lines)


class Buyer(User):
    def __init__(self, name, email):
        super().__init__(name, email)

    def display_details(self):
        return f"Buyer Details\nName: {self.name}\nEmail: {self.get_email()}"

    def purchase_product(self, product, seller):
        commission_rate = 0.10
        commission = product.price * commission_rate
        seller_amount = product.price - commission
        seller.add_profit(seller_amount)
        return {
            "product": product.name,
            "price": product.price,
            "commission": commission,
            "seller_amount": seller_amount,
        }


def validate_registration(name, email, phone, password, creator_id):
    errors = []

    if not re.match(r"^[A-Za-z ]+$", name):
        errors.append("Name should contain only alphabets and spaces.")
    if not re.fullmatch(r"[a-zA-Z0-9._%+-]+@gmail\.com", email):
        errors.append("Invalid Gmail format.")
    if not re.fullmatch(r"^[6-9]\d{9}$", phone):
        errors.append("Phone number must be 10 digits and start with 6-9.")
    if len(password) < 8:
        errors.append("Password must contain at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r"[@#$%^&*!]", password):
        errors.append("Password must contain at least one special character.")
    if not re.fullmatch(r"CR\d{4}", creator_id):
        errors.append("Creator ID must be in format CR1234.")

    return {"valid": len(errors) == 0, "errors": errors}


def create_creator_records_file():
    records = [
        "CR1001,Ananya,ananya@gmail.com,Beaded Bracelet,Jewelry,500\n",
        "CR1002,Rahul,rahul@gmail.com,Crochet Bag,Handmade Crafts,850\n",
        "CR1003,Meera,meera@gmail.com,Resin Keychain,Handmade Crafts,250\n",
        "CR1004,Aditi,aditi@gmail.com,Canvas Painting,Artwork,1500\n",
        "CR1005,Kiran,kiran@gmail.com,Digital Planner,Digital Products,300\n",
        "CR1006,Sneha,sneha@gmail.com,Handmade Earrings,Jewelry,400\n",
        "CR1007,Riya,riya@gmail.com,Photo Frame,Artwork,700\n",
        "CR1008,Arjun,arjun@gmail.com,Notebook Cover,Handmade Crafts,350\n",
    ]
    path = BASE_DIR / "creator_records.csv"
    path.write_text("".join(records), encoding="utf-8")
    return path


def load_creator_records():
    path = BASE_DIR / "creator_records.csv"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 6:
                rows.append({
                    "Creator ID": parts[0],
                    "Creator Name": parts[1],
                    "Email": parts[2],
                    "Product": parts[3],
                    "Category": parts[4],
                    "Price": parts[5],
                })
    return rows


def get_user_lookup(username):
    url = "https://jsonplaceholder.typicode.com/users"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        users = response.json()
        for user in users:
            if user["username"].lower() == username.lower():
                return user
        return None
    except requests.RequestException:
        return "error"


@st.cache_data
def load_market_data():
    products = pd.read_csv(BASE_DIR / "products.csv")
    sales = pd.read_csv(BASE_DIR / "creator_sales.csv")
    creators = json.loads((BASE_DIR / "creators.json").read_text(encoding="utf-8"))
    products["Price"] = pd.to_numeric(products["Price"], errors="coerce").fillna(0)
    products["Stock"] = pd.to_numeric(products["Stock"], errors="coerce").fillna(0).astype(int)
    sales["Revenue"] = sales["Price"] * sales["Units_Sold"]
    return products, sales, creators


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def initialize_session_state():
    if "users" not in st.session_state:
        st.session_state.users = [
            {"name": "Admin User", "email": "admin@creator.com", "password": hash_password("admin123"), "role": "admin"},
            {"name": "Seller One", "email": "seller@creator.com", "password": hash_password("seller123"), "role": "seller"},
            {"name": "Buyer One", "email": "buyer@creator.com", "password": hash_password("buyer123"), "role": "buyer"},
        ]
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "products" not in st.session_state:
        st.session_state.products = load_market_data()[0].copy()
    if "cart" not in st.session_state:
        st.session_state.cart = []
    if "orders" not in st.session_state:
        st.session_state.orders = [
            {
                "Order ID": "#1048",
                "Creator": "Aarav Crafts",
                "Product": "Wooden Vase",
                "Amount": "₹850",
                "Status": "Paid",
                "Updated": "3 days ago",
            },
            {
                "Order ID": "#1049",
                "Creator": "Meera Jewels",
                "Product": "Pearl Necklace",
                "Amount": "₹1,500",
                "Status": "Paid",
                "Updated": "1 day ago",
            },
        ]
    if "support_tickets" not in st.session_state:
        st.session_state.support_tickets = [
            {"Issue type": "Order issue", "Customer": "Aditya", "Status": "Open"},
            {"Issue type": "Payment", "Customer": "Nisha", "Status": "Resolved"},
        ]


def authenticate_user(email, password):
    for user in st.session_state.users:
        if user["email"].lower() == email.lower() and user["password"] == hash_password(password):
            st.session_state.current_user = user
            st.session_state.authenticated = True
            return True
    return False


def register_user(name, email, password, role):
    for user in st.session_state.users:
        if user["email"].lower() == email.lower():
            return False

    st.session_state.users.append({
        "name": name,
        "email": email.lower(),
        "password": hash_password(password),
        "role": role,
    })
    return True


def add_to_cart(product_id, quantity=1):
    product = st.session_state.products[st.session_state.products["Product"] == product_id].iloc[0]
    for item in st.session_state.cart:
        if item["Product"] == product["Product"]:
            item["Quantity"] += quantity
            return
    st.session_state.cart.append({
        "Product": product["Product"],
        "Creator": product["Creator"],
        "Category": product["Category"],
        "Price": float(product["Price"]),
        "Quantity": quantity,
    })


def place_order(customer_name):
    if not st.session_state.cart:
        st.warning("Your cart is empty.")
        return

    for item in st.session_state.cart:
        product = st.session_state.products[st.session_state.products["Product"] == item["Product"]]
        if product.empty:
            continue
        row = product.iloc[0]
        if row["Stock"] < item["Quantity"]:
            st.error(f"Not enough stock for {item['Product']}.")
            return

    order_id = f"#{1000 + len(st.session_state.orders)}"
    subtotal = sum(item["Price"] * item["Quantity"] for item in st.session_state.cart)

    for item in st.session_state.cart:
        product_index = st.session_state.products.index[st.session_state.products["Product"] == item["Product"]][0]
        st.session_state.products.at[product_index, "Stock"] -= item["Quantity"]

    st.session_state.orders.append({
        "Order ID": order_id,
        "Creator": st.session_state.cart[0]["Creator"],
        "Product": ", ".join(item["Product"] for item in st.session_state.cart),
        "Amount": f"₹{subtotal:,.0f}",
        "Status": "Pending",
        "Updated": "Just now",
        "Customer": customer_name,
    })

    st.session_state.cart = []
    st.success(f"Order {order_id} placed successfully for {customer_name}.")


def render_auth_page():
    st.title("Creator Marketplace")
    st.caption("Sign in to access your marketplace dashboard")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                if authenticate_user(email, password):
                    st.success(f"Welcome back, {st.session_state.current_user['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with tab2:
        with st.form("signup_form"):
            full_name = st.text_input("Full name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            role = st.selectbox("Role", ["buyer", "seller"], key="signup_role")
            submitted = st.form_submit_button("Create account")
            if submitted:
                if not full_name or not email or not password:
                    st.warning("Please fill in all fields.")
                elif register_user(full_name, email, password, role):
                    st.success("Account created successfully. Please login.")
                else:
                    st.warning("An account with this email already exists.")


def render_home():
    initialize_session_state()
    st.title("Creator Marketplace")
    st.caption("Marketplace dashboard for products, creators, and sales performance")

    products = st.session_state.products
    sales = products[["Category", "Price", "Stock"]].copy()
    sales["Revenue"] = sales["Price"] * sales["Stock"]
    total_revenue = float(products["Price"].sum())
    total_units = int(products["Stock"].sum())
    avg_price = float(products["Price"].mean())
    total_creators = len(products["Creator"].unique())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Revenue", f"₹{total_revenue:,.0f}")
    col2.metric("Inventory", f"{total_units}")
    col3.metric("Avg. Price", f"₹{avg_price:,.0f}")
    col4.metric("Creators", total_creators)

    st.markdown("---")
    chart_col, side_col = st.columns([2.2, 1])
    with chart_col:
        revenue_chart = sales.groupby("Category")["Revenue"].sum().sort_values(ascending=False)
        st.subheader("Revenue by category")
        st.bar_chart(revenue_chart)

    with side_col:
        st.subheader("Stock alert")
        low_stock = products[products["Stock"] <= 10][["Product", "Stock"]]
        if low_stock.empty:
            st.write("All products are well-stocked.")
        else:
            st.dataframe(low_stock, hide_index=True, use_container_width=True)

    st.markdown("---")

    feature_col1, feature_col2, feature_col3 = st.columns(3)
    with feature_col1:
        st.subheader("Featured collection")
        for _, row in products.head(3).iterrows():
            st.markdown(f"### {row['Product']}")
            st.write(f"{row['Category']} • ₹{row['Price']}")
            st.write(f"Stock: {row['Stock']} units")

    with feature_col2:
        st.subheader("Popular creators")
        creator_summary = products.groupby("Creator")["Price"].sum().sort_values(ascending=False).head(5)
        for name, value in creator_summary.items():
            st.write(f"• {name} — ₹{value:,.0f}")

    with feature_col3:
        st.subheader("Business health")
        st.write("★★★★★ Strong demand")
        st.write("92% repeat customer retention")
        st.write("Fast delivery performance")

    st.markdown("---")

    st.subheader("Recent orders")
    orders_df = pd.DataFrame(st.session_state.orders)
    st.dataframe(orders_df, hide_index=True, use_container_width=True)


def render_catalog():
    initialize_session_state()
    st.title("Catalog")
    products = st.session_state.products

    search_term = st.text_input("Search products")
    category_filter = st.selectbox("Filter by category", ["All"] + sorted(products["Category"].unique().tolist()))

    filtered = products.copy()
    if category_filter != "All":
        filtered = filtered[filtered["Category"] == category_filter]
    if search_term:
        filtered = filtered[filtered["Product"].str.contains(search_term, case=False, na=False)]

    with st.expander("Add new product", expanded=False):
        new_name = st.text_input("Product name", key="new_product_name")
        new_creator = st.text_input("Creator name", key="new_creator_name")
        new_category = st.selectbox("Category", ["Handmade Crafts", "Jewelry", "Artwork", "Digital Products"], key="new_category")
        new_price = st.number_input("Price", min_value=100, step=50, value=500, key="new_price")
        new_stock = st.number_input("Stock", min_value=1, step=1, value=10, key="new_stock")
        if st.button("Publish product"):
            if new_name and new_creator:
                new_row = {
                    "Creator": new_creator,
                    "Product": new_name,
                    "Category": new_category,
                    "Price": new_price,
                    "Stock": int(new_stock),
                }
                st.session_state.products = pd.concat([st.session_state.products, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"{new_name} has been added to the catalog.")
            else:
                st.warning("Please provide a product name and creator name.")

    st.subheader(f"Showing {len(filtered)} products")
    if filtered.empty:
        st.info("No products match this filter.")
        return

    for _, row in filtered.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {row['Product']}")
            st.write(f"{row['Creator']} • {row['Category']}")
            st.write(f"Price: ₹{row['Price']}")
            st.write(f"In stock: {row['Stock']}")
        with col2:
            quantity = st.number_input("Qty", min_value=1, max_value=max(1, int(row["Stock"])), value=1, key=f"qty_{row['Product']}")
            if st.button("Add to cart", key=f"add_{row['Product']}"):
                if row["Stock"] > 0:
                    add_to_cart(row["Product"], quantity)
                    st.success(f"{row['Product']} added to cart.")
                else:
                    st.warning("This product is out of stock.")


def render_cart():
    initialize_session_state()
    st.title("Cart")
    if not st.session_state.cart:
        st.info("Your cart is empty.")
        return

    cart_df = pd.DataFrame(st.session_state.cart)
    cart_df["Total"] = cart_df["Price"] * cart_df["Quantity"]
    st.dataframe(cart_df[["Product", "Category", "Quantity", "Price", "Total"]], hide_index=True, use_container_width=True)

    customer_name = st.text_input("Customer name")
    if st.button("Checkout"):
        if customer_name:
            place_order(customer_name)
        else:
            st.warning("Please enter the customer name.")


def render_creators():
    initialize_session_state()
    st.title("Creators")
    products = st.session_state.products

    creator_summary = products.groupby("Creator").agg(
        Products=("Product", "count"),
        Revenue=("Price", "sum"),
        Avg_Price=("Price", "mean")
    ).reset_index()
    creator_summary = creator_summary.sort_values("Revenue", ascending=False)
    st.dataframe(creator_summary, hide_index=True, use_container_width=True)

    st.markdown("---")
    with st.form("creator_form"):
        creator_name = st.text_input("New creator name")
        creator_category = st.selectbox("Business category", ["Handmade Crafts", "Jewelry", "Artwork", "Digital Products"])
        submitted = st.form_submit_button("Add creator")
        if submitted and creator_name:
            st.session_state.products = pd.concat([
                st.session_state.products,
                pd.DataFrame([{
                    "Creator": creator_name,
                    "Product": f"{creator_name} Signature Item",
                    "Category": creator_category,
                    "Price": 500,
                    "Stock": 20,
                }])
            ], ignore_index=True)
            st.success(f"{creator_name} was added to the marketplace.")


def render_orders():
    initialize_session_state()
    st.title("Orders")
    if not st.session_state.orders:
        st.info("No orders yet.")
        return

    orders_df = pd.DataFrame(st.session_state.orders)
    st.dataframe(orders_df, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.subheader("Order status summary")
    status_counts = pd.Series({status: (pd.DataFrame(st.session_state.orders)["Status"] == status).sum() for status in ["Paid", "Pending", "Processing", "Shipped"]})
    st.bar_chart(status_counts)


def render_analytics():
    initialize_session_state()
    st.title("Analytics")
    products = st.session_state.products

    category_summary = products.groupby("Category").agg(
        Products=("Product", "count"),
        Inventory=("Stock", "sum"),
        Revenue=("Price", "sum")
    )
    st.dataframe(category_summary, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Inventory by category")
        st.bar_chart(category_summary["Inventory"])
    with col2:
        st.subheader("Price distribution")
        st.bar_chart(products.set_index("Product")["Price"])

    st.markdown("---")
    st.subheader("Low stock products")
    low_stock = products[products["Stock"] <= 10][["Product", "Category", "Stock"]]
    st.dataframe(low_stock, hide_index=True, use_container_width=True)


def render_support():
    initialize_session_state()
    st.title("Support")
    st.subheader("Customer support overview")
    col1, col2 = st.columns(2)
    col1.metric("Open tickets", sum(1 for t in st.session_state.support_tickets if t["Status"] == "Open"))
    col2.metric("Resolved today", sum(1 for t in st.session_state.support_tickets if t["Status"] == "Resolved"))

    with st.form("support_form"):
        issue_type = st.selectbox("Issue type", ["Order issue", "Payment", "Refund", "Product query"])
        customer_name = st.text_input("Customer name")
        problem = st.text_area("Problem details")
        submitted = st.form_submit_button("Submit ticket")
        if submitted and customer_name and problem:
            st.session_state.support_tickets.append({
                "Issue type": issue_type,
                "Customer": customer_name,
                "Status": "Open",
            })
            st.success("Support ticket created successfully.")

    st.markdown("---")
    st.subheader("Ticket list")
    st.dataframe(pd.DataFrame(st.session_state.support_tickets), use_container_width=True)


def main():
    initialize_session_state()

    if not st.session_state.authenticated:
        render_auth_page()
        return

    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; }
        div[data-testid="stSidebarNav"] { background: linear-gradient(180deg, #111827 0%, #1f2937 100%); }
        section[data-testid="stSidebar"] { background: #111827; }
        .st-emotion-cache-1v0mbdj { color: #f9fafb; }
        .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label { color: #111827; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title(f"Welcome, {st.session_state.current_user['name']}")
    st.sidebar.write(f"Role: {st.session_state.current_user['role'].title()}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()

    nav_options = ["Dashboard", "Catalog", "Cart", "Creators", "Orders", "Analytics", "Support"]
    if st.session_state.current_user["role"] == "buyer":
        nav_options = ["Dashboard", "Catalog", "Cart", "Orders", "Support"]
    elif st.session_state.current_user["role"] == "seller":
        nav_options = ["Dashboard", "Catalog", "Creators", "Orders", "Analytics"]

    nav = st.sidebar.radio("Navigation", nav_options, index=0)

    if nav == "Dashboard":
        render_home()
    elif nav == "Catalog":
        render_catalog()
    elif nav == "Cart":
        render_cart()
    elif nav == "Creators":
        render_creators()
    elif nav == "Orders":
        render_orders()
    elif nav == "Analytics":
        render_analytics()
    elif nav == "Support":
        render_support()


if __name__ == "__main__":
    main()
