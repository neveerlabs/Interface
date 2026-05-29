const translations = {
  en: {
    home: "Home", documentation: "Documentation", changelog: "Changelog",
    features: "Features", about: "About", getting_started: "Getting Started",
    commands_reference: "Commands Reference", tutorials: "Tutorials",
    ping_tools: "Ping Tools", ip_changer: "IP Changer",
    network_scanner: "Network Scanner", hotspot_manager: "Hotspot Manager",
    wireshark: "Wireshark",
    hero_badge: "v3.1.9 — Now Available",
    hero_title: "Network\nCommand\nCenter",
    hero_subtitle: "Simplify network diagnostics, scanning, and management with a clean, modern terminal toolkit.",
    get_started: "Get Started", github: "GitHub",
    stat_tools: "Tools", stat_platforms: "Platforms", stat_license: "License",
    features_tag: "Features",
    features_heading: "Everything you need to manage your network",
    features_subheading: "Built for Linux power users, security researchers, and network administrators.",
    view_all_features: "View All Features",
    platform_tag: "Compatibility",
    platform_title: "Cross-Platform Support",
    platform_subtitle: "Run Interface on your preferred environment",
    os_linux: "Linux", os_linux_short: "Kali / Ubuntu / Arch",
    os_windows: "Windows", os_windows_short: "Native Win32",
    os_wsl_short: "Windows + WSL2",
    os_android_short: "via Termux",
    os_ios_short: "Apple devices",
    badge_full: "Full Support", badge_partial: "Partial",
    badge_limited: "Limited", badge_none: "Not Supported",
    feat1_title: "Network Scanner", feat1_desc: "Instantly discover every device on your local network with detailed host info and open ports.",
    feat2_title: "Hotspot Manager", feat2_desc: "Create secure Wi-Fi hotspots and monitor connected clients in real time.",
    feat3_title: "Device Info", feat3_desc: "Detailed hardware specifications and system information at your fingertips.",
    features_page_title: "All Features",
    features_page_subtitle: "A complete toolkit for network diagnostics, management, and analysis.",
    feat_scanner_title: "Network Scanner",
    feat_scanner_desc: "Discover all active hosts on your local network using ARP and nmap. Retrieves IP addresses, MAC addresses, hostnames, and vendor information for each device.",
    feat_hotspot_title: "Hotspot Manager",
    feat_hotspot_desc: "Create and manage Wi-Fi access points using hostapd and dnsmasq. Supports custom SSID, password, channel, and DHCP range configuration with real-time client monitoring.",
    feat_device_title: "Device Info",
    feat_device_desc: "Display comprehensive hardware and system information including CPU, memory, OS version, kernel, and all network interfaces with their current configuration.",
    feat_ping_title: "Ping Tools",
    feat_ping_desc: "Advanced ping utilities with configurable packet count, interval, and size. Includes traceroute, latency graphing, and continuous ping with colored output.",
    feat_ip_title: "IP Changer",
    feat_ip_desc: "Change your network interface IP address, subnet mask, and gateway. Supports both DHCP and static configuration on Linux and Windows via netsh.",
    feat_wireshark_title: "Wireshark Integration",
    feat_wireshark_desc: "Launch Wireshark or tshark directly from the menu with pre-built capture filters. Capture on any interface and export session data for offline analysis.",
    feat_update_title: "Auto Update Checker",
    feat_update_desc: "Automatically checks the GitHub repository for new versions on startup. Displays the full changelog for any pending updates and prompts for confirmation before applying.",
    docs_tag: "Documentation", docs_title: "Documentation",
    docs_subtitle: "Everything you need to get Interface running on your machine.",
    docs_nav_title: "Contents",
    docs_gs_subtitle: "Follow these steps to install and run Interface on your system.",
    docs_step1_title: "Clone the Repository",
    docs_step1_desc: "Download the source code from GitHub using git.",
    docs_step2_title: "Install Dependencies",
    docs_step2_desc: "Install the required Python packages and system tools.",
    docs_step3_title: "Run Interface",
    docs_step3_desc: "Launch the script with root privileges for full functionality.",
    docs_step4_title: "Windows Setup",
    docs_step4_desc: "On Windows, run as Administrator. Some features require additional tools.",
    cmd_col_name: "Command", cmd_col_desc: "Description", cmd_col_platform: "Platform",
    cmd_scanner: "Scan local network for active hosts using ARP and nmap. Returns IP, MAC, hostname, and vendor.",
    cmd_hotspot: "Create/stop Wi-Fi hotspot. Configure SSID, password, channel, and DHCP range. Requires hostapd & dnsmasq.",
    cmd_ip: "Change IP address of a network adapter. Supports static assignment and DHCP release/renew.",
    cmd_ping: "Send ICMP packets to a target host. Configurable count, interval, and packet size.",
    cmd_wireshark: "Launch Wireshark GUI or tshark CLI for packet capture on a selected interface.",
    cmd_device: "Display system hardware info: CPU, RAM, OS, kernel version, and all network interfaces.",
    cmd_update: "Connect to GitHub to check for new releases and display changelog for pending updates.",
    docs_cmd_subtitle: "All available tools and their descriptions.",
    docs_tut_subtitle: "Step-by-step guides for common use cases.",
    coming_soon: "Coming Soon",
    coming_soon_desc: "Video tutorials and detailed walkthroughs are in progress. Check back soon or contribute on GitHub.",
    changelog_tag: "Changelog", changelog_subtitle: "A complete history of changes, fixes, and new features across all versions.",
    loading: "Loading...",
    about_tag: "About", about_subtitle: "Interface is an open-source Python network toolkit built by Neverlabs.",
    about_project_title: "The Project",
    about_project_desc: "Interface is a terminal-based network utility script written in Python. It was created as a UKK TKJ project by Neverlabs to provide a clean, interactive menu-driven experience for common network administration tasks on Linux, Windows, and Android (Termux).",
    about_project_desc2: "The goal is to make powerful network tools accessible without memorizing complex CLI syntax — just launch and navigate.",
    about_license_title: "License",
    about_license_desc: "Interface is free and open-source software distributed under the GNU General Public License v3.0. You are free to use, modify, and distribute it under the same terms.",
    about_author_title: "Author",
    about_author_desc: "Developed and maintained by Neverlabs. Built as a final project (UKK) for TKJ (Computer and Network Engineering) studies. Contributions are welcome on GitHub.",
    about_contact_title: "Contact & Links",
    error_page: "Page Not Found",
    error_desc: "The page you are looking for does not exist.",
    footer_text: "Interface — Open Source Network Toolkit by Neverlabs — GPL-3.0"
  },
  id: {
    home: "Beranda", documentation: "Dokumentasi", changelog: "Catatan Perubahan",
    features: "Fitur", about: "Tentang", getting_started: "Mulai Cepat",
    commands_reference: "Referensi Perintah", tutorials: "Tutorial",
    ping_tools: "Alat Ping", ip_changer: "Pengubah IP",
    network_scanner: "Pemindai Jaringan", hotspot_manager: "Manajer Hotspot",
    wireshark: "Wireshark",
    hero_badge: "v3.1.9 — Tersedia Sekarang",
    hero_subtitle: "Sederhanakan diagnostik, pemindaian, dan manajemen jaringan dengan perangkat terminal modern yang bersih.",
    get_started: "Mulai", github: "GitHub",
    stat_tools: "Alat", stat_platforms: "Platform", stat_license: "Lisensi",
    features_tag: "Fitur",
    features_heading: "Semua yang Anda butuhkan untuk mengelola jaringan",
    features_subheading: "Dibuat untuk pengguna Linux, peneliti keamanan, dan administrator jaringan.",
    view_all_features: "Lihat Semua Fitur",
    platform_tag: "Kompatibilitas",
    platform_title: "Dukungan Lintas Platform",
    platform_subtitle: "Jalankan Interface di lingkungan pilihan Anda",
    os_linux: "Linux", os_linux_short: "Kali / Ubuntu / Arch",
    os_windows: "Windows", os_windows_short: "Native Win32",
    os_wsl_short: "Windows + WSL2",
    os_android_short: "via Termux",
    os_ios_short: "Perangkat Apple",
    badge_full: "Dukungan Penuh", badge_partial: "Sebagian",
    badge_limited: "Terbatas", badge_none: "Tidak Didukung",
    feat1_title: "Pemindai Jaringan", feat1_desc: "Temukan setiap perangkat di jaringan lokal Anda secara instan beserta info host dan port yang terbuka.",
    feat2_title: "Manajer Hotspot", feat2_desc: "Buat hotspot Wi-Fi yang aman dan pantau klien yang terhubung secara real time.",
    feat3_title: "Info Perangkat", feat3_desc: "Spesifikasi perangkat keras terperinci dan informasi sistem di ujung jari Anda.",
    features_page_title: "Semua Fitur",
    features_page_subtitle: "Toolkit lengkap untuk diagnostik, manajemen, dan analisis jaringan.",
    feat_scanner_title: "Pemindai Jaringan",
    feat_scanner_desc: "Temukan semua host aktif di jaringan lokal menggunakan ARP dan nmap. Mengambil alamat IP, MAC, hostname, dan informasi vendor untuk setiap perangkat.",
    feat_hotspot_title: "Manajer Hotspot",
    feat_hotspot_desc: "Buat dan kelola access point Wi-Fi menggunakan hostapd dan dnsmasq. Mendukung konfigurasi SSID, kata sandi, channel, dan rentang DHCP dengan pemantauan klien real-time.",
    feat_device_title: "Info Perangkat",
    feat_device_desc: "Tampilkan informasi hardware dan sistem secara lengkap termasuk CPU, memori, versi OS, kernel, dan semua antarmuka jaringan beserta konfigurasinya.",
    feat_ping_title: "Alat Ping",
    feat_ping_desc: "Utilitas ping canggih dengan jumlah paket, interval, dan ukuran yang dapat dikonfigurasi. Termasuk traceroute, grafik latensi, dan ping kontinu dengan output berwarna.",
    feat_ip_title: "Pengubah IP",
    feat_ip_desc: "Ubah alamat IP, subnet mask, dan gateway antarmuka jaringan. Mendukung konfigurasi DHCP dan statis di Linux dan Windows via netsh.",
    feat_wireshark_title: "Integrasi Wireshark",
    feat_wireshark_desc: "Luncurkan Wireshark atau tshark langsung dari menu dengan filter tangkapan bawaan. Tangkap pada antarmuka apa pun dan ekspor data sesi untuk analisis offline.",
    feat_update_title: "Pemeriksa Pembaruan Otomatis",
    feat_update_desc: "Secara otomatis memeriksa repositori GitHub untuk versi baru saat startup. Menampilkan changelog lengkap untuk pembaruan yang tertunda.",
    docs_tag: "Dokumentasi", docs_title: "Dokumentasi",
    docs_subtitle: "Semua yang Anda butuhkan untuk menjalankan Interface di mesin Anda.",
    docs_nav_title: "Isi",
    docs_gs_subtitle: "Ikuti langkah-langkah ini untuk menginstal dan menjalankan Interface di sistem Anda.",
    docs_step1_title: "Kloning Repositori",
    docs_step1_desc: "Unduh kode sumber dari GitHub menggunakan git.",
    docs_step2_title: "Instal Dependensi",
    docs_step2_desc: "Instal paket Python yang diperlukan dan alat sistem.",
    docs_step3_title: "Jalankan Interface",
    docs_step3_desc: "Luncurkan skrip dengan hak akses root untuk fungsionalitas penuh.",
    docs_step4_title: "Pengaturan Windows",
    docs_step4_desc: "Di Windows, jalankan sebagai Administrator. Beberapa fitur memerlukan alat tambahan.",
    cmd_col_name: "Perintah", cmd_col_desc: "Deskripsi", cmd_col_platform: "Platform",
    cmd_scanner: "Pindai jaringan lokal untuk host aktif menggunakan ARP dan nmap. Mengembalikan IP, MAC, hostname, dan vendor.",
    cmd_hotspot: "Buat/hentikan hotspot Wi-Fi. Konfigurasi SSID, kata sandi, channel, dan rentang DHCP.",
    cmd_ip: "Ubah alamat IP adapter jaringan. Mendukung penetapan statis dan rilis/perbarui DHCP.",
    cmd_ping: "Kirim paket ICMP ke host target. Jumlah, interval, dan ukuran paket dapat dikonfigurasi.",
    cmd_wireshark: "Luncurkan GUI Wireshark atau CLI tshark untuk pengambilan paket.",
    cmd_device: "Tampilkan info hardware: CPU, RAM, OS, versi kernel, dan semua antarmuka jaringan.",
    cmd_update: "Hubungkan ke GitHub untuk memeriksa rilis baru dan menampilkan changelog.",
    docs_cmd_subtitle: "Semua alat yang tersedia beserta deskripsinya.",
    docs_tut_subtitle: "Panduan langkah demi langkah untuk kasus penggunaan umum.",
    coming_soon: "Segera Hadir",
    coming_soon_desc: "Tutorial video dan panduan mendetail sedang dalam proses. Periksa kembali atau berkontribusi di GitHub.",
    changelog_tag: "Catatan Perubahan", changelog_subtitle: "Riwayat lengkap perubahan, perbaikan, dan fitur baru di semua versi.",
    loading: "Memuat...",
    about_tag: "Tentang", about_subtitle: "Interface adalah toolkit jaringan Python open-source yang dibuat oleh Neverlabs.",
    about_project_title: "Proyek",
    about_project_desc: "Interface adalah skrip utilitas jaringan berbasis terminal yang ditulis dalam Python. Dibuat sebagai proyek UKK TKJ oleh Neverlabs untuk menyediakan pengalaman menu interaktif yang bersih untuk tugas administrasi jaringan umum.",
    about_project_desc2: "Tujuannya adalah membuat alat jaringan yang powerful dapat diakses tanpa menghafal sintaks CLI yang rumit — cukup luncurkan dan navigasi.",
    about_license_title: "Lisensi",
    about_license_desc: "Interface adalah perangkat lunak bebas dan open-source yang didistribusikan di bawah GNU General Public License v3.0. Anda bebas menggunakan, memodifikasi, dan mendistribusikannya.",
    about_author_title: "Penulis",
    about_author_desc: "Dikembangkan dan dipelihara oleh Neverlabs. Dibuat sebagai proyek akhir (UKK) untuk studi TKJ (Teknik Komputer dan Jaringan).",
    about_contact_title: "Kontak & Tautan",
    error_page: "Halaman Tidak Ditemukan",
    error_desc: "Halaman yang Anda cari tidak ada.",
    footer_text: "Interface — Toolkit Jaringan Open Source oleh Neverlabs — GPL-3.0"
  }
};

