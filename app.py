import os
import time
import uuid  #useful for db keys, filename
from flask import Flask, render_template, request, url_for, redirect, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required 
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image, ImageDraw, ImageColor, ImageFilter, ImageOps

try:
    from colorthief import ColorThief
    COLOR_THIEF_AVAILABLE = True
except ImportError:
    COLOR_THIEF_AVAILABLE = False

import qrcode
import sys
import socket
import numpy as np

# --- App & Database Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-and-secure-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qr_project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['PUBLIC_HOST'] = os.environ.get('PUBLIC_HOST')

app.config['PUBLIC_PORT'] = os.environ.get('PUBLIC_PORT', '5000')

def detect_local_ip():
    """Try to detect a non-loopback LAN IP for this host."""
    try:
        # UDP connect to an external address doesn't send packets but lets the OS select a suitable interface
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith('127.'):
                return ip
    except Exception:
        pass
    return None

# If PUBLIC_HOST not provided,  to auto-detect a LAN IP and use it(to be completed in-progress)
if not app.config.get('PUBLIC_HOST'):
    local_ip = detect_local_ip()
    if local_ip:
        app.config['PUBLIC_HOST'] = f"http://{local_ip}:{app.config.get('PUBLIC_PORT', '5000')}"
    else:
        # Leave PUBLIC_HOST unset if detection failed; user can set it explicitly.
        app.config['PUBLIC_HOST'] = None

# if PUBLIC_HOST is still unset and pyngrok is installed, open a public tunnel and use it.
try:
    from pyngrok import ngrok
    PYNGROK_AVAILABLE = True
except Exception:
    PYNGROK_AVAILABLE = False

if not app.config.get('PUBLIC_HOST') and PYNGROK_AVAILABLE:
    try:
        try:
            ngrok_port = int(app.config.get('PUBLIC_PORT', 5000))
        except Exception:
            ngrok_port = 5000

        # If user provided an ngrok auth token via env, register it (optional)
        ngrok_token = os.environ.get('NGROK_AUTHTOKEN') or os.environ.get('NGROK_AUTH_TOKEN')
        if ngrok_token:
            try:
                ngrok.set_auth_token(ngrok_token)
            except Exception:
                pass

        tunnel = ngrok.connect(ngrok_port, bind_tls=True)
        public_url = tunnel.public_url
        app.config['PUBLIC_HOST'] = public_url
        print(f"Auto ngrok tunnel started: {public_url} -> localhost:{ngrok_port}")
    except Exception as e:
        print("pyngrok failed to create a tunnel or is not configured properly:", e)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


STATIC_FOLDER_NAME = "static"
UPLOAD_SUBDIR = "uploads"
QR_SUBDIR = "qrcodes"
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER_NAME, UPLOAD_SUBDIR)
QR_FOLDER = os.path.join(STATIC_FOLDER_NAME, QR_SUBDIR)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)


STYLES = ["classic", "gradient", "logo"]



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    qrcodes = db.relationship('QRCode', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class QRCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(150), nullable=False)
    
    logo_path = db.Column(db.String(255), nullable=False) 
    scan_count = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    links = db.relationship('QRLink', backref='qrcode', lazy=True, cascade="all, delete-orphan")
    generated_files = db.relationship('GeneratedFile', backref='qrcode', lazy=True, cascade="all, delete-orphan")

class QRLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    click_count = db.Column(db.Integer, default=0)
    qr_id = db.Column(db.Integer, db.ForeignKey('qr_code.id'), nullable=False)
    
class GeneratedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    style = db.Column(db.String(50), nullable=False)
   
    file_path = db.Column(db.String(255), nullable=False)
    qr_id = db.Column(db.Integer, db.ForeignKey('qr_code.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




def extract_dominant_colors(image_path, num_colors=3):
    """Extracts dominant colors using ColorThief if available, otherwise defaults."""
    if COLOR_THIEF_AVAILABLE:
        try:
            color_thief = ColorThief(image_path)
            palette = ['#%02x%02x%02x' % color for color in color_thief.get_palette(color_count=num_colors)]
            return palette
        except Exception:
            
            pass 
    
    
    return ["#000000", "#FFFFFF"]

def create_styled_qr(data_url, logo_full_path, style):
    """Creates a styled QR code pointing to our app's landing page."""
    
    
    if not os.path.exists(logo_full_path):
        raise FileNotFoundError(f"Logo file not found at: {logo_full_path}")
        
    colors = extract_dominant_colors(logo_full_path)
    fill_color = colors[0]
    back_color = colors[1] if len(colors) > 1 else "#FFFFFF"
    
    filename = f"{style}_{int(time.time())}_{str(uuid.uuid4())[:8]}.png"
    output_full_path = os.path.join(STATIC_FOLDER_NAME, QR_SUBDIR, filename)
    output_relative_path = os.path.join(QR_SUBDIR, filename).replace(os.path.sep, '/')

    qr = qrcode.QRCode(version=6, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(data_url)
    qr.make(fit=True)
    
    qr_img = None
    
    if style == "logo":
        # Simpler, scannable logo style
        base_qr_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGBA")

        # Load and prepare the logo for the center
        logo_img = Image.open(logo_full_path).convert("RGBA")
        # Calculate center size 
        logo_size_factor = 0.25 #size of logo 
        center_size = int(base_qr_img.size[0] * logo_size_factor)
        logo_img = logo_img.resize((center_size, center_size), Image.Resampling.LANCZOS)

        # Create a circular mask for the center logo
        mask = Image.new('L', (center_size, center_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, center_size, center_size), fill=255)

        offset = ( (base_qr_img.size[0] - center_size) // 2, (base_qr_img.size[1] - center_size) // 2 )

        qr_img = base_qr_img.copy()
        qr_img.paste(logo_img, offset, mask=mask)

    elif style == "gradient":
        qr_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGBA")
        
        # Simple top-to-bottom color gradient for aesthetic effect
        gradient_layer = Image.new("RGBA", qr_img.size)
        draw = ImageDraw.Draw(gradient_layer)
        width, height = gradient_layer.size
        
         
        try:
            start_rgb = ImageColor.getrgb(fill_color)
        except ValueError:
            # Fallback if the color format is somehow bad
            start_rgb = (0, 0, 0)
            
        end_rgb = (255, 255, 255)
        

        for y in range(height):
            # Interpolate color
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * y / height)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * y / height)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * y / height)
            
            # Apply color with low opacity over the QR image
            draw.line([(0, y), (width, y)], fill=(r, g, b, 50)) # Alpha 50/255
            
        qr_img = Image.alpha_composite(qr_img, gradient_layer)

    else: # classic
        qr_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGBA")

    if qr_img:
        qr_img.save(output_full_path)
    
    return output_relative_path


# --- Routes ---

@app.route("/", methods=["GET"])
def index():
    # Public landing page
    return render_template('home.html')


@app.route("/create", methods=["GET", "POST"])
def create():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form.get("title")
        image = request.files.get("image")
        selected_styles = request.form.getlist("styles")
        labels = request.form.getlist("labels[]")
        urls = request.form.getlist("urls[]")

        # --- Validation ---
        if not title:
            return jsonify({"success": False, "message": "A title for your QR code is required."})

        if not image or not image.filename:
            return jsonify({"success": False, "message": "A logo image is required."})

        if not selected_styles:
            return jsonify({"success": False, "message": "Please select at least one QR code style."})

       
        link_pairs = [(l, u) for l, u in zip(labels, urls) if l.strip() and u.strip()]

        # --- File & Data Processing ---
        filename = f"{int(time.time())}_{image.filename}"
        logo_full_path = os.path.join(STATIC_FOLDER_NAME, UPLOAD_SUBDIR, filename)
        logo_relative_path = os.path.join(UPLOAD_SUBDIR, filename).replace(os.path.sep, '/')

        try:
            image.save(logo_full_path)
        except Exception as e:
            print(f"ERROR SAVING LOGO FILE: {e}")
            return jsonify({"success": False, "message": f"Could not save logo file. Error: {e}"})

        new_qr = QRCode(title=title, logo_path=logo_relative_path, owner=current_user)
        
        for label, url in link_pairs:
            new_link = QRLink(label=label, url=url)
            new_qr.links.append(new_link)

        db.session.add(new_qr)
        db.session.commit()

        public_host = app.config.get('PUBLIC_HOST')
        if public_host:
            landing_page_url = public_host.rstrip('/') + url_for('qr_landing', unique_id=new_qr.unique_id)
        else:
            landing_page_url = url_for('qr_landing', unique_id=new_qr.unique_id, _external=True)

        qr_paths = []
        for style in selected_styles:
            try:
                generated_path_relative = create_styled_qr(landing_page_url, logo_full_path, style)

                file_entry = GeneratedFile(style=style, file_path=generated_path_relative, qrcode=new_qr)
                db.session.add(file_entry)

                web_path = url_for('static', filename=generated_path_relative)
                qr_paths.append(web_path)
            except Exception as e:
                print(f"ERROR GENERATING QR CODE ({style}): {e}")
                continue

        db.session.commit()

        if not qr_paths:
            return jsonify({"success": False, "message": "Could not generate any QR codes. Please check the server logs for detailed errors."})

        return jsonify({"success": True, "qr_paths": qr_paths})

    return render_template("index.html", styles=STYLES)

# The public-facing landing page for a QR code
@app.route("/qr/<unique_id>")
def qr_landing(unique_id):
    qr_code = QRCode.query.filter_by(unique_id=unique_id).first_or_404()
    
    # Increment scan count
    qr_code.scan_count += 1
    db.session.commit()
    
    return render_template("landing.html", qr_code=qr_code)

# The redirector that tracks clicks
@app.route("/redirect/<int:link_id>")
def redirect_link(link_id):
    link = QRLink.query.get_or_404(link_id)
    
    # Increment click count
    link.click_count += 1
    db.session.commit()
    
    return redirect(link.url)

# --- User & Dashboard Routes ---
@app.route("/dashboard")
@login_required
def dashboard():
    user_qrs = QRCode.query.filter_by(user_id=current_user.id).order_by(QRCode.id.desc()).all()
    return render_template("dashboard.html", user_qrs=user_qrs)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error="Username already exists.")
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/features")
def features():
    return render_template("features.html")


@app.route('/about')
def about():
    return render_template('about.html')



if __name__ == "__main__":
    #  database tables if they don't exist
    with app.app_context():
        db.create_all()
    public_host = app.config.get('PUBLIC_HOST')
    
    is_debugger = sys.gettrace() is not None
    try:
        if public_host:
            try:
                port = int(os.environ.get('PUBLIC_PORT', 5000))
            except Exception:
                port = 5000
        else:
            port = int(os.environ.get('PUBLIC_PORT', 5000)) if os.environ.get('PUBLIC_PORT') else 5000

       
        print(f"STARTUP: PUBLIC_HOST={public_host!r} is_debugger={is_debugger} port={port} file={__file__}")
        sys.stdout.flush()

        
        if public_host:
            app.run(host='0.0.0.0', port=port, debug=(not is_debugger), use_reloader=False)
        else:
            app.run(debug=(not is_debugger), use_reloader=False)
    except SystemExit as se:
       
        try:
            code = int(se.code)
        except Exception:
            code = se.code
        if code == 3:
            print(f"Ignored SystemExit with code 3 from app.run (debugger interaction). Message: {se}")
        else:
            raise