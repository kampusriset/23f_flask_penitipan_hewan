from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import date
import pandas as pd
from flask import send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = "petcare_secret"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="petcare"
        )
        # Update database schema if needed
        update_database()
        return conn
    except mysql.connector.Error as err:
        if err.errno == 1049:  # Unknown database
            # Create database and tables
            create_database_and_tables()
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="petcare"
            )
            # Update database schema after creating tables
            update_database()
            return conn
        else:
            raise err


def create_database_and_tables():
    """Create database and tables if they don't exist"""
    # Connect without database
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    cursor = conn.cursor()

    # Create database
    cursor.execute("CREATE DATABASE IF NOT EXISTS petcare")
    cursor.execute("USE petcare")

    # Create tables one by one
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            nama VARCHAR(100) DEFAULT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            nama VARCHAR(100) NOT NULL,
            role VARCHAR(20) DEFAULT 'pembeli'
        )
    """)



    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservasi (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama_pemilik VARCHAR(100) NOT NULL,
            telepon VARCHAR(20) NOT NULL,
            alamat TEXT NOT NULL,
            nama_hewan VARCHAR(100) NOT NULL,
            jenis VARCHAR(50) NOT NULL,
            check_in DATE NOT NULL,
            check_out DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'Menunggu',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adopsi (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            nama VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            telp VARCHAR(20) NOT NULL,
            jenis_hewan VARCHAR(50) NOT NULL,
            alasan TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'Menunggu',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donasi (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            nama VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            telp VARCHAR(20) NOT NULL,
            jumlah DECIMAL(10,2) NOT NULL,
            metode VARCHAR(50) NOT NULL,
            bukti_transfer VARCHAR(255),
            status VARCHAR(20) DEFAULT 'Menunggu',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sukarelawan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            nama VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            telp VARCHAR(20) NOT NULL,
            keahlian VARCHAR(100) NOT NULL,
            waktu VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'Menunggu',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pesan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            judul VARCHAR(200) NOT NULL,
            isi TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'Belum Dibaca',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Insert default admin
    cursor.execute("""
        INSERT INTO admin (email, password, nama)
        VALUES ('admin@example.com', 'admin123', 'Administrator')
        ON DUPLICATE KEY UPDATE password='admin123'
    """)

    conn.commit()
    cursor.close()
    conn.close()


def update_database():
    """Update database schema from username to email columns and add new columns"""
    messages = []
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()

        # Use the petcare database
        cursor.execute("USE petcare")

        try:
            # For admin table
            cursor.execute("SHOW COLUMNS FROM admin LIKE 'username'")
            if cursor.fetchone():
                cursor.execute("ALTER TABLE admin CHANGE username email VARCHAR(50) UNIQUE NOT NULL")
                messages.append("Updated admin table: username → email")

            # For users table
            cursor.execute("SHOW COLUMNS FROM users LIKE 'username'")
            if cursor.fetchone():
                cursor.execute("ALTER TABLE users CHANGE username email VARCHAR(50) UNIQUE NOT NULL")
                messages.append("Updated users table: username → email")

            # Add telp and alamat columns to users table if they don't exist
            cursor.execute("SHOW COLUMNS FROM users LIKE 'telp'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN telp VARCHAR(20)")
                messages.append("Added telp column to users table")

            cursor.execute("SHOW COLUMNS FROM users LIKE 'alamat'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN alamat TEXT")
                messages.append("Added alamat column to users table")

            # Add telp and alamat columns to admin table if they don't exist
            cursor.execute("SHOW COLUMNS FROM admin LIKE 'telp'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE admin ADD COLUMN telp VARCHAR(20)")
                messages.append("Added telp column to admin table")

            cursor.execute("SHOW COLUMNS FROM admin LIKE 'alamat'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE admin ADD COLUMN alamat TEXT")
                messages.append("Added alamat column to admin table")

            cursor.execute("SHOW COLUMNS FROM admin LIKE 'tanggal_lahir'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE admin ADD COLUMN tanggal_lahir DATE")
                messages.append("Added tanggal_lahir column to admin table")

            cursor.execute("SHOW COLUMNS FROM admin LIKE 'bio'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE admin ADD COLUMN bio TEXT")
                messages.append("Added bio column to admin table")

            # Add role column to users table if it doesn't exist
            cursor.execute("SHOW COLUMNS FROM users LIKE 'role'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'pembeli'")
                messages.append("Added role column to users table")
                # Set default role for existing users
                cursor.execute("UPDATE users SET role='pembeli' WHERE role IS NULL")
                messages.append("Set default role 'pembeli' for existing users")

            # Add user_id column to reservasi table if it doesn't exist
            cursor.execute("SHOW COLUMNS FROM reservasi LIKE 'user_id'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE reservasi ADD COLUMN user_id INT AFTER id")
                cursor.execute("ALTER TABLE reservasi ADD CONSTRAINT fk_reservasi_user_id FOREIGN KEY (user_id) REFERENCES users(id)")
                messages.append("Added user_id column to reservasi table")

            # Update default data
            cursor.execute("""
                INSERT INTO admin (email, password, nama)
                VALUES ('admin@example.com', 'admin123', 'Administrator')
                ON DUPLICATE KEY UPDATE password='admin123'
            """)

            cursor.execute("""
                INSERT INTO users (email, password, nama)
                VALUES ('user1@example.com', 'user123', 'User Pertama')
                ON DUPLICATE KEY UPDATE password='user123'
            """)

            # Insert sample message for the user if not exists
            cursor.execute("""
                INSERT INTO pesan (user_id, judul, isi, status)
                SELECT 1, 'Selamat Datang di PetCare', 'Terima kasih telah bergabung dengan PetCare! Kami siap membantu Anda dengan layanan penitipan hewan yang terbaik.', 'Belum Dibaca'
                WHERE NOT EXISTS (SELECT 1 FROM pesan WHERE user_id = 1 AND judul = 'Selamat Datang di PetCare')
            """)

            conn.commit()
            messages.append("Database schema updated successfully!")
            messages.append("Default credentials updated!")

        except mysql.connector.Error as e:
            messages.append(f"Error updating database: {e}")
            cursor.close()
            conn.close()
            return False, messages

        cursor.close()
        conn.close()
        return True, messages

    except mysql.connector.Error as e:
        messages.append(f"Database connection error: {e}")
        return False, messages


@app.route("/")
def home():
    return render_template("home.html", session=session)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email dan password harus diisi", "error")
            return redirect(url_for("login"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check admin table first
        cursor.execute(
            "SELECT * FROM admin WHERE email=%s AND password=%s",
            (email, password)
        )
        admin = cursor.fetchone()

        if admin:
            session["email"] = email
            session["role"] = "admin"
            cursor.close()
            conn.close()
            flash("Login admin berhasil", "success")
            return redirect(url_for("admin_dashboard"))

        # Check user table
        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session["email"] = email
            session["role"] = "user"
            session["user_id"] = user["id"]
            session["nama"] = user["nama"]
            flash("Login user berhasil", "success")
            return redirect(url_for("user_dashboard"))

        flash("Email atau password salah", "error")

    return render_template("login.html")






@app.route("/admin/dashboard")
def admin_dashboard():
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM reservasi")
    total_reservasi = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reservasi WHERE status='Menunggu'")
    reservasi_menunggu = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reservasi WHERE status='Diterima'")
    reservasi_selesai = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    total_user = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM donasi")
    total_donasi = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM donasi WHERE status='Menunggu'")
    donasi_menunggu = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM donasi WHERE status='Diterima'")
    donasi_diterima = cursor.fetchone()[0] or 0

    cursor.close()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        today=date.today(),
        total_reservasi=total_reservasi,
        reservasi_menunggu=reservasi_menunggu,
        reservasi_selesai=reservasi_selesai,
        total_user=total_user,
        total_donasi=total_donasi,
        donasi_menunggu=donasi_menunggu,
        donasi_diterima=donasi_diterima
    )



@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Admin berhasil logout", "info")
    return redirect(url_for("home"))



from io import BytesIO

@app.route("/admin/export/reservasi/excel")
def export_reservasi_excel():
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    query = """
        SELECT id, nama_pemilik, telepon, alamat,
               nama_hewan, jenis, check_in, check_out, status
        FROM reservasi
        ORDER BY id DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()

    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    return send_file(
        output,
        download_name="laporan_reservasi.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



from io import BytesIO

@app.route("/admin/export/reservasi/pdf")
def export_reservasi_pdf():
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        styles = getSampleStyleSheet()
        elements = []

        # Main Title
        title = Paragraph("LAPORAN KEGIATAN PENITIPAN HEWAN", styles['Title'])
        elements.append(title)
        elements.append(Paragraph("<br/><br/>", styles['Normal']))

        # RESERVASI SECTION
        elements.append(Paragraph("1. DATA RESERVASI", styles['Heading2']))
        elements.append(Paragraph("<br/>", styles['Normal']))

        cursor.execute("""
            SELECT id, nama_pemilik, nama_hewan, jenis,
                   check_in, check_out, status
            FROM reservasi
            ORDER BY id DESC
        """)
        reservasi_data = cursor.fetchall()

        if reservasi_data:
            table_data = [
                ['ID', 'Nama Pemilik', 'Nama Hewan', 'Jenis', 'Check-in', 'Check-out', 'Status']
            ]

            for row in reservasi_data:
                table_data.append([
                    str(row[0]),
                    row[1],
                    row[2],
                    row[3],
                    str(row[4]),
                    str(row[5]),
                    row[6]
                ])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("Tidak ada data reservasi", styles['Normal']))

        elements.append(Paragraph("<br/><br/>", styles['Normal']))

        # ADOPSI SECTION
        elements.append(Paragraph("2. DATA ADOPSI", styles['Heading2']))
        elements.append(Paragraph("<br/>", styles['Normal']))

        cursor.execute("""
            SELECT id, nama, email, telp, jenis_hewan, created_at, status
            FROM adopsi
            ORDER BY id DESC
        """)
        adopsi_data = cursor.fetchall()

        if adopsi_data:
            table_data = [
                ['ID', 'Nama', 'Email', 'Telepon', 'Jenis Hewan', 'Tanggal', 'Status']
            ]

            for row in adopsi_data:
                table_data.append([
                    str(row[0]),
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    str(row[5]),
                    row[6]
                ])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("Tidak ada data adopsi", styles['Normal']))

        elements.append(Paragraph("<br/><br/>", styles['Normal']))

        # DONASI SECTION
        elements.append(Paragraph("3. DATA DONASI", styles['Heading2']))
        elements.append(Paragraph("<br/>", styles['Normal']))

        cursor.execute("""
            SELECT id, nama, email, telp, jumlah, metode, created_at, status
            FROM donasi
            ORDER BY id DESC
        """)
        donasi_data = cursor.fetchall()

        if donasi_data:
            table_data = [
                ['ID', 'Nama', 'Email', 'Telepon', 'Jumlah', 'Metode', 'Tanggal', 'Status']
            ]

            for row in donasi_data:
                table_data.append([
                    str(row[0]),
                    row[1],
                    row[2],
                    row[3],
                    f"Rp {row[4]:,}",
                    row[5],
                    str(row[6]),
                    row[7]
                ])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("Tidak ada data donasi", styles['Normal']))

        elements.append(Paragraph("<br/><br/>", styles['Normal']))

        # SUKARELAWAN SECTION
        elements.append(Paragraph("4. DATA SUKARELAWAN", styles['Heading2']))
        elements.append(Paragraph("<br/>", styles['Normal']))

        cursor.execute("""
            SELECT id, nama, email, telp, keahlian, waktu, status
            FROM sukarelawan
            ORDER BY id DESC
        """)
        sukarelawan_data = cursor.fetchall()

        if sukarelawan_data:
            # Create centered style for paragraphs
            centered_style = getSampleStyleSheet()['Normal']
            centered_style.alignment = 1  # 0=left, 1=center, 2=right

            table_data = [
                ['ID', 'Nama', 'Email', 'Telepon', 'Keahlian', 'Waktu', 'Status']
            ]

            for row in sukarelawan_data:
                table_data.append([
                    str(row[0]),
                    row[1],
                    row[2],
                    row[3],
                    Paragraph(row[4], centered_style),
                    row[5],
                    row[6]
                ])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("Tidak ada data sukarelawan", styles['Normal']))

        # Generate PDF
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        doc.build(elements)
        output.seek(0)

        cursor.close()
        conn.close()

        return send_file(
            output,
            download_name="laporan_kegiatan.pdf",
            as_attachment=True,
            mimetype="application/pdf"
        )
    except Exception as e:
        # Close database connections in case of error
        try:
            cursor.close()
            conn.close()
        except:
            pass
        # Return error response
        return f"Error generating PDF: {str(e)}", 500






