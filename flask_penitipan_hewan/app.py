from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "petcare_secret"
DB = "petcare.db"


def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute("""CREATE TABLE IF NOT EXISTS pemilik (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT,
        telepon TEXT,
        alamat TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS hewan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_hewan TEXT,
        jenis TEXT,
        pemilik_id INTEGER,
        kandang TEXT,
        check_in TEXT,
        check_out TEXT,
        status TEXT,
        FOREIGN KEY (pemilik_id) REFERENCES pemilik(id) ON DELETE CASCADE
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS reservasi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pemilik_id INTEGER,
        nama_hewan TEXT,
        telp TEXT,
        alamat TEXT,
        jenis TEXT,
        check_in TEXT,
        check_out TEXT,
        catatan TEXT,
        status TEXT,
        FOREIGN KEY (pemilik_id) REFERENCES pemilik(id) ON DELETE CASCADE
    )""")
    conn.commit()
    conn.close()

init_db()


USERNAME = "admin"
PASSWORD = "admin123"

@app.route("/", methods=["GET"])
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u==USERNAME and p==PASSWORD:
            session["username"]=u
            flash("Login berhasil!","success")
            return redirect(url_for("dashboard"))
        else:
            flash("Username atau password salah!","error")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Anda telah logout.","info")
    return redirect(url_for("login"))



@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    hewan = conn.execute("""
        SELECT h.*, p.nama AS pemilik_nama 
        FROM hewan h 
        JOIN pemilik p ON h.pemilik_id=p.id
    """).fetchall()
    conn.close()

    total = len(hewan)
    dirawat = sum(1 for h in hewan if h["status"]=="Dirawat")
    siap = sum(1 for h in hewan if h["status"]=="Selesai")

    return render_template("dashboard.html",
        username=session["username"],
        total_hewan=total,
        sedang_dirawat=dirawat,
        siap_ambil=siap,
        today=date.today(),
        pelanggan=hewan
    )


@app.route("/reservasi", methods=["GET","POST"])
def reservasi():
    if "username" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    if request.method=="POST":
        nama_pemilik=request.form["pemilik"]
        telp=request.form["telp"]
        alamat=request.form["alamat"]
        nama_hewan=request.form["nama_hewan"]
        jenis=request.form["jenis"]
        checkin=request.form["checkin"]
        checkout=request.form["checkout"]
        catatan=request.form["catatan"]

        pemilik = conn.execute("SELECT * FROM pemilik WHERE nama=?",(nama_pemilik,)).fetchone()
        if not pemilik:
            cur = conn.execute("INSERT INTO pemilik (nama,telepon,alamat) VALUES (?,?,?)",(nama_pemilik,telp,alamat))
            pemilik_id = cur.lastrowid
        else:
            pemilik_id = pemilik["id"]

        conn.execute("""INSERT INTO reservasi (pemilik_id,nama_hewan,telp,alamat,jenis,check_in,check_out,catatan,status)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                     (pemilik_id,nama_hewan,telp,alamat,jenis,checkin,checkout,catatan,"Menunggu Check-in"))

        conn.execute("""INSERT INTO hewan (nama_hewan,jenis,pemilik_id,kandang,check_in,check_out,status)
                        VALUES (?,?,?,?,?,?,?)""",
                     (nama_hewan,jenis,pemilik_id,"-",checkin,checkout,"Dirawat"))
        conn.commit()
        flash("Reservasi berhasil disimpan & data otomatis ditambahkan!","success")
        return redirect(url_for("reservasi"))

    reservasi = conn.execute("""SELECT r.*, p.nama AS pemilik_nama
                               FROM reservasi r
                               JOIN pemilik p ON r.pemilik_id=p.id""").fetchall()
    conn.close()
    return render_template("reservasi.html", data=reservasi)


@app.route("/hewan")
def data_hewan():
    if "username" not in session:
        return redirect(url_for("login"))
    conn=get_db_connection()
    hewan=conn.execute("""SELECT h.*, p.nama AS pemilik_nama 
                          FROM hewan h 
                          JOIN pemilik p ON h.pemilik_id=p.id""").fetchall()
    conn.close()
    return render_template("data_hewan.html", data=hewan)


@app.route("/pemilik")
def data_pemilik():
    if "username" not in session:
        return redirect(url_for("login"))
    conn=get_db_connection()
    pemilik=conn.execute("SELECT * FROM pemilik").fetchall()
    conn.close()
    return render_template("data_pemilik.html", data=pemilik)


@app.route("/hewan/hapus/<int:id>")
def hapus_hewan(id):
    if "username" not in session:
        return redirect(url_for("login"))
    conn=get_db_connection()
    hewan=conn.execute("SELECT * FROM hewan WHERE id=?",(id,)).fetchone()
    if hewan:
        conn.execute("DELETE FROM reservasi WHERE nama_hewan=? AND pemilik_id=?",(hewan["nama_hewan"], hewan["pemilik_id"]))
        conn.execute("DELETE FROM hewan WHERE id=?",(id,))
        conn.commit()
        flash("Data hewan dan reservasi terkait berhasil dihapus!","success")
    else:
        flash("Hewan tidak ditemukan!","error")
    conn.close()
    return redirect(url_for("data_hewan"))


@app.route("/pemilik/hapus/<int:id>")
def hapus_pemilik(id):
    if "username" not in session:
        return redirect(url_for("login"))
    conn=get_db_connection()
    pemilik=conn.execute("SELECT * FROM pemilik WHERE id=?",(id,)).fetchone()
    if pemilik:
        conn.execute("DELETE FROM pemilik WHERE id=?",(id,))
        conn.commit()
        flash("Data pemilik, hewan, dan reservasi terkait berhasil dihapus!","success")
    else:
        flash("Pemilik tidak ditemukan!","error")
    conn.close()
    return redirect(url_for("data_pemilik"))


@app.route("/pengaturan", methods=["GET","POST"])
def pengaturan():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method=="POST":
        action=request.form.get("action")
        global PASSWORD
        if action=="ubah_tema":
            session["tema"]=request.form.get("tema")
            flash(f"Tema berhasil diubah menjadi {session['tema']}!","success")

        elif action=="ganti_password":
            old=request.form.get("old_password")
            new=request.form.get("new_password")
            if old!=PASSWORD:
                flash("Password lama salah!","error")
            else:
                PASSWORD=new
                flash("Password berhasil diubah!","success")
                
        elif action=="hapus_akun":
            conn=get_db_connection()
            conn.execute("DELETE FROM reservasi")
            conn.execute("DELETE FROM hewan")
            conn.execute("DELETE FROM pemilik")
            conn.commit()
            conn.close()
            session.pop("username", None)
            flash("Akun dan semua data berhasil dihapus!","info")
            return redirect(url_for("login"))
        return redirect(url_for("pengaturan"))

    return render_template("pengaturan.html", today=date.today())


@app.route("/reset-data")
def reset_data():
    conn=get_db_connection()
    conn.execute("DELETE FROM reservasi")
    conn.execute("DELETE FROM hewan")
    conn.execute("DELETE FROM pemilik")
    conn.commit()
    conn.close()
    flash("Semua data berhasil dihapus!","info")
    return redirect(url_for("pengaturan"))


if __name__=="__main__":
    app.run(debug=True)
