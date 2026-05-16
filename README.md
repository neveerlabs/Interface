<div align="center">

# Interface

**Alat Bantu Pengujian Jaringan, Spesifikasi Perangkat & Manajemen Hotspot WiFi**  
Dikembangkan oleh seorang siswa untuk Uji Kompetensi Keahlian (UKK) Teknik Komputer & Jaringan (TKJ)  
Fokus konfigurasi router MikroTik RB750 / RB941  

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python)](https://www.python.org/)
[![Kali Linux](https://img.shields.io/badge/Kali_Linux-2024.1-blue?logo=kalilinux)](https://www.kali.org/)
[![nmap](https://img.shields.io/badge/nmap-7.99-red?logo=nmap)](https://nmap.org/)
[![arp--scan](https://img.shields.io/badge/arp--scan-1.10.0-lightgrey)](https://github.com/royhills/arp-scan)
[![NetworkManager](https://img.shields.io/badge/NetworkManager-orange?logo=networkmanager)](https://networkmanager.dev/)
[![License: GPL-3.0](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/neveerlabs/Interface/blob/main/LICENSE)

</div>

---

## Fitur

- **Monitor Jaringan Real-time**  
  SSID, Interface, Method (Static/DHCP), IP clien, MAC Address, IPv6, Subnet Mask, Gateway, IP Publik, Status koneksi & Internet.

- **Pemindaian Jaringan**  
  Scan semua perangkat yang terhubung dalam satu subnet menggunakan `nmap`, `arp-scan`, atau fallback ping sweep.

- **Ping Interaktif**  
  Ping DNS, Google, router/gateway, antar router, atau antar klien dengan tampilan output secara real-time.

- **Ubah IP Dynamic**  
  Ubah IP Static ↔ Dynamic (DHCP) lewat `nmcli` atau perintah manual. IP static yang lama otomatis dibersihkan.

- **Informasi Perangkat Lengkap**  
  Hardware: hostname, merek, model, serial number, resolusi layar, RAM, CPU, GPU, disk, partisi, NIC, USB.  
  Software: OS, kernel, arsitektur, desktop environment, init system, BIOS, motherboard.

- **Manajemen Hotspot WiFi**  
  Buat, edit, dan hapus konfigurasi hotspot WiFi. aktifkan, hentikan, atau restart server hotspot kapan saja. Dilengkapi monitoring log DHCP secara langsung dan kemampuan untuk melihat detail perangkat yang sedang terhubung. Konfigurasi disimpan otomatis dan server hotspot dapat berjalan di latar belakang tanpa mengganggu menu utama. *(hanya tersedia di Linux dengan `hostapd` & `dnsmasq`)*

---

## Persyaratan Sistem

- **Sistem Operasi**: Kali Linux (atau distribusi Linux lain dengan NetworkManager)
- **Paket Sistem** (wajib):
  - `nmap` (untuk pemindaian client secara optimal)
  - `arp-scan` (cadangan jika nmap tidak tersedia)
  - `ethtool` (mendeteksi driver & bus NIC)
  - `curl` (mengambil IP publik)
  - `iwgetid` (untuk WiFi, biasanya udah terinstal)
  - `iproute2` (`ip` command)
  - `sudo` (untuk perubahan IP dan akses root)
  - `NetworkManager` (`nmcli`) – direkomendasikan untuk mengubah IP
  - `hostapd` (untuk membuat access point)
  - `dnsmasq` (untuk DHCP server hotspot)
- **Wireshark**
- **Python 3.13+**  
- **Hak akses root** (`sudo`) untuk beberapa fitur (Ubah IP, pemindaian penuh, manajemen hotspot)

---

## Instalasi & Menjalankan

* Clone repositori
  ```bash
  git clone https://github.com/neveerlabs/Interface.git
  cd Interface
  ```
* Install dependensi
  ```bash
  pip install -r requirements.txt
  ```
* Install arp-scan & nmap
  ```bash
  sudo apt install arp-scan -y && sudo apt install nmap -y
  ```
* Instalasi library di os Linux (Desktop / Server)
  ```bash
  sudo apt install -y python3-pip nmap arp-scan ethtool iproute2 curl hostapd dnsmasq
  pip install questionary
  ```
* Windows Native (tanpa WSL)
  * Install Python 3 dari `https://python.org`.
  * Install `Nmap` dari `https://nmap.org/download.html`.
  * Buka PowerShell (run dengan `run administrator`), jalankan:
  ```bash
  pip install questionary
  ```
  > Catatan: *Fitur hotspot tidak tersedia di Windows.*
* Windows dengan WSL
  * Di dalam WSL, perlakukan seperti lingkungan Linux.
  * Pastikan network mode WSL menggunakan mirrored atau bridge agar mendapatkan IP yang sesuai.
  * Fitur hotspot mungkin memerlukan konfigurasi tambahan.
* Android (di termux)
  ```bash
  pkg update && pkg upgrade
  pkg install python python-pip nmap ethtool iproute2 curl
  pip install questionary
  ```
  > Catatan: *Beberapa fitur mungkin gak bisa digunakan karena bukan root. Hotspot tidak tersedia di Termux.*
* iOS (Tidak Didukung)
> *Script tidak dapat berjalan di iOS karena kebijakan keamanan Apple!*
* Linux: `sudo apt install wireshark -y` (Debian/Ubuntu), `sudo pacman -S wireshark` (Arch), `sudo dnf install wireshark` (Fedora)
* Windows: Download dari `https://www.wireshark.org/download.html`, pastikan centang "Install Wireshark" dan "TShark" saat instalasi, dan tambahkan ke PATH.
* Termux: Tidak mendukung (akan muncul pesan khusus).
* Jalankan dengan hak root (agar fitur ubah IP, scan penuh, dan hotspot berfungsi)
  ```bash
  sudo /home/{user}/venv/bin/python app.py

  # Atau
  sudo python3 app.py
  ```

## Penggunaan
Setelah script berjalan, input nya menggunakan keyboard scrollbar (gunakan panah atas/bawah & Enter):
* `Display Network Specifications` – Tampilkan info jaringan
* `Display Device Specifications` – Tampilkan spesifikasi perangkat
* `Ping DNS / Google / Router / Gateway / Between Router / Between Clients` – Jalankan ping ke target
* `Change IP (Static / Dynamic)` – Ubah method
* `Check IP Addresses of All Clients on the Network` – Scsn client jaringan
* `Manage Hotspot` – Masuk ke sub-menu untuk mengatur hotspot WiFi:
  * `Create WiFi Hotspot` – Membuat konfigurasi hotspot baru (SSID, password, IP, DHCP pool, sumber internet (ISP)). Konfigurasi disimpan ke dalam file.
  * `Edit Configuration` – Mengubah konfigurasi yang sudah ada.
  * `Delete Configuration` – Menghapus konfigurasi.
  * `Start Hotspot Server` – Menjalankan server hotspot berdasarkan konfigurasian yg dipilih. Hotspot akan terus berjalan meski Anda keluar dari sub-menu `Manage Hotspot`, selama aplikasi utama (Interface) masih terus berjalan.
  * `Restart Hotspot Server` – Menghentikan lalu menjalankan kembali server.
  * `Stop Hotspot Server` – Mematikan server hotspot. Semua aturan NAT dan interface dikembalikan seperti semula.
  * `Monitor Log` – Menampilkan log DHCP terbaru dari `dnsmasq` secara langsung (`tekan Ctrl+C` untuk kembali).
  * `View Connected Devices` – Melihat perangkat yang sedang terhubung ke hotspot beserta detailnya.
* `Run Wireshark` – Buka aplikasi `Wireshark`. Jika belum terinstal, maka akan dibei tau cara install-nya. Tekan `Ctrl+C` kapan aja untuk nutup Wireshark dan balik ke menu utama.
* `Exit` – Keluar

## Catatan Penting
* Jalankan dengan `sudo` agar fitur pemindaian (nmap) mendeteksi semua perangkat, pengubahan IP, dan hotspot berjalan mulus.
* Jika tidak menggunakan `sudo`, beberapa informasi (seperti serial number) mungkin tidak terbaca.
* Teks output menggunakan **bahasa Inggris United States (US)** untuk kemudahan dokumentasi, dan mudah dipahami.
* Script tidak menyimpan log ke file secara permanen, dan tidak ada data yang dikirim ke server manapun (kecuali konfigurasi hotspot yang disimpan lokal di file JSON).
* Fitur Wireshark hanya tersedia di Linux & Windows (Termux, iOS, WSL tanpa GUI mungkin terbatas).
* Jika Wireshark gak kedetect, script bakal ngasih instruksi instalasi sesuai OS.
* Tekan `Ctrl+C` saat Wireshark berjalan akan menghentikan proses Wireshark dan mengembalikan kontrol ke script **tanpa keluar dari script Interface**.
* Wireshark butuh akses root atau CAP_NET_RAW untuk packet capture. jadi, pastikan script dijalankan dengan sudo di Linux, atau "Run as Administrator" di Windows (CMD).
* **Fitur Hotspot**:
  * Hanya berjalan di Linux dengan `hostapd` dan `dnsmasq` terinstal.
  * Jangan gunakan interface AP (wlan0) yang sama untuk koneksi sumber internet (ISP). Pilih interface lain (eth0, wlan1) atau pilih "No internet (LAN only)" karena akan terjadi bentrok.
  * Server hotspot tetap berjalan saat Anda kembali ke menu utama atau menjalankan fitur lain. Untuk menghentikannya, gunakan menu `Stop Hotspot Server` atau keluar dari aplikasi.
  * Saat aplikasi ditutup (termasuk dengan `Ctrl+C`), server hotspot otomatis dimatikan dan semua aturan NAT dibersihkan.

---

Lisensi
GPL-3.0 License. Bebas digunakan, dimodifikasi, dan disebarluaskan.

<div align="center">

`Made with by Neverlabs | © 2026`

https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white
https://img.shields.io/badge/X-000000?style=for-the-badge&logo=x&logoColor=white
https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white
https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white
https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white

</div>