@app.route("/user/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        nama = request.form.get("nama")

        if not email or not password or not nama:
            flash("Email, password, dan nama harus diisi", "error")
            return redirect(url_for("user_register"))

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (email, password, nama, role) VALUES (%s, %s, %s, %s)",
                (email, password, nama, 'pembeli')
            )
            conn.commit()
            user_id = cursor.lastrowid
            session["email"] = email
            session["role"] = "user"
            session["user_id"] = user_id
            session["nama"] = nama
            flash("Akun berhasil dibuat dan Anda telah login!", "success")
            return redirect(url_for("user_dashboard"))
        except:
            flash("Email sudah digunakan!", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template("user/register.html")


@app.route("/user/dashboard")
def user_dashboard():
    if "email" not in session or session.get("role") != "user":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get user data
    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()

    # Get accepted reservations for the user
    cursor.execute("""
        SELECT * FROM reservasi
        WHERE user_id = %s AND status = 'Diterima'
        ORDER BY created_at DESC
        LIMIT 5
    """, (session["user_id"],))
    accepted_reservations = cursor.fetchall()

    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM reservasi WHERE user_id = %s AND status = 'Diterima'", (session["user_id"],))
    result = cursor.fetchone()
    reservasi_aktif = result['COUNT(*)'] if result else 0

    cursor.execute("SELECT COUNT(*) FROM reservasi WHERE user_id = %s", (session["user_id"],))
    result = cursor.fetchone()
    total_pemesanan = result['COUNT(*)'] if result else 0

    cursor.execute("SELECT COUNT(*) FROM pesan WHERE user_id = %s AND status = 'Belum Dibaca'", (session["user_id"],))
    result = cursor.fetchone()
    pesan_masuk = result['COUNT(*)'] if result else 0

    # Get recent activities from all tables
    recent_activities = []

    # Get recent reservations
    cursor.execute("""
        SELECT 'Reservasi' as type, nama_hewan as title, created_at, status
        FROM reservasi
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 3
    """, (session["user_id"],))
    reservations = cursor.fetchall()
    for r in reservations:
        icon = "✅" if r['status'] == 'Diterima' else "⏳" if r['status'] == 'Menunggu' else "❌"
        recent_activities.append({
            'icon': icon,
            'title': f"Reservasi {r['title']}",
            'time': r['created_at'].strftime('%d/%m/%Y %H:%M') if r['created_at'] else 'N/A'
        })

    # Get recent adopsi
    cursor.execute("""
        SELECT 'Adopsi' as type, jenis_hewan as title, created_at, status
        FROM adopsi
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 3
    """, (session["user_id"],))
    adopsi = cursor.fetchall()
    for a in adopsi:
        icon = "✅" if a['status'] == 'Diterima' else "⏳" if a['status'] == 'Menunggu' else "❌"
        recent_activities.append({
            'icon': icon,
            'title': f"Adopsi {a['title']}",
            'time': a['created_at'].strftime('%d/%m/%Y %H:%M') if a['created_at'] else 'N/A'
        })

    # Get recent donasi
    cursor.execute("""
        SELECT 'Donasi' as type, jumlah as title, created_at, status
        FROM donasi
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 3
    """, (session["user_id"],))
    donasi = cursor.fetchall()
    for d in donasi:
        icon = "✅" if d['status'] == 'Diterima' else "⏳" if d['status'] == 'Menunggu' else "❌"
        recent_activities.append({
            'icon': icon,
            'title': f"Donasi Rp {d['title']:,}",
            'time': d['created_at'].strftime('%d/%m/%Y %H:%M') if d['created_at'] else 'N/A'
        })

    # Get recent sukarelawan
    cursor.execute("""
        SELECT 'Sukarelawan' as type, keahlian as title, created_at, status
        FROM sukarelawan
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 3
    """, (session["user_id"],))
    sukarelawan = cursor.fetchall()
    for s in sukarelawan:
        icon = "✅" if s['status'] == 'Diterima' else "⏳" if s['status'] == 'Menunggu' else "❌"
        recent_activities.append({
            'icon': icon,
            'title': f"Sukarelawan - {s['title']}",
            'time': s['created_at'].strftime('%d/%m/%Y %H:%M') if s['created_at'] else 'N/A'
        })

    # Get recent messages
    cursor.execute("""
        SELECT 'Pesan' as type, judul as title, created_at, status
        FROM pesan
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 3
    """, (session["user_id"],))
    messages = cursor.fetchall()
    for m in messages:
        icon = "💬"
        recent_activities.append({
            'icon': icon,
            'title': f"Pesan: {m['title']}",
            'time': m['created_at'].strftime('%d/%m/%Y %H:%M') if m['created_at'] else 'N/A'
        })

    # Sort all activities by time and take top 5
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = recent_activities[:5]

    cursor.close()
    conn.close()

    return render_template(
        "user/dashboard.html",
        email=session["email"],
        today=date.today(),
        user=user,
        accepted_reservations=accepted_reservations,
        reservasi_aktif=reservasi_aktif,
        total_pemesanan=total_pemesanan,
        pesan_masuk=pesan_masuk,
        recent_activities=recent_activities
    )


@app.route("/user/profil", methods=["GET", "POST"])
def user_profil():
    if "email" not in session or session.get("role") != "user":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if request.method == "POST":
        nama = request.form.get("nama")
        email = request.form.get("email")
        telp = request.form.get("telp")
        alamat = request.form.get("alamat")

        if not all([nama, email, telp]):
            flash("Nama, email, dan telepon harus diisi", "error")
            return redirect(url_for("user_profil"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET nama=%s, email=%s, telp=%s, alamat=%s WHERE id=%s
        """, (nama, email, telp, alamat, session["user_id"]))
        conn.commit()
        cursor.close()
        conn.close()

        session["nama"] = nama
        session["email"] = email
        flash("Profil berhasil diperbarui", "success")
        return redirect(url_for("user_profil"))

    return render_template("user/edit_profil.html", user=user, today=date.today())


@app.route("/user/pemesanan", methods=["GET", "POST"])
def user_pemesanan():
    if "email" not in session or session.get("role") != "user":
        return redirect(url_for("login"))

    if request.method == "POST":
        nama_pemilik = request.form["pemilik_nama"]
        telp = request.form["telp"]
        alamat = request.form["alamat"]
        nama_hewan = request.form["nama_hewan"]
        jenis = request.form["jenis_hewan"]
        checkin = request.form["check_in"]
        checkout = request.form["check_out"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reservasi
            (user_id, nama_pemilik, telepon, alamat, nama_hewan, jenis, check_in, check_out, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session["user_id"],
            nama_pemilik,
            telp,
            alamat,
            nama_hewan,
            jenis,
            checkin,
            checkout,
            "Menunggu"
        ))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Reservasi berhasil dikirim!", "success")
        return redirect(url_for("user_dashboard"))

    return render_template("user/pemesanan.html")


@app.route("/user/logout")
def user_logout():
    session.clear()
    flash("User berhasil logout", "info")
    return redirect(url_for("home"))


@app.route("/user/reservasi", methods=["GET", "POST"])
def user_reservasi():
    if "email" not in session or session.get("role") != "user":
        return redirect(url_for("login"))

    if request.method == "POST":
        nama_pemilik = request.form["pemilik_nama"]
        telp = request.form["telp"]
        alamat = request.form["alamat"]
        nama_hewan = request.form["nama_hewan"]
        jenis = request.form["jenis_hewan"]
        checkin = request.form["check_in"]
        checkout = request.form["check_out"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reservasi
            (user_id, nama_pemilik, telepon, alamat, nama_hewan, jenis, check_in, check_out, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session["user_id"],
            nama_pemilik,
            telp,
            alamat,
            nama_hewan,
            jenis,
            checkin,
            checkout,
            "Menunggu"
        ))


        conn.commit()
        cursor.close()
        conn.close()

        flash("Reservasi berhasil dikirim!", "success")
        return redirect(url_for("user_dashboard"))

    return render_template("user/form_reservasi.html")


@app.route("/admin/reservasi")
def admin_reservasi():
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
    SELECT * FROM reservasi
    ORDER BY id DESC
    """)

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("admin/data_reservasi.html", data=data)


@app.route("/admin/reservasi/hapus/<int:id>")
def admin_reservasi_hapus(id):
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reservasi WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Reservasi berhasil dihapus", "info")
    return redirect(url_for("admin_reservasi"))


@app.route("/admin/reservasi/terima/<int:id>")
def admin_reservasi_terima(id):
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM reservasi WHERE id=%s",
        (id,)
    )
    r = cursor.fetchone()

    if not r:
        flash("Reservasi tidak ditemukan", "error")
        cursor.close()
        conn.close()
        return redirect(url_for("admin_reservasi"))



    cursor.execute(
        "UPDATE reservasi SET status=%s WHERE id=%s",
        ("Diterima", id)
    )

    # Send confirmation message to user
    if r.get("user_id") and r["user_id"] is not None:
        cursor.execute("""
            INSERT INTO pesan (user_id, judul, isi, status)
            VALUES (%s, %s, %s, %s)
        """, (
            r["user_id"],
            "Reservasi Diterima",
            f"Reservasi Anda untuk {r['nama_hewan']} ({r['jenis']}) telah diterima. Check-in: {r['check_in']}, Check-out: {r['check_out']}. Terima kasih telah mempercayakan hewan Anda kepada kami!",
            "Belum Dibaca"
        ))
        flash("Reservasi diterima & pesan konfirmasi dikirim ke user", "success")
    else:
        flash("Reservasi diterima, tetapi pesan konfirmasi tidak dapat dikirim karena data user tidak lengkap", "warning")

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_reservasi"))


@app.route("/admin/reservasi/tolak/<int:id>")
def admin_reservasi_tolak(id):
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM reservasi WHERE id=%s", (id,))
    r = cursor.fetchone()

    if not r:
        flash("Reservasi tidak ditemukan", "error")
        cursor.close()
        conn.close()
        return redirect(url_for("admin_reservasi"))

    cursor.execute(
        "UPDATE reservasi SET status=%s WHERE id=%s",
        ("Ditolak", id)
    )

    # Send rejection message to user
    if r.get("user_id") and r["user_id"] is not None:
        cursor.execute("""
            INSERT INTO pesan (user_id, judul, isi, status)
            VALUES (%s, %s, %s, %s)
        """, (
            r["user_id"],
            "Reservasi Ditolak",
            f"Maaf, reservasi Anda untuk {r['nama_hewan']} ({r['jenis']}) telah ditolak. Silakan hubungi kami untuk informasi lebih lanjut.",
            "Belum Dibaca"
        ))
        flash("Reservasi ditolak & pesan penolakan dikirim ke user", "warning")
    else:
        flash("Reservasi ditolak, tetapi pesan penolakan tidak dapat dikirim karena data user tidak lengkap", "warning")

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_reservasi"))
















@app.route("/user/adopsi", methods=["GET", "POST"])
def user_adopsi():
    if "email" not in session or session.get("role") != "user":
        return redirect(url_for("login"))

    # Get user data for auto-filling form
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if request.method == "POST":
        user_id = session.get("user_id")
        nama = request.form.get("nama")
        email = request.form.get("email")
        telp = request.form.get("telp")
        jenis_hewan = request.form.get("jenis_hewan")
        alasan = request.form.get("alasan")

        if not all([nama, email, telp, jenis_hewan, alasan]):
            flash("Semua field wajib diisi", "error")
            return redirect(url_for("user_adopsi"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO adopsi (user_id, nama, email, telp, jenis_hewan, alasan, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, nama, email, telp, jenis_hewan, alasan, "Menunggu"))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Form adopsi berhasil dikirim", "success")
        return redirect(url_for("user_dashboard"))

    return render_template("user/form_adopsi.html", user=user)



@app.route("/admin/data_adopsi")
def admin_adopsi():
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM adopsi ORDER BY id DESC")
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("admin/data_adopsi.html", data=data)


@app.route("/admin/adopsi/terima/<int:id>")
def admin_adopsi_terima(id):
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM adopsi WHERE id=%s", (id,))
    adopsi = cursor.fetchone()

    if not adopsi:
        flash("Data adopsi tidak ditemukan", "error")
        cursor.close()
        conn.close()
        return redirect(url_for("admin_adopsi"))

    cursor.execute(
        "UPDATE adopsi SET status='Diterima' WHERE id=%s",
        (id,)
    )

    cursor.execute("""
        INSERT INTO pesan (user_id, judul, isi, status)
        VALUES (%s, %s, %s, %s)
    """, (
        adopsi["user_id"],
        "Adopsi Diterima",
        f"Adopsi Anda untuk hewan {adopsi['jenis_hewan']} telah diterima. Terima kasih sudah merawatnya!",
        "Belum Dibaca"
    ))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Adopsi diterima & pesan dikirim ke user", "success")
    return redirect(url_for("admin_adopsi"))


@app.route("/admin/adopsi/tolak/<int:id>")
def adopsi_tolak(id):
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM adopsi WHERE id=%s", (id,))
    adopsi = cursor.fetchone()

    if not adopsi:
        flash("Data adopsi tidak ditemukan", "error")
        cursor.close()
        conn.close()
        return redirect(url_for("admin_adopsi"))

    cursor.execute("UPDATE adopsi SET status=%s WHERE id=%s", ("Ditolak", id))

    # Send rejection message to user
    if adopsi.get("user_id") and adopsi["user_id"] is not None:
        cursor.execute("""
            INSERT INTO pesan (user_id, judul, isi, status)
            VALUES (%s, %s, %s, %s)
        """, (
            adopsi["user_id"],
            "Adopsi Ditolak",
            f"Maaf, permohonan adopsi Anda untuk hewan {adopsi['jenis_hewan']} telah ditolak. Silakan hubungi kami untuk informasi lebih lanjut.",
            "Belum Dibaca"
        ))
        flash("Adopsi ditolak & pesan penolakan dikirim ke user", "warning")
    else:
        flash("Adopsi ditolak, tetapi pesan penolakan tidak dapat dikirim karena data user tidak lengkap", "warning")

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_adopsi"))


@app.route("/admin/adopsi/hapus/<int:id>")
def adopsi_hapus(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM adopsi WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_adopsi"))


@app.route("/user/donasi", methods=["GET", "POST"])
def user_donasi():
    if "email" not in session or session.get("role") != "user":
        return redirect(url_for("login"))

    if request.method == "POST":
        user_id = session.get("user_id")
        nama = request.form.get("nama")
        email = request.form.get("email")
        telp = request.form.get("telp")
        jumlah = request.form.get("jumlah")
        metode = request.form.get("metode")

        if not all([user_id, nama, email, telp, jumlah, metode]):
            flash("Semua field wajib diisi", "error")
            return redirect(url_for("user_donasi"))

        # Handle file upload
        bukti_transfer = None
        if 'bukti_transfer' in request.files:
            file = request.files['bukti_transfer']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to make filename unique
                import time
                filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                bukti_transfer = filename
            elif file and file.filename != '':
                flash("Format file tidak didukung. Gunakan PNG, JPG, JPEG, atau GIF", "error")
                return redirect(url_for("user_donasi"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO donasi (user_id, nama, email, telp, jumlah, metode, bukti_transfer)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            nama,
            email,
            telp,
            jumlah,
            metode,
            bukti_transfer
        ))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Donasi berhasil dikirim", "success")
        return redirect(url_for("user_dashboard"))

    return render_template("user/form_donasi.html")


@app.route("/admin/data_donasi")
def admin_data_donasi():
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM donasi ORDER BY id DESC")
    donasi = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("admin/data_donasi.html", donasi=donasi)


@app.route("/admin/donasi/terima/<int:id>")
def admin_donasi_terima(id):
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM donasi WHERE id=%s", (id,))
    donasi = cursor.fetchone()

    if not donasi:
        flash("Data donasi tidak ditemukan", "error")
        return redirect(url_for("admin_data_donasi"))

    cursor.execute(
        "UPDATE donasi SET status='Diterima' WHERE id=%s",
        (id,)
    )

    # Send confirmation message to user
    cursor.execute("""
        INSERT INTO pesan (user_id, judul, isi, status)
        VALUES (%s, %s, %s, %s)
    """, (
        donasi["user_id"],
        "Donasi Diterima",
        f"Donasi Anda sebesar Rp {donasi['jumlah']} telah diterima. Terima kasih atas kontribusi Anda untuk membantu hewan-hewan yang membutuhkan!",
        "Belum Dibaca"
    ))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Donasi berhasil diterima", "success")
    return redirect(url_for("admin_data_donasi"))


@app.route("/admin/donasi/hapus/<int:id>")
def donasi_hapus(id):
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM donasi WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_data_donasi"))


@app.route("/user/sukarelawan", methods=["GET", "POST"])
def user_sukarelawan():
    if "email" not in session or session.get("role") != "user":
        return redirect(url_for("login"))

    if request.method == "POST":
        user_id = session.get("user_id")
        nama = request.form.get("nama")
        email = request.form.get("email")
        telp = request.form.get("telp")
        keahlian = request.form.get("keahlian")
        waktu = request.form.get("waktu")

        if not all([nama, email, telp, keahlian, waktu]):
            flash("Semua field wajib diisi", "error")
            return redirect(url_for("user_sukarelawan"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sukarelawan (user_id, nama, email, telp, keahlian, waktu)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            nama,
            email,
            telp,
            keahlian,
            waktu
        ))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Pendaftaran sukarelawan berhasil dikirim", "success")
        return redirect(url_for("user_dashboard"))

    return render_template("user/form_sukarelawan.html")


@app.route("/admin/data_sukarelawan")
def admin_sukarelawan():
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sukarelawan ORDER BY id DESC")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin/data_sukarelawan.html", data=data)


@app.route("/admin/sukarelawan/terima/<int:id>")
def admin_sukarelawan_terima(id):
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM sukarelawan WHERE id=%s", (id,))
    sukarelawan = cursor.fetchone()

    if not sukarelawan:
        flash("Data sukarelawan tidak ditemukan", "error")
        cursor.close()
        conn.close()
        return redirect(url_for("admin_sukarelawan"))

    cursor.execute(
        "UPDATE sukarelawan SET status='Diterima' WHERE id=%s",
        (id,)
    )

    cursor.execute("""
        INSERT INTO pesan (user_id, judul, isi, status)
        VALUES (%s, %s, %s, %s)
    """, (
        sukarelawan["user_id"],
        "Pendaftaran Sukarelawan Diterima",
        "Pendaftaran sukarelawan anda telah diterima. Terima kasih telah bergabung.",
        "Belum Dibaca"
    ))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Sukarelawan diterima & pesan dikirim ke user", "success")
    return redirect(url_for("admin_sukarelawan"))


@app.route("/admin/sukarelawan/tolak/<int:id>")
def sukarelawan_tolak(id):
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sukarelawan SET status=%s WHERE id=%s", ("Ditolak", id))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_sukarelawan"))


