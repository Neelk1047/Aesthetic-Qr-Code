# Aesthetic-Qr-Code
Flask-based web app to generate aesthetic, multi-link QR codes with color extraction and same Wi-Fi access restriction. Includes login system, multiple QR styles (classic, gradient, logo), and personalized QR management. (Future plan: enable QR access over cellular data with secure token-based validation.)

Hey there! 
Ever wished you could share **multiple links using a single QR code** without cluttering everything?  
That's exactly what this project does! "Aesthetic QR Code Generator" lets you create **stylish QR codes** that can contain **multiple destinations** — and for now, they only work when you're on the **same Wi-Fi**.  

*(Don’t worry, I plan to make it work over cellular data in the future!)*

##  What It Can Do

- **Login & Personal Dashboard** – keeps your QR codes private and **tracks all previously generated QR codes**  
- **Keeps track of count** – Keeps count for qr scans and links clicked 
- **Multiple Links in One QR** – no more managing 5 different QR codes  
- **Three QR Styles** – Classic, Gradient, or Logo-based  
- **Color Extraction** – pick an image/logo, and the QR color will match  
- **Local Access Only (for now)** – QR works only on the same Wi-Fi  

## Teckstack

I built this with the help of **Python and web technologies**:

 Backend | Python 3, Flask |
 Auth | Flask-Login |
 Database | SQLite + Flask-SQLAlchemy |
 Frontend | HTML, CSS, JavaScript |
 QR & Image | Pillow (PIL), qrcode
 Color Extraction | ColorThief 
 Tunneling (for testing on phone) | pyngrok (optional) inprogress
 Tools | Git, VS Code, pip, virtualenv |


##  How To Use

1. **Login or Register** (simple and secure)
2. **Click On Create QR
3. **Enter Title** — e.g., `Portfolio`
4. **Upload an Image or Logo** — optional, for color matching
5. **Add Links** — GitHub, LinkedIn, Portfolio, whatever you want
6. **Choose QR Style** — Classic, Gradient, or Logo
7. **Click Generate** — three beautiful QR codes appear
8.  **Dashboard Keeps Track** — see all previously generated QR codes anytime
9.   **Scan it** — and see all your links in one place (works on the same Wi-Fi)  

**Example:**  

Imagine you want to share your GitHub, LinkedIn, and personal website in one QR code. Just add all three links, pick a style, and boom! Three QR codes are generated. Your dashboard automatically logs them so you can reuse or review later 😎  


## Project Structure
QR_CODE_/

├── app.py
├── debug_render_dashboard.py
├── requirements.txt
├── static/
│   ├── qrcodes/
│   ├── uploads/
│   ├── app.js
│   ├── styled_qr.png
│   └── styles.css
├── templates/
│   ├── about.html
│   ├── base.html
│   ├── dashboard.html
│   ├── features.html
│   ├── home.html
│   ├── index.html
│   ├── landing.html
│   ├── login.html
│   └── register.html
├── instance/
│   └── qr_project.db
└── __pycache__/ 


##setup->

# Clone the repo
git clone https://github.com/<your-username>/aesthetic-qr-code.git
cd aesthetic-qr-code

# Create virtual environment
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
