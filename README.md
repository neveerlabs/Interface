# Interface

**Alat Bantu Pengujian Jaringan & Spesifikasi Perangkat**  
Dikembangkan dari seorang siswa untuk Uji Kompetensi Keahlian (UKK) Teknik Komputer & Jaringan (TKJ)  
Fokus konfigurasi router MikroTik RB750 / RB941

---

## Fitur

- **Monitor Jaringan Real-time**  
  SSID, Interface, Method (Static/DHCP), IP clien, MAC Address, IPv6, Subnet Mask, Gateway, IP Publik, Status koneksi & Internet.

- **Pemindaian Jaringan**  
  Deteksi semua perangkat yang terhubung dalam satu subnet menggunakan `nmap`, `arp-scan`, atau fallback ping sweep.

- **Ping Interaktif**  
  Ping DNS, Google, router/gateway, antar router, atau antar klien dengan tampilan output langsung seperti di terminal.

- **Ubah IP Dinamis**  
  Pindah mode IP Static ↔ Dynamic (DHCP) lewat `nmcli` atau perintah manual. IP statis lama otomatis dibersihkan.

- **Informasi Perangkat Lengkap**  
  Hardware: hostname, merek, model, serial number, resolusi layar, RAM, CPU, GPU, disk, partisi, NIC, USB.  
  Software: OS, kernel, arsitektur, desktop environment, init system, BIOS, motherboard.

---

## Persyaratan Sistem

- **Sistem Operasi**: Kali Linux (atau distribusi Linux lain dengan NetworkManager)
- **Paket Sistem** (wajib):
  - `nmap` (untuk pemindaian optimal)
  - `arp-scan` (cadangan jika nmap tidak tersedia)
  - `ethtool` (mendeteksi driver & bus NIC)
  - `curl` (mengambil IP publik)
  - `iwgetid` (untuk WiFi, biasanya sudah terinstal)
  - `iproute2` (`ip` command)
  - `sudo` (untuk perubahan IP dan akses serial)
  - `NetworkManager` (`nmcli`) – direkomendasikan untuk ubah IP

- **Python 3.8+**  
- **Pip**: lihat `requirements.txt`  
- **Hak akses root** (`sudo`) untuk beberapa fitur (Ubah IP, pemindaian penuh)

---

## Instalasi & Menjalankan

```bash
# 1. Clone repositori
git clone https://github.com/neveerlabs/Interface.git
cd Interface

# 3. Install dependensi
pip install questionary

# 4. Jalankan dengan hak root (agar fitur ubah IP & scan penuh berfungsi)
sudo /home/user/venv/bin/python app.py
```

## Penggunaan
Setelah script berjalan, kamu akan disambut menu interaktif (gunakan panah atas/bawah & Enter):
* **`Display Network Specifications`** – Tampilkan info jaringan lengkap
* **`Display Device Specifications`** – Tampilkan spesifikasi perangkat
* **`Ping DNS / Google / Router / Gateway / Between Router / Between Clients`** – Jalankan ping ke target pilihan
* **`Change IP (Static / Dynamic)`** – Ubah mode IP
* **`Check IP Addresses of All Clients on the Network`** – Pindai jaringan
* **`Exit`** – Keluar

## Catatan Penting
- Jalankan dengan `sudo` agar fitur pemindaian (nmap) mendeteksi semua perangkat, dan pengubahan IP berjalan mulus.
- Jika tidak menggunakan `sudo`, beberapa informasi (seperti serial number) mungkin tidak terbaca.
- Seluruh output **berbahasa Inggris** untuk kemudahan dokumentasi, namun mudah dipahami.
- Script tidak menyimpan log ke file, semua bersifat sementara.

---

## Kontribusi
Kontribusi sangat diterima! Silakan buka issue atau pull request.

---

## Lisensi
MIT License. Bebas digunakan, dimodifikasi, dan disebarluaskan.