@app.route("/admin/sukarelawan/hapus/<int:id>")
def sukarelawan_hapus(id):
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sukarelawan WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_sukarelawan"))


@app.route("/user/pesan")
def user_pesan():
    if "email" not in session or session.get("role") != "user":
        flash("Silakan login terlebih dahulu", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    if not user_id:
        flash("User tidak valid, silakan login ulang", "error")
        return redirect(url_for("login"))

    user_id = int(user_id)  # Ensure user_id is integer

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM pesan
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    pesan = cursor.fetchall()
    cursor.close()
    conn.close()

    # Debug: Print session info and messages
    print(f"DEBUG: Session user_id: {session.get('user_id')}, type: {type(session.get('user_id'))}")
    print(f"DEBUG: Converted user_id: {user_id}")
    print(f"DEBUG: Messages found: {len(pesan)}")
    for msg in pesan:
        print(f"DEBUG: Message ID {msg['id']}: {msg['judul']}")

    return render_template("user/pesan.html", data=pesan)


@app.route("/pengaturan", methods=["GET","POST"])
def pengaturan():
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    # Ensure database schema is up to date
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check and add missing columns to admin table
    try:
        cursor.execute("SHOW COLUMNS FROM admin LIKE 'telp'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE admin ADD COLUMN telp VARCHAR(20)")
            print("Added telp column to admin table")

        cursor.execute("SHOW COLUMNS FROM admin LIKE 'alamat'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE admin ADD COLUMN alamat TEXT")
            print("Added alamat column to admin table")

        cursor.execute("SHOW COLUMNS FROM admin LIKE 'bio'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE admin ADD COLUMN bio TEXT")
            print("Added bio column to admin table")

        conn.commit()
    except Exception as e:
        print(f"Database update error: {e}")
        cursor.close()
        conn.close()
        flash("Database schema error. Please contact administrator.", "error")
        return redirect(url_for("admin_dashboard"))

    cursor.close()
    conn.close()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admin WHERE email = %s", (session["email"],))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            nama = request.form.get("nama")
            email = request.form.get("email")
            telp = request.form.get("telp")
            alamat = request.form.get("alamat")
            bio = request.form.get("bio")

            if not all([nama, email]):
                flash("Nama dan email harus diisi", "error")
                return redirect(url_for("pengaturan"))

            # Handle password change if provided
            password_lama = request.form.get("password_lama")
            password_baru = request.form.get("password_baru")
            password_konfirmasi = request.form.get("password_konfirmasi")

            if password_lama or password_baru or password_konfirmasi:
                if not password_lama:
                    flash("Masukkan password lama untuk mengubah password", "error")
                    return redirect(url_for("pengaturan"))
                if password_baru != password_konfirmasi:
                    flash("Password baru dan konfirmasi password tidak cocok", "error")
                    return redirect(url_for("pengaturan"))
                if len(password_baru) < 6:
                    flash("Password baru minimal 6 karakter", "error")
                    return redirect(url_for("pengaturan"))

                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT password FROM admin WHERE email=%s", (session["email"],))
                admin_data = cursor.fetchone()

                if not admin_data or admin_data["password"] != password_lama:
                    flash("Password lama salah", "error")
                    cursor.close()
                    conn.close()
                    return redirect(url_for("pengaturan"))

                cursor.execute("UPDATE admin SET password=%s WHERE email=%s", (password_baru, session["email"]))
                conn.commit()
                cursor.close()
                conn.close()

            # Update profile
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE admin SET nama=%s, email=%s, telp=%s, alamat=%s, bio=%s WHERE email=%s
            """, (nama, email, telp, alamat, bio, session["email"]))
            conn.commit()
            cursor.close()
            conn.close()

            session["email"] = email
            flash("Profil berhasil diperbarui", "success")
            return redirect(url_for("pengaturan"))

        return redirect(url_for("pengaturan"))

    return render_template("admin/pengaturan.html", admin=admin, today=date.today())


@app.route("/reset-data")
def reset_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM reservasi")

    conn.commit()
    cursor.close()
    conn.close()

    flash("Semua data berhasil dihapus!", "info")
    return redirect(url_for("pengaturan"))


@app.route("/admin/update_db")
def admin_update_db():
    if "email" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    success, messages = update_database()

    if success:
        flash("Database berhasil diupdate!", "success")
    else:
        flash("Gagal update database!", "error")

    for msg in messages:
        flash(msg, "info")

    return redirect(url_for("pengaturan"))


if __name__ == "__main__":
    app.run(debug=True)