let currentLang = localStorage.getItem('lang') || 'en';
let currentRoute = '';

function applyLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('lang', lang);
  document.querySelectorAll('[data-translate]').forEach(el => {
    const key = el.getAttribute('data-translate');
    const val = translations[lang]?.[key];
    if (!val) return;
    const hasSVG = el.querySelector('svg');
    if (hasSVG) {
      el.childNodes.forEach(node => {
        if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
          node.textContent = val;
        }
      });
    } else {
      el.textContent = val;
    }
  });
  const flag = lang === 'en' ? 'US' : 'ID';
  document.querySelectorAll('#langText, #mobileLangText').forEach(el => el.textContent = flag);
  document.documentElement.lang = lang;
}

function setTheme(isDark) {
  document.body.classList.toggle('dark', isDark);
  const sun = document.querySelector('.sun-icon');
  const moon = document.querySelector('.moon-icon');
  if (sun) sun.classList.toggle('hidden', isDark);
  if (moon) moon.classList.toggle('hidden', !isDark);
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

const routes = {
  '': 'home', '/': 'home', '/features': 'features',
  '/docs': 'docs', '/changelog': 'changelog', '/about': 'about'
};

function getRoute() {
  const hash = window.location.hash.replace('#', '') || '/';
  const [base, queryString] = hash.split('?');
  const params = new URLSearchParams(queryString);
  const section = params.get('section');
  return { route: routes[base] || 'home', section };
}

async function navigate(routeInfo) {
  const { route, section } = routeInfo;
  if (route === currentRoute && !section) return;
  currentRoute = route;

  const main = document.getElementById('main-content');
  main.innerHTML = '<div class="page-loading"><div class="spinner"></div></div>';

  loadPageCSS(route);

  try {
    const res = await fetch(`pages/${route}.html`);
    if (!res.ok) throw new Error('Not found');
    const html = await res.text();
    main.innerHTML = html;
    applyLanguage(currentLang);
    initPage(route, section);
    setupReveal();
    updateActiveNav(route);
  } catch (e) {
    main.innerHTML = `
      <div class="page-wrapper">
        <div class="container section">
          <div class="page-error">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            <h2 style="font-family:var(--display);font-weight:800;font-size:1.5rem;">${translations[currentLang].error_page}</h2>
            <p>${translations[currentLang].error_desc}</p>
            <a href="#/" class="btn btn-primary" style="margin-top:16px;">Go Home</a>
          </div>
        </div>
      </div>`;
  }
}

function loadPageCSS(route) {
  const cssMap = { home: 'home', features: 'features', docs: 'pages', changelog: 'pages', about: 'pages' };
  const file = cssMap[route];
  if (!file) return;
  const id = `css-${file}`;
  if (!document.getElementById(id)) {
    const link = document.createElement('link');
    link.id = id;
    link.rel = 'stylesheet';
    link.href = `css/${file}.css`;
    document.head.appendChild(link);
  }
}

function updateActiveNav(route) {
  document.querySelectorAll('[data-route]').forEach(el => {
    el.classList.toggle('active-nav', el.dataset.route === route);
  });
}

function initPage(route, section) {
  const inits = { home: initHome, docs: initDocs, changelog: initChangelog };
  if (inits[route]) inits[route](section);
}

function initHome() {}

function initDocs(section) {
  const targetSection = section || 'getting-started';
  const targetId = `docs-${targetSection}`;
  const targetButton = document.querySelector(`.docs-nav-item[data-section="${targetSection}"]`);
  if (targetButton) {
    document.querySelectorAll('.docs-nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.docs-section').forEach(s => s.classList.remove('active'));
    targetButton.classList.add('active');
    const target = document.getElementById(targetId);
    if (target) target.classList.add('active');
  }
  document.querySelectorAll('.docs-nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const sectionName = btn.dataset.section;
      document.querySelectorAll('.docs-nav-item').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.docs-section').forEach(s => s.classList.remove('active'));
      btn.classList.add('active');
      const target = document.getElementById(`docs-${sectionName}`);
      if (target) target.classList.add('active');
    });
  });
}

