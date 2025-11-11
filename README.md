# 🚗 Vehicle Parking Management System - "LOT AND FOUND"

A comprehensive Flask-based web application for managing parking lots, reservations, and payments across various industries.

## 🌟 Features

### 👤 **User Features**
- **Account Management**: Registration, login, profile management
- **Parking Search**: Filter by location, price, and type (shaded/open)
- **Real-time Booking**: Reserve available parking spots instantly
- **Payment System**: Automatic cost calculation based on parking duration
- **History Tracking**: View past reservations and transactions
- **Mobile Responsive**: Works seamlessly on all devices

### 👨‍💼 **Admin Features**
- **Lot Management**: Create, edit, and delete parking lots
- **User Management**: View and monitor all registered users
- **Reservation Monitoring**: Track all active and completed bookings
- **Analytics Dashboard**: Occupancy statistics and revenue reports
- **Spot Control**: Individual parking spot status management
- **Dynamic Pricing**: Set different rates for different lot types

## 🏗️ **Technology Stack**

- **Backend**: Flask (Python)
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **ORM**: SQLAlchemy
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Authentication**: Flask-Login with session management
- **Forms**: Flask-WTF with CSRF protection
- **Icons**: Font Awesome
- **Deployment**: Gunicorn WSGI server

## 📁 **Project Structure**

```
parking-app/
├── app.py                 # Main application file
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── login.html        # Login page
│   ├── signup.html       # Registration page
│   ├── profile.html      # User profile
│   ├── view_lot.html     # Lot details
│   ├── admin/            # Admin templates
│   │   ├── admin_dashboard.html
│   │   ├── admin_nav.html
│   │   ├── new_lot.html
│   │   ├── edit_lot.html
│   │   ├── view_users.html
│   │   ├── admin_summary.html
│   │   ├── admin_chart.html
│   │   └── spot_details.html
│   └── user/             # User templates
│       ├── user_dashboard.html
│       ├── user_nav.html
│       ├── book_spot.html
│       ├── release_spot.html
│       ├── payment.html
│       ├── user_summary.html
│       └── transaction_history.html
├── static/               # Static files
│   ├── style.css        # Custom CSS
│   └── images/          # Images and icons
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
├── Procfile            # Depl
---
