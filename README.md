# Creator Marketplace App

A full-stack style marketplace dashboard built with Python and Streamlit. This project combines marketplace functionality, creator management, cart logic, analytics, and user authentication in a single application.

## Features

- User login and sign-up system
- Role-based access for buyer and seller users
- Product catalog with search and category filters
- Add-to-cart and checkout flow
- Creator dashboard and product management
- Order tracking and status summary
- Sales and analytics overview
- Support ticket form and ticket tracking
- Responsive Streamlit UI

## Tech Stack

- Python
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Hashlib for secure password storage

## Project Files

- `creator_marketplace.py` - Main app
- `products.csv` - Product dataset
- `creator_sales.csv` - Sales data
- `creators.json` - Creator records
- `students.csv` - Example student dataset for analytics

## Default Login Accounts

You can use these sample accounts to test the app:

- Admin: `admin@creator.com` / `admin123`
- Seller: `seller@creator.com` / `seller123`
- Buyer: `buyer@creator.com` / `buyer123`

## Run the App

From the project folder, run:

```bash
py -m streamlit run creator_marketplace.py
```

Then open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## App Structure

The app includes:

- Dashboard overview
- Product catalog
- Shopping cart
- Creator management
- Orders page
- Analytics dashboard
- Support center

## Notes

This app is designed as a realistic marketplace prototype and can be extended with a database, backend API, payment integration, and admin controls.
