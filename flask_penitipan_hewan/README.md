# Flask Penitipan Hewan (Pet Care)

Aplikasi web untuk sistem penitipan hewan berbasis Flask dengan MySQL.

## Persyaratan Sistem

- Python 3.8 atau lebih baru
- MySQL Server
- Git (opsional)

## Instalasi

1. **Clone atau download project ini**

2. **Install dependencies Python:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Database MySQL:**
   - Pastikan MySQL Server sudah terinstall dan berjalan
   - Buat database baru (opsional, aplikasi akan membuat otomatis jika belum ada):
     ```sql
     CREATE DATABASE petcare;
     ```
   - Konfigurasi koneksi database ada di `app.py` (default: localhost, user: root, password: kosong)

4. **Jalankan aplikasi:**
   ```bash
   python app.py
   ```

5. **Akses aplikasi:**
   - Buka browser dan kunjungi: `http://localhost:5000`

## Fitur Utama

- **Admin Dashboard:** Kelola reservasi, adopsi, donasi, dan sukarelawan
- **User Dashboard:** Buat reservasi, adopsi, donasi, dan pendaftaran sukarelawan
- **Laporan:** Export data ke Excel dan PDF
- **Sistem Pesan:** Komunikasi antara admin dan user

## Akun Default

**Admin:**
- Email: admin@example.com
- Password: admin123

**User:**
- Email: user1@example.com
- Password: user123

## Struktur Project

```
flask_penitipan_hewan/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── static/               # Static files (CSS, JS, images)
│   ├── css/
│   ├── images/
│   └── uploads/
├── templates/            # HTML templates
│   ├── admin/           # Admin templates
│   └── user/            # User templates
└── README.md            # This file
```

## Teknologi yang Digunakan

- **Backend:** Flask (Python)
- **Database:** MySQL
- **Frontend:** HTML, CSS, Bootstrap
- **Libraries:** pandas, reportlab, openpyxl

## Troubleshooting

1. **Error koneksi database:**
   - Pastikan MySQL Server berjalan
   - Periksa konfigurasi di `app.py`
   - Pastikan user MySQL memiliki akses ke database

2. **Port 5000 sudah digunakan:**
   - Ubah port di `app.py` atau stop aplikasi lain yang menggunakan port tersebut

3. **Import error:**
   - Pastikan semua dependencies terinstall dengan `pip install -r requirements.txt`

## Lisensi

Project ini dibuat untuk keperluan edukasi.