async function initChangelog() {
  const list = document.getElementById('changelogList');
  if (!list) return;
  try {
    const res = await fetch('data/changelog.json');
    const data = await res.json();
    list.innerHTML = data.map((item, i) => `
      <div class="changelog-item${i === 0 ? ' open' : ''}">
        <div class="changelog-header">
          <div class="changelog-version-row">
            <span class="changelog-version">${item.version}</span>
            <span class="changelog-date">${item.date}</span>
            ${i === 0 ? `<span class="changelog-latest">Latest</span>` : ''}
          </div>
          <svg class="changelog-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>
        </div>
        <div class="changelog-body">
          <ul class="changelog-changes">
            ${item.changes.map(c => `<li class="changelog-change"><span class="change-dot"></span><span>${c}</span></li>`).join('')}
          </ul>
        </div>
      </div>
    `).join('');
    list.querySelectorAll('.changelog-header').forEach(header => {
      header.addEventListener('click', () => {
        const item = header.parentElement;
        const isOpen = item.classList.contains('open');
        list.querySelectorAll('.changelog-item').forEach(i => i.classList.remove('open'));
        if (!isOpen) item.classList.add('open');
      });
    });
  } catch (e) {
    list.innerHTML = '<div class="page-error"><p>Failed to load changelog data.</p></div>';
  }
}

