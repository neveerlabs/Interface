<div align="center">

# Interface

**Alat Bantu Pengujian Jaringan & Spesifikasi Perangkat**  
Dikembangkan dari seorang siswa untuk Uji Kompetensi Keahlian (UKK) Teknik Komputer & Jaringan (TKJ)  
Fokus konfigurasi router MikroTik RB750 / RB941  

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python)](https://www.python.org/)
[![Kali Linux](https://img.shields.io/badge/Kali_Linux-2024.1-blue?logo=kalilinux)](https://www.kali.org/)
[![nmap](https://img.shields.io/badge/nmap-7.99-red?logo=nmap)](https://nmap.org/)
[![arp--scan](https://img.shields.io/badge/arp--scan-1.10.0-lightgrey)](https://github.com/royhills/arp-scan)
[![NetworkManager](https://img.shields.io/badge/NetworkManager-orange?logo=networkmanager)](https://networkmanager.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## Fitur

- **Monitor Jaringan Real-time**  
  SSID, Interface, Method (Static/DHCP), IP clien, MAC Address, IPv6, Subnet Mask, Gateway, IP Publik, Status koneksi & Internet.

- **Pemindaian Jaringan**  
  Deteksi semua perangkat yang terhubung dalam satu subnet menggunakan `nmap`, `arp-scan`, atau fallback ping sweep.

- **Ping Interaktif**  
  Ping DNS, Google, router/gateway, antar router, atau antar klien dengan tampilan output real-time.

- **Ubah IP Dynamic**  
  Pindah mode IP Static ↔ Dynamic (DHCP) lewat `nmcli` atau perintah manual. IP static yang lama otomatis dibersihkan.

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

- **Python 3.13+**  
- **Hak akses root** (`sudo`) untuk beberapa fitur (Ubah IP, pemindaian penuh)

---

## Instalasi & Menjalankan

```bash
# 1. Clone repositori
git clone https://github.com/neveerlabs/Interface.git
cd Interface

# 3. Install dependensi
pip install questionary

# 4 Install arp-scan & nmap
sudo apt install arp-scan -y && sudo apt install nmap -y

# 5. Jalankan dengan hak root (agar fitur ubah IP & scan penuh berfungsi)
sudo /home/user/venv/bin/python app.py
```

## Penggunaan
Setelah script berjalan, input nya menggunakan keyboard scrollbar (gunakan panah atas/bawah & Enter):

* **`Display Network Specifications`** – Tampilkan info jaringan lengkap

* **`Display Device Specifications`** – Tampilkan spesifikasi perangkat

* **`Ping DNS / Google / Router / Gateway / Between Router / Between Clients`** – Jalankan ping ke target

* **`Change IP (Static / Dynamic)`** – Ubah method

* **`Check IP Addresses of All Clients on the Network`** – Pindai clint jaringan

* **`Exit`** – Keluar

## Catatan Penting
- Jalankan dengan `sudo` agar fitur pemindaian (nmap) mendeteksi semua perangkat, dan pengubahan IP berjalan mulus.
- Jika tidak menggunakan `sudo`, beberapa informasi (seperti serial number) mungkin tidak terbaca.
- Tkes output menggunakan **bahasa Inggris United States (US)** untuk kemudahan dokumentasi, dan mudah dipahami (Jangan dikomen ya guys, itu teksnya hasil translate di google).
- Script tidak menyimpan log ke file, dan tidak ada data yang dsimpan / dikirim ke server manapun.

---

## Lisensi
MIT License. Bebas digunakan, dimodifikasi, dan disebarluaskan.


<div align="center">

`Made with by Neverlabs | © 2026`

[![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://wa.me/628561765372)
[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://instagram.com/neveerlabs)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/neveerlabs)
[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/Neverlabs)
[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:userlinuxorg@gmail.com)

</div>