function setupReveal() {
  document.querySelectorAll('.reveal').forEach(el => {
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
  });
  if (window.IntersectionObserver) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          e.target.style.opacity = '';
          e.target.style.transform = '';
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.08 });
    document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
  }
}

function initDropdownHover() {
  const isHoverSupported = window.matchMedia('(hover: hover)').matches;
  if (!isHoverSupported) return;
  const dropdowns = document.querySelectorAll('.dropdown');
  dropdowns.forEach(dropdown => {
    const toggle = dropdown.querySelector('.dropdown-toggle');
    const menu = dropdown.querySelector('.dropdown-menu');
    if (!toggle || !menu) return;
    let hoverTimeout;
    function openDropdown() {
      clearTimeout(hoverTimeout);
      dropdown.classList.add('open');
    }
    function closeDropdown() {
      hoverTimeout = setTimeout(() => {
        dropdown.classList.remove('open');
      }, 100);
    }
    toggle.addEventListener('mouseenter', openDropdown);
    toggle.addEventListener('mouseleave', closeDropdown);
    menu.addEventListener('mouseenter', openDropdown);
    menu.addEventListener('mouseleave', closeDropdown);
  });
}

function init() {
  const savedTheme = localStorage.getItem('theme');
  setTheme(savedTheme !== 'light');
  applyLanguage(currentLang);
  document.getElementById('themeToggle')?.addEventListener('click', () => {
    setTheme(!document.body.classList.contains('dark'));
  });
  ['langToggle', 'mobileLangToggle'].forEach(id => {
    document.getElementById(id)?.addEventListener('click', (e) => {
      e.preventDefault();
      applyLanguage(currentLang === 'en' ? 'id' : 'en');
      document.getElementById('navMenu')?.classList.remove('active');
    });
  });
  const hamburger = document.getElementById('hamburger');
  const navMenu = document.getElementById('navMenu');
  hamburger?.addEventListener('click', e => {
    e.stopPropagation();
    navMenu?.classList.toggle('active');
  });
  document.addEventListener('click', e => {
    if (navMenu && !navMenu.contains(e.target) && !hamburger?.contains(e.target)) {
      navMenu.classList.remove('active');
    }
  });
  document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
    toggle.addEventListener('click', e => {
      e.preventDefault();
      const parent = toggle.closest('.dropdown');
      if (!parent) return;
      document.querySelectorAll('.dropdown').forEach(d => {
        if (d !== parent) d.classList.remove('open');
      });
      parent.classList.toggle('open');
    });
  });
  document.addEventListener('click', e => {
    document.querySelectorAll('.dropdown').forEach(d => {
      if (!d.contains(e.target)) d.classList.remove('open');
    });
  });
  document.querySelectorAll('.mobile-dropdown-toggle').forEach(toggle => {
    toggle.addEventListener('click', e => {
      e.preventDefault();
      toggle.parentElement.classList.toggle('open');
    });
  });
  navMenu?.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => navMenu.classList.remove('active'));
  });
  window.addEventListener('hashchange', () => {
    const routeInfo = getRoute();
    navigate(routeInfo);
  });
  document.addEventListener('click', e => {
    const a = e.target.closest('a[href^="#/"]');
    if (a) {
      e.preventDefault();
      const href = a.getAttribute('href');
      window.location.hash = href;
    }
  });
  initDropdownHover();
  navigate(getRoute());
}

document.addEventListener('DOMContentLoaded', init);