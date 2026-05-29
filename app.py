#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import socket
import struct
import platform
from threading import Thread, Lock
from queue import Queue
import time
import signal
import shlex
import ipaddress
import shutil
import json
import atexit
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

try:
    import questionary
except ImportError:
    print("ERROR: Library 'questionary' Not found. Run: pip install questionary")
    sys.exit(1)

IS_WINDOWS = os.name == 'nt'
IS_WSL = False
IS_TERMUX = False
IS_IOS = False
IS_LINUX = False
IS_UNIX = False

if hasattr(sys, 'getandroidapilevel'):
    IS_TERMUX = True
elif 'TERMUX_VERSION' in os.environ:
    IS_TERMUX = True

if not IS_WINDOWS:
    IS_UNIX = True
    try:
        with open('/proc/version', 'r') as f:
            content = f.read()
            if 'Microsoft' in content or 'WSL' in content:
                IS_WSL = True
    except:
        pass
    IS_LINUX = 'linux' in sys.platform
    IS_IOS = 'ios' in sys.platform

if IS_IOS:
    print("IOS is not supported for this script.")
    sys.exit(1)

HOTSPOT_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotspot_configs.json")
HOTSPOT_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotspot_state.json")
VERSION_FILE = "version.txt"
CHANGELOG_FILE = "changelog.txt"
REPO_RAW_BASE = "https://raw.githubusercontent.com/neveerlabs/Interface/main"

log_buffer = []
log_lock = Lock()
dnsmasq_monitor_thread = None
monitor_stop_flag = False

COLORS = {
    'INFO': '\033[32m',
    'WARNING': '\033[33m',
    'ERROR': '\033[31m',
    'RESET': '\033[0m'
}

def run_command(command, timeout=5):
    try:
        if IS_WINDOWS:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(command, shell=True, capture_output=True,
                                    text=True, timeout=timeout, startupinfo=startupinfo)
        else:
            result = subprocess.run(command, shell=True, capture_output=True,
                                    text=True, timeout=timeout)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", -1
    except Exception as e:
        return "", str(e), -1

def run_command_stream(command, timeout=10):
    preexec_func = None
    if IS_UNIX:
        preexec_func = os.setsid
    try:
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1,
                                preexec_fn=preexec_func)
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            print(line, end='')
        proc.wait(timeout=timeout)
        return proc.returncode
    except subprocess.TimeoutExpired:
        if IS_UNIX and preexec_func:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except:
                proc.kill()
        else:
            proc.kill()
        proc.wait()
        return -1
    except Exception:
        return -1

def get_default_interface():
    if IS_WINDOWS:
        out, _, _ = run_command("ipconfig | findstr /i \"Default Gateway\"")
        if out:
            for line in out.splitlines():
                if ':' in line:
                    gw = line.split(':')[-1].strip()
                    if gw:
                        out2, _, _ = run_command("ipconfig")
                        adapter = None
                        for l in out2.splitlines():
                            if 'adapter' in l.lower():
                                adapter = l.split('adapter')[1].strip()[:-1]
                            if gw in l and adapter:
                                return adapter.replace(':', '').strip(), gw
        return None, None
    out, _, rc = run_command("ip route show default")
    if rc != 0 or not out:
        return None, None
    parts = out.split()
    if len(parts) < 5:
        return None, None
    return parts[4], parts[2]

def _get_ip_ioctl(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15].encode('utf-8')))[20:24])
        return ip
    except:
        return None
    finally:
        s.close()

def _get_ip_fallback(ifname):
    if IS_WINDOWS:
        out, _, _ = run_command(f"ipconfig | findstr /i \"{ifname}\"")
        if out:
            for line in out.splitlines():
                if 'IPv4 Address' in line:
                    return line.split(':')[-1].strip()
        return None
    out, _, _ = run_command(f"ip -4 addr show dev {ifname} 2>/dev/null | grep inet | awk '{{print $2}}' | cut -d/ -f1")
    if out:
        return out.strip()
    return None

def get_ip_address(ifname):
    if HAS_FCNTL and IS_UNIX:
        res = _get_ip_ioctl(ifname)
        if res:
            return res
    return _get_ip_fallback(ifname)

def _get_netmask_ioctl(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        mask = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x891b, struct.pack('256s', ifname[:15].encode('utf-8')))[20:24])
        return mask
    except:
        return None
    finally:
        s.close()

def _get_netmask_fallback(ifname):
    if IS_WINDOWS:
        out, _, _ = run_command(f"ipconfig | findstr /i \"{ifname}\"")
        if out:
            for line in out.splitlines():
                if 'Subnet Mask' in line:
                    return line.split(':')[-1].strip()
        return None
    out, _, _ = run_command(f"ip -4 addr show dev {ifname} 2>/dev/null | grep inet | awk '{{print $2}}' | cut -d/ -f2")
    if out:
        cidr = out.strip()
        return cidr_to_netmask(int(cidr))
    return None

def cidr_to_netmask(cidr):
    try:
        cidr = int(cidr)
        mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
        return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"
    except:
        return None

def get_netmask(ifname):
    if HAS_FCNTL and IS_UNIX:
        res = _get_netmask_ioctl(ifname)
        if res:
            return res
    return _get_netmask_fallback(ifname)

def get_mac_address(ifname):
    try:
        if IS_WINDOWS:
            out, _, _ = run_command(f"getmac /v | findstr /i \"{ifname}\"")
            if out:
                parts = out.split()
                for p in parts:
                    if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$', p):
                        return p.replace('-', ':').lower()
                return "N/A"
        else:
            with open(f"/sys/class/net/{ifname}/address", "r") as f:
                return f.read().strip().lower()
    except:
        if IS_UNIX:
            out, _, _ = run_command(f"ip link show {ifname} | grep link/ether | awk '{{print $2}}'")
            if out:
                return out.strip().lower()
        return "N/A"

def netmask_to_cidr(netmask):
    try:
        parts = netmask.split('.')
        binary_str = ''.join([bin(int(x)+256)[3:] for x in parts])
        return str(binary_str.count('1'))
    except:
        return None

def check_internet():
    if IS_WINDOWS:
        _, _, rc = run_command("ping -n 1 -w 2000 8.8.8.8")
    else:
        _, _, rc = run_command("ping -c 1 -W 2 8.8.8.8")
    return rc == 0

def get_public_ip():
    if IS_WINDOWS:
        out, _, rc = run_command("powershell -Command \"(Invoke-WebRequest -Uri 'http://ifconfig.me' -TimeoutSec 3).Content\"", timeout=5)
        if rc == 0 and out and re.match(r'^\d+\.\d+\.\d+\.\d+$', out):
            return out.strip()
        out, _, rc = run_command("powershell -Command \"(Invoke-WebRequest -Uri 'http://api.ipify.org' -TimeoutSec 3).Content\"", timeout=5)
        if rc == 0 and out and re.match(r'^\d+\.\d+\.\d+\.\d+$', out):
            return out.strip()
    else:
        out, _, rc = run_command("curl -s --max-time 3 ifconfig.me", timeout=3)
        if rc == 0 and out and re.match(r'^\d+\.\d+\.\d+\.\d+$', out):
            return out
        out, _, rc = run_command("curl -s --max-time 3 api.ipify.org", timeout=3)
        if rc == 0 and out and re.match(r'^\d+\.\d+\.\d+\.\d+$', out):
            return out
    return "Unknown"

def get_connection_method(iface):
    if IS_WINDOWS:
        return "Unknown"
    con_name = get_active_connection_name()
    if con_name:
        out, _, rc = run_command(f"nmcli -t -f IP4.METHOD connection show '{con_name}'")
        if rc == 0 and out:
            if 'auto' in out:
                return "Dynamic (DHCP)"
            elif 'manual' in out:
                return "Static"
    out, _, _ = run_command(f"ip -4 -o addr show {iface} 2>/dev/null | grep -v secondary | head -1")
    if out and "dynamic" in out:
        return "Dynamic (DHCP)"
    elif out:
        return "Static"
    return "Unknown"

def get_network_info():
    info = {}
    iface, gateway = get_default_interface()
    info['interface'] = iface if iface else "Unknown"
    info['gateway'] = gateway if gateway else "Unknown"
    if iface:
        if IS_WINDOWS:
            info['connection_type'] = "Ethernet or WiFi"
        else:
            if iface.startswith("wl"):
                info['connection_type'] = "Wireless"
            elif iface.startswith(("eth", "en")):
                info['connection_type'] = "Ethernet"
            else:
                info['connection_type'] = "Other"
        info['ip_client'] = get_ip_address(iface)
        info['netmask'] = get_netmask(iface)
        info['mac_address'] = get_mac_address(iface)
        info['connection_status'] = "Connected" if info.get('ip_client') else "Not connected"
        info['method'] = get_connection_method(iface)
        if IS_WINDOWS:
            info['ipv6_address'] = "Unknown"
        else:
            v6_out, _, _ = run_command(f"ip -6 -o addr show dev {iface} scope global 2>/dev/null | awk '{{print $4}}'")
            info['ipv6_address'] = ', '.join(v6_out.splitlines()) if v6_out else "Unknown"
    else:
        info['connection_type'] = "Unknown"
        info['ip_client'] = None
        info['netmask'] = None
        info['mac_address'] = "N/A"
        info['connection_status'] = "Not connected"
        info['method'] = "Unknown"
        info['ipv6_address'] = "Unknown"
    info['ssid'] = "Unknown"
    if iface and not IS_WINDOWS and iface.startswith("wl"):
        out, _, _ = run_command("iwgetid -r")
        if out:
            info['ssid'] = out
    info['internet_status'] = "Access internet" if check_internet() else "Not internet"
    info['public_ip'] = get_public_ip() if check_internet() else "Unknown"
    return info

def display_network_info(info):
    print("\n==========> NETWORK SPECIFICATIONS <==========")
    print(f"  SSID                : {info.get('ssid','?')}")
    print(f"  Interface           : {info.get('interface','?')}")
    print(f"  Connection Type     : {info.get('connection_type','?')}")
    print(f"  Method              : {info.get('method','?')}")
    print(f"  IP Client           : {info.get('ip_client','?')}")
    print(f"  IPv6                : {info.get('ipv6_address','?')}")
    print(f"  Mac Address         : {info.get('mac_address','?')}")
    print(f"  Subnet Mask         : {info.get('netmask','?')}")
    print(f"  Gateway / IP Router : {info.get('gateway','?')}")
    print(f"  IP Public           : {info.get('public_ip','?')}")
    print(f"  Connection status   : {info.get('connection_status','?')}")
    print(f"  Internet state      : {info.get('internet_status','?')}")

def get_nic_hardware_info(iface):
    if IS_WINDOWS:
        return {'driver': 'N/A', 'bus': 'N/A', 'vendor': 'N/A', 'device': 'N/A'}
    info = {'driver': 'N/A', 'bus': 'N/A', 'vendor': 'N/A', 'device': 'N/A', 'vendor_device': 'N/A'}
    ethtool_out, _, _ = run_command(f"ethtool -i {iface} 2>/dev/null")
    if ethtool_out:
        for line in ethtool_out.splitlines():
            if line.startswith("driver:"):
                info['driver'] = line.split(':')[1].strip()
            elif line.startswith("bus-info:"):
                info['bus'] = line.split(':')[1].strip()
    bus = info['bus']
    if bus and bus != 'N/A':
        lspci_out, _, _ = run_command(f"lspci -v -s {bus} 2>/dev/null")
        if lspci_out:
            first_line = lspci_out.splitlines()[0]
            vendor_device = ' '.join(first_line.split()[1:])
            info['vendor_device'] = vendor_device
    return info

def get_device_info():
    info = {}
    if IS_WINDOWS:
        info['hostname'] = platform.node()
        info['brand'] = "Unknown"
        info['model'] = "Unknown"
        info['serial'] = "Unknown"
        info['screen_size'] = "Unknown"
        info['ram'] = "Unknown"
        info['processor'] = "Unknown"
        info['cpu_cores'] = "Unknown"
        info['gpu'] = "Unknown"
        info['disks'] = []
        info['partitions'] = []
        info['nics'] = []
        info['usb_devices'] = []
        info['os_distro'] = "Windows"
        info['os_version'] = platform.version()
        info['kernel_version'] = "Unknown"
        info['architecture'] = platform.machine()
        info['desktop_environment'] = "Windows UI"
        info['init_system'] = "N/A"
        info['bios_vendor'] = "Unknown"
        info['bios_version'] = "Unknown"
        info['bios_date'] = "Unknown"
        info['mb_vendor'] = "Unknown"
        info['mb_model'] = "Unknown"
        return info

    info = {}
    info['hostname'] = platform.node()
    try:
        with open("/sys/class/dmi/id/sys_vendor", "r") as f: info['brand'] = f.read().strip()
    except: info['brand'] = "Unknown"
    try:
        with open("/sys/class/dmi/id/product_name", "r") as f: info['model'] = f.read().strip()
    except: info['model'] = "Unknown"
    try:
        with open("/sys/class/dmi/id/product_serial", "r") as f: info['serial'] = f.read().strip()
    except: info['serial'] = "Unknown"

    scr, _, _ = run_command("xrandr --current 2>/dev/null | grep '*' | awk '{print $1}'")
    info['screen_size'] = scr.splitlines()[0] if scr else "Unknown"

    mem, _, _ = run_command("grep MemTotal /proc/meminfo")
    if mem:
        total_kb = int(re.findall(r'\d+', mem)[0])
        info['ram'] = f"{round(total_kb/1024**2, 1)} GB"
    else:
        info['ram'] = "Unknown"

    cpu, _, _ = run_command("grep 'model name' /proc/cpuinfo | head -1")
    info['processor'] = cpu.split(':')[-1].strip() if cpu else "Unknown"
    info['cpu_cores'] = os.cpu_count() if hasattr(os, 'cpu_count') else "Unknown"

    gpu, _, _ = run_command("lspci | grep -i 'vga\\|3d\\|display'")
    if gpu:
        gpus = [line.split(': ')[-1].strip() for line in gpu.split('\n') if line]
        info['gpu'] = ', '.join(gpus)
    else:
        info['gpu'] = "Unknown"

    disks_out, _, _ = run_command("lsblk -ndo NAME,TYPE,SIZE,TRAN,MODEL,SERIAL 2>/dev/null")
    info['disks'] = []
    if disks_out:
        for line in disks_out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == 'disk':
                name = parts[0]
                size = parts[2] if len(parts) > 2 else ''
                tran = parts[3] if len(parts) > 3 else ''
                model = ' '.join(parts[4:-1]) if len(parts) > 4 else ''
                serial = parts[-1] if len(parts) > 4 else ''
                info['disks'].append({'name': name, 'size': size, 'transport': tran, 'model': model, 'serial': serial})

    parts_out, _, _ = run_command("lsblk -no NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT 2>/dev/null | grep -v '^loop'")
    info['partitions'] = []
    if parts_out:
        for line in parts_out.splitlines():
            cols = line.split()
            if len(cols) >= 4:
                label = cols[3] if cols[3] else '-'
                mount = cols[4] if len(cols) > 4 else 'tidak ter-mount'
                info['partitions'].append({'name': cols[0], 'size': cols[1], 'fstype': cols[2], 'label': label, 'mount': mount})

    ifaces, _, _ = run_command("ip -o link show | awk -F': ' '{print $2}'")
    info['nics'] = []
    if ifaces:
        for iface in ifaces.splitlines():
            iface = iface.strip()
            mac = get_mac_address(iface)
            speed, _, _ = run_command(f"cat /sys/class/net/{iface}/speed 2>/dev/null")
            hw = get_nic_hardware_info(iface)
            mac = mac if mac else "N/A"
            speed = f"{speed} Mbps" if speed and speed.strip() != '-1' else "N/A"
            driver = hw['driver']
            bus = hw['bus']
            vendor_device = hw.get('vendor_device', 'N/A')
            info['nics'].append({'name': iface, 'mac': mac, 'speed': speed, 'driver': driver, 'bus': bus, 'vendor_device': vendor_device})

    usb_out, _, _ = run_command("lsusb")
    if usb_out:
        info['usb_devices'] = [line.strip() for line in usb_out.splitlines()]
    else:
        info['usb_devices'] = []

    os_release, _, _ = run_command("cat /etc/os-release 2>/dev/null")
    info['os_distro'] = "Unknown"
    if os_release:
        for line in os_release.splitlines():
            if line.startswith("PRETTY_NAME="):
                info['os_distro'] = line.split('=')[1].strip('"')
                break
    kernel, _, _ = run_command("uname -r")
    info['kernel_version'] = kernel if kernel else "Unknown"
    arch, _, _ = run_command("uname -m")
    info['architecture'] = arch if arch else "Unknown"
    de, _, _ = run_command("echo $XDG_CURRENT_DESKTOP")
    info['desktop_environment'] = de if de else "Unknown"
    init_system, _, _ = run_command("ps --no-headers -o comm 1")
    info['init_system'] = init_system if init_system else "Unknown"

    try:
        with open("/sys/class/dmi/id/bios_vendor", "r") as f: info['bios_vendor'] = f.read().strip()
    except: info['bios_vendor'] = "Unknown"
    try:
        with open("/sys/class/dmi/id/bios_version", "r") as f: info['bios_version'] = f.read().strip()
    except: info['bios_version'] = "Unknown"
    try:
        with open("/sys/class/dmi/id/bios_date", "r") as f: info['bios_date'] = f.read().strip()
    except: info['bios_date'] = "Unknown"
    try:
        with open("/sys/class/dmi/id/board_vendor", "r") as f: info['mb_vendor'] = f.read().strip()
    except: info['mb_vendor'] = "Unknown"
    try:
        with open("/sys/class/dmi/id/board_name", "r") as f: info['mb_model'] = f.read().strip()
    except: info['mb_model'] = "Unknown"

    return info

def display_device_info(info):
    print("\n==========> DEVICE SPECIFICATIONS <==========")
    print(f"  Hostname            : {info.get('hostname','?')}")
    print(f"  Merek               : {info.get('brand','?')}")
    print(f"  Model               : {info.get('model','?')}")
    print(f"  Serial number       : {info.get('serial','?')}")
    print(f"  screen resolution   : {info.get('screen_size','?')}")
    print(f"  RAM                 : {info.get('ram','?')}")
    print(f"  Processor           : {info.get('processor','?')} ({info.get('cpu_cores','?')} core)")
    print(f"  GPU                 : {info.get('gpu','?')}")
    disks = info.get('disks', [])
    if disks:
        print(f"  Disk                :")
        for d in disks:
            print(f"                        /dev/{d['name']} {d['size']} {d['model']} ({d['transport']}) S/N:{d['serial']}")
    else:
        print(f"  Disk                : -")
    parts = info.get('partitions', [])
    if parts:
        print(f"  Partisi             :")
        for p in parts:
            print(f"                        {p['name']} {p['size']} {p['fstype']} label:{p['label']} mounted on {p['mount']}")
    else:
        print(f"  Partisi             : -")
    nics = info.get('nics', [])
    if nics:
        print(f"  NIC                 :")
        for n in nics:
            print(f"                        {n['name']}  MAC:{n['mac']}  Speed:{n['speed']}")
            print(f"                        Driver: {n['driver']}  Bus: {n['bus']}")
            print(f"                        Vendor/Device: {n['vendor_device']}")
    else:
        print(f"  NIC                 : -")
    usbs = info.get('usb_devices', [])
    if usbs:
        print(f"  Perangkat USB       :")
        for u in usbs:
            print(f"                        {u}")
    else:
        print(f"  Perangkat USB       : -")
    print(f"  System Information  :")
    print(f"  OS                  : {info.get('os_distro','?')}")
    print(f"  Kernel              : {info.get('kernel_version','?')}")
    print(f"  Architecture        : {info.get('architecture','?')}")
    print(f"  Desktop Environment : {info.get('desktop_environment','?')}")
    print(f"  Init System         : {info.get('init_system','?')}")
    print(f"  BIOS                : {info.get('bios_vendor','?')} {info.get('bios_version','?')} ({info.get('bios_date','?')})")
    print(f"  Motherboard         : {info.get('mb_vendor','?')} {info.get('mb_model','?')}")

def ping_target(target, count=4):
    sanitized = shlex.quote(target)
    if IS_WINDOWS:
        rc = run_command_stream(f"ping -n {count} -w 2000 {sanitized}")
    else:
        rc = run_command_stream(f"ping -c {count} -W 2 {sanitized}")
    if rc != 0:
        print(f"Failed: no response or error")
    print()

def get_active_connection_name():
    if IS_WINDOWS:
        return None
    out, _, rc = run_command("nmcli -t -f NAME,DEVICE connection show --active")
    if rc != 0 or not out:
        return None
    for line in out.splitlines():
        if ':' in line:
            name, dev = line.split(':', 1)
            def_iface = get_default_interface()[0]
            if def_iface and dev == def_iface:
                return name
    return None

def is_valid_ipv4(addr):
    try:
        ipaddress.IPv4Address(addr)
        return True
    except:
        return False

def ubah_ip_menu():
    if IS_WINDOWS:
        print("This feature is only supported on Linux.")
        return
    iface, gateway = get_default_interface()
    if not iface:
        print("Built-in interface not found")
        return

    con_name = get_active_connection_name()
    use_nmcli = con_name is not None

    pilihan = questionary.select(
        "select mode IP:",
        choices=["Dynamic (DHCP)", "Static (Manual)"]
    ).ask()
    if not pilihan:
        return

    if pilihan.startswith("Dynamic"):
        print(f"Setup {iface} to DHCP...")
        if use_nmcli:
            cmd = (f"sudo nmcli connection modify {shlex.quote(con_name)} "
                   f"ipv4.method auto ipv4.addresses \"\" ipv4.gateway \"\" ipv4.dns \"\" && "
                   f"sudo ip addr flush dev {shlex.quote(iface)} && "
                   f"sudo nmcli connection down {shlex.quote(con_name)} && "
                   f"sudo nmcli connection up {shlex.quote(con_name)}")
        else:
            cmd = f"sudo dhclient -r {shlex.quote(iface)} ; sudo dhclient {shlex.quote(iface)}"
        out, err, rc = run_command(cmd, timeout=15)
        if rc == 0:
            print("Success! IP address obtained via DHCP.")
        else:
            print(f"Failed: {err}")
        return

    ip = questionary.text("Enter IP address:").ask()
    if not ip or not is_valid_ipv4(ip):
        print("Invalid IP address.")
        return

    default_netmask = get_netmask(iface)
    prompt_netmask = f"Enter subnet mask (leave blank for {default_netmask}):" if default_netmask else "Enter subnet mask:"
    netmask = questionary.text(prompt_netmask).ask()
    if not netmask:
        netmask = default_netmask
    if not netmask or not is_valid_ipv4(netmask):
        print("Invalid subnet mask.")
        return

    gw = questionary.text(f"Enter gateway (leave blank for {gateway}):").ask()
    if not gw:
        gw = gateway
    if not gw or not is_valid_ipv4(gw):
        print("Invalid gateway address.")
        return

    dns = questionary.text("Enter DNS:").ask()
    if not dns or not is_valid_ipv4(dns):
        print("Invalid DNS address.")
        return

    cidr = netmask_to_cidr(netmask)
    if not cidr:
        print("Invalid subnet mask.")
        return

    addr_cidr = f"{ip}/{cidr}"
    if use_nmcli:
        cmd = (f"sudo nmcli connection modify {shlex.quote(con_name)} "
               f"ipv4.method manual "
               f"ipv4.addresses {shlex.quote(addr_cidr)} "
               f"ipv4.gateway {shlex.quote(gw)} "
               f"ipv4.dns {shlex.quote(dns)} && "
               f"sudo nmcli connection up {shlex.quote(con_name)}")
    else:
        cmd = (f"sudo ip addr flush dev {shlex.quote(iface)} && "
               f"sudo ip addr add {shlex.quote(addr_cidr)} dev {shlex.quote(iface)} && "
               f"sudo ip route add default via {shlex.quote(gw)} && "
               f"echo 'nameserver {shlex.quote(dns)}' | sudo tee /etc/resolv.conf > /dev/null")

    print("Applying static configuration...")
    out, err, rc = run_command(cmd, timeout=15)
    if rc == 0:
        print("Static configuration successfully applied.")
    else:
        print(f"Failed: {err}")

def scan_network():
    iface, _ = get_default_interface()
    if not iface:
        print("Unable to determine network interface.")
        return
    ip_client = get_ip_address(iface)
    netmask = get_netmask(iface)
    if not ip_client or not netmask:
        print("Incomplete IP/netmask data.")
        return

    cidr = netmask_to_cidr(netmask)
    if not cidr:
        print("Invalid subnet mask.")
        return

    try:
        network = ipaddress.IPv4Network(f"{ip_client}/{cidr}", strict=False)
        subnet = f"{network.network_address}/{cidr}"
    except Exception as e:
        print(f"Failed to calculate subnet: {e}")
        return

    print(f"[*] Scanning subnet {subnet}...")
    nmap_out, _, nmap_rc = run_command(f"nmap -sn {shlex.quote(subnet)}", timeout=20)
    if nmap_rc == 0:
        print("[*] Scan results (nmap):")
        print(nmap_out)
        return

    print("nmap is not available, trying arp-scan...")
    arp_out, _, arp_rc = run_command("arp-scan --localnet", timeout=15)
    if arp_rc == 0:
        print("[*] Scan results (arp-scan):")
        print(arp_out)
        return

    print("arp-scan failed, falling back to ping sweep...")
    try:
        hosts = list(network.hosts())
        if not hosts:
            print("No valid hosts found in the subnet.")
            return
        threads = []
        q = Queue()
        def ping_one(addr):
            target = shlex.quote(str(addr))
            if IS_WINDOWS:
                _, _, r = run_command(f"ping -n 1 -w 1000 {target}")
            else:
                _, _, r = run_command(f"ping -c 1 -W 1 {target}")
            if r == 0:
                q.put(str(addr))
        for addr in hosts:
            t = Thread(target=ping_one, args=(addr,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        active = []
        while not q.empty():
            active.append(q.get())
        if active:
            print("[*] Active client IPs (ping sweep):")
            for a in sorted(active, key=lambda x: tuple(map(int, x.split('.')))):
                print(a)
        else:
            print("No other clients detected.")
    except Exception as e:
        print(f"Error ping sweep: {e}")

def run_wireshark():
    if IS_TERMUX:
        print("Wireshark is not supported on Termux.")
        print("Consider using tcpdump or a PCAP analyzer instead.")
        return
    if IS_IOS:
        print("Wireshark cannot run on IOS.")
        return

    wireshark_cmd = None
    if IS_WINDOWS:
        possible_paths = [
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Wireshark', 'wireshark.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Wireshark', 'wireshark.exe')
        ]
        for p in possible_paths:
            if os.path.isfile(p):
                wireshark_cmd = p
                break
        if not wireshark_cmd and shutil.which('wireshark'):
            wireshark_cmd = 'wireshark'
    else:
        wireshark_cmd = 'wireshark'

    if not wireshark_cmd or (isinstance(wireshark_cmd, str) and not shutil.which(wireshark_cmd)):
        print("Wireshark is not installed or not found in PATH.")
        if IS_WINDOWS:
            print("Download it from https://www.wireshark.org/download.html")
        else:
            print("Install it using your package manager, e.g.:")
            print("  sudo apt install wireshark   (Debian/Ubuntu)")
            print("  sudo pacman -S wireshark     (Arch)")
            print("  sudo dnf install wireshark   (Fedora)")
        return

    print("Launching Wireshark...")
    print("Press Ctrl+C to stop Wireshark and return to the menu.")
    try:
        if IS_WINDOWS:
            proc = subprocess.Popen([wireshark_cmd], shell=False)
        else:
            proc = subprocess.Popen([wireshark_cmd], shell=False, preexec_fn=os.setsid)
        proc.wait()
    except KeyboardInterrupt:
        print("\nStopping Wireshark...")
        try:
            if IS_WINDOWS:
                proc.terminate()
                proc.wait(timeout=5)
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=5)
        except:
            try:
                proc.kill()
                proc.wait()
            except:
                pass
        print("Wireshark has been closed.")
    except FileNotFoundError:
        print("Unexpected error: Wireshark executable not found.")
    except Exception as e:
        print(f"Failed to run Wireshark: {e}")

def print_header():
    try:
        icon_lines = [
            '   *               *',
            '  *  *           *  *',
            ' *  *  *  (*)  *  *  *',
            ' *  *  *  /**  *  *  *',
            '  *  *   /***\\   *  *',
            '   *    /*****\\    *',
            '       /*******\\'
        ]
        text_lines = [
            'Name: Interface',
            'Repos: https:github.com/neveerlabs/Interface',
            'Version: v3.1.9',
            'Lost update: 29 Mei 2026'
        ]
        for i in range(7):
            icon = icon_lines[i]
            text = text_lines[i] if i < len(text_lines) else ''
            print(f"{icon:<28}{text}")
    except Exception:
        print("Name: Interface")
        print("Repos: https:github.com/neveerlabs/Interface")
        print("Version: v3.1.9")
        print("Lost update: 29 Mei 2026")

def load_configs():
    if not os.path.exists(HOTSPOT_CONFIG_FILE):
        return []
    try:
        with open(HOTSPOT_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_configs(configs):
    with open(HOTSPOT_CONFIG_FILE, 'w') as f:
        json.dump(configs, f, indent=2)

def load_state():
    if not os.path.exists(HOTSPOT_STATE_FILE):
        return None
    try:
        with open(HOTSPOT_STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def save_state(state):
    if state is None:
        if os.path.exists(HOTSPOT_STATE_FILE):
            os.remove(HOTSPOT_STATE_FILE)
    else:
        with open(HOTSPOT_STATE_FILE, 'w') as f:
            json.dump(state, f)

def is_hotspot_running():
    state = load_state()
    if not state:
        return False
    hostapd_pid = state.get('hostapd_pid')
    dnsmasq_pid = state.get('dnsmasq_pid')
    if hostapd_pid:
        try:
            os.kill(hostapd_pid, 0)
        except OSError:
            return False
    if dnsmasq_pid:
        try:
            os.kill(dnsmasq_pid, 0)
        except OSError:
            return False
    return True

def log_hotspot(status, message):
    global log_buffer
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {'time': timestamp, 'status': status, 'message': message}
    with log_lock:
        log_buffer.append(entry)
    if not monitor_stop_flag:
        color = COLORS.get(status, '')
        reset = COLORS['RESET']
        print(f"[{timestamp}] {color}[{status}]{reset} {message}")

def stop_hotspot_server():
    global dnsmasq_monitor_thread, monitor_stop_flag, log_buffer
    state = load_state()
    if state:
        hostapd_pid = state.get('hostapd_pid')
        dnsmasq_pid = state.get('dnsmasq_pid')
        if hostapd_pid:
            try:
                os.kill(hostapd_pid, signal.SIGTERM)
            except:
                pass
        if dnsmasq_pid:
            try:
                os.kill(dnsmasq_pid, signal.SIGTERM)
            except:
                pass
        monitor_stop_flag = True
        time.sleep(0.5)
        ap_iface = state.get('ap_iface')
        wan_iface = state.get('wan_iface')
        run_command("pkill hostapd; pkill dnsmasq", timeout=2)
        if ap_iface:
            run_command(f"ip addr flush dev {ap_iface}")
            run_command(f"nmcli device set {ap_iface} managed yes 2>/dev/null", timeout=2)
            run_command(f"ip link set {ap_iface} up")
        if wan_iface:
            run_command(f"iptables -t nat -D POSTROUTING -o {wan_iface} -j MASQUERADE 2>/dev/null")
            run_command(f"iptables -D FORWARD -i {ap_iface} -o {wan_iface} -j ACCEPT 2>/dev/null")
            run_command(f"iptables -D FORWARD -i {wan_iface} -o {ap_iface} -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null")
        run_command("sysctl -w net.ipv4.ip_forward=0 > /dev/null")
        for f in ["/tmp/hostapd.conf", "/tmp/dnsmasq.conf"]:
            if os.path.exists(f):
                os.remove(f)
        save_state(None)
        with log_lock:
            log_buffer.clear()
        log_hotspot("INFO", "Hotspot server stopped.")
    else:
        print("No hotspot server is currently running.")

def get_all_interfaces():
    out, _, _ = run_command("ip -o link show | awk -F': ' '{print $2}'")
    if not out:
        return []
    return [iface.strip() for iface in out.splitlines() if iface.strip() != "lo"]

def get_wireless_iface():
    for iface in get_all_interfaces():
        if iface.startswith("wl"):
            return iface
    return None

def validate_hotspot_config(config):
    ip_wifi = config.get('ip_wifi', '')
    ip_pool = config.get('ip_pool', '')
    gateway = config.get('gateway', '')

    try:
        iface = ipaddress.IPv4Interface(ip_wifi)
        net = iface.network
        mask = iface.netmask
    except Exception as e:
        return False, f"Invalid IP WiFi configuration: {e}"

    if not gateway:
        return False, "Gateway is not set."
    try:
        gw_ip = ipaddress.IPv4Address(gateway)
    except:
        return False, "Invalid gateway IP address."
    if gw_ip not in net:
        return False, f"Gateway {gateway} is not in the subnet {net}."

    if gw_ip == iface.ip:
        pass
    else:
        pass

    try:
        start_str, end_str = ip_pool.split('-')
        start_ip = ipaddress.IPv4Address(start_str.strip())
        end_ip = ipaddress.IPv4Address(end_str.strip())
    except:
        return False, "IP pool format must be start-end (e.g., 192.168.1.10-192.168.1.50)."

    if start_ip >= end_ip:
        return False, "IP pool start must be less than end."

    if start_ip not in net or end_ip not in net:
        return False, f"IP pool range {start_ip}-{end_ip} is not within subnet {net}."

    if iface.ip in ipaddress.summarize_address_range(start_ip, end_ip):
        return False, f"AP IP address {iface.ip} must not be inside the DHCP pool range."

    if gw_ip in ipaddress.summarize_address_range(start_ip, end_ip):
        return False, f"Gateway IP {gw_ip} must not be inside the DHCP pool range."

    if net.broadcast_address in ipaddress.summarize_address_range(start_ip, end_ip):
        return False, f"Broadcast address {net.broadcast_address} must not be inside the pool."

    return True, ""

def write_hostapd_conf(ssid, password, ap_iface):
    config = f"""interface={ap_iface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
"""
    if password:
        config += f"""wpa=2
wpa_passphrase={password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
    else:
        config += "wpa=0\n"
    with open("/tmp/hostapd.conf", "w") as f:
        f.write(config)

def write_dnsmasq_conf(ap_iface, dhcp_start, dhcp_end, netmask, gateway):
    config = f"""interface={ap_iface}
dhcp-range={dhcp_start},{dhcp_end},{netmask},12h
dhcp-option=3,{gateway}
dhcp-option=6,{gateway}
no-resolv
log-dhcp
"""
    with open("/tmp/dnsmasq.conf", "w") as f:
        f.write(config)

def monitor_dnsmasq_output(proc):
    global log_buffer, monitor_stop_flag
    for line in iter(proc.stdout.readline, ''):
        if monitor_stop_flag:
            break
        stripped = line.rstrip()
        if not stripped:
            continue
        if 'error' in stripped.lower():
            status = 'ERROR'
        elif 'warning' in stripped.lower():
            status = 'WARNING'
        else:
            status = 'INFO'
        log_hotspot(status, stripped)
    proc.stdout.close()

def start_hotspot_process(config):
    global dnsmasq_monitor_thread, monitor_stop_flag, log_buffer
    if IS_WINDOWS or IS_TERMUX:
        log_hotspot("ERROR", "Hotspot server only supported on Linux.")
        return None, None

    if not shutil.which('hostapd') or not shutil.which('dnsmasq'):
        log_hotspot("ERROR", "hostapd or dnsmasq not found. Please install them.")
        return None, None

    valid, err_msg = validate_hotspot_config(config)
    if not valid:
        log_hotspot("ERROR", f"Configuration error: {err_msg}")
        return None, None

    ap_iface = config['ap_iface']
    wan_iface = config.get('wan_iface')
    ip_wifi = config['ip_wifi']
    ip_pool = config['ip_pool']
    gateway = config['gateway']
    ssid = config['ssid']
    password = config['password']

    stop_hotspot_server()
    monitor_stop_flag = False
    with log_lock:
        log_buffer.clear()

    run_command(f"systemctl stop hostapd dnsmasq 2>/dev/null")
    run_command("pkill hostapd; pkill dnsmasq", timeout=2)
    time.sleep(0.5)

    subprocess.run(f"nmcli device set {ap_iface} managed no 2>/dev/null", shell=True)
    write_hostapd_conf(ssid, password, ap_iface)

    try:
        start_str, end_str = ip_pool.split('-')
        start_ip = ipaddress.IPv4Address(start_str.strip())
        end_ip = ipaddress.IPv4Address(end_str.strip())
        iface = ipaddress.IPv4Interface(ip_wifi)
        netmask = str(iface.netmask)
    except Exception as e:
        log_hotspot("ERROR", f"Failed to process pool configuration: {e}")
        return None, None

    write_dnsmasq_conf(ap_iface, str(start_ip), str(end_ip), netmask, gateway)

    if "/" in ip_wifi:
        ip_net = ip_wifi
    else:
        ip_net = ip_wifi + "/24"
    run_command(f"ip addr flush dev {ap_iface}")
    run_command(f"ip addr add {ip_net} dev {ap_iface}")
    run_command(f"ip link set {ap_iface} up")

    if wan_iface:
        run_command("sysctl -w net.ipv4.ip_forward=1 > /dev/null")
        run_command(f"iptables -t nat -A POSTROUTING -o {wan_iface} -j MASQUERADE")
        run_command(f"iptables -A FORWARD -i {ap_iface} -o {wan_iface} -j ACCEPT")
        run_command(f"iptables -A FORWARD -i {wan_iface} -o {ap_iface} -m state --state RELATED,ESTABLISHED -j ACCEPT")

    hostapd_proc = subprocess.Popen(["hostapd", "/tmp/hostapd.conf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)
    dnsmasq_proc = subprocess.Popen(["dnsmasq", "-d", "-C", "/tmp/dnsmasq.conf"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    state = {
        "hostapd_pid": hostapd_proc.pid,
        "dnsmasq_pid": dnsmasq_proc.pid,
        "ap_iface": ap_iface,
        "wan_iface": wan_iface
    }
    save_state(state)

    dnsmasq_monitor_thread = Thread(target=monitor_dnsmasq_output, args=(dnsmasq_proc,), daemon=True)
    dnsmasq_monitor_thread.start()
    log_hotspot("INFO", f"Hotspot '{ssid}' started successfully.")
    return hostapd_proc, dnsmasq_proc

def cleanup_hotspot_on_exit():
    global monitor_stop_flag
    monitor_stop_flag = True
    state = load_state()
    if state:
        hostapd_pid = state.get('hostapd_pid')
        dnsmasq_pid = state.get('dnsmasq_pid')
        ap_iface = state.get('ap_iface')
        wan_iface = state.get('wan_iface')
        if hostapd_pid:
            try:
                os.kill(hostapd_pid, signal.SIGTERM)
            except:
                pass
        if dnsmasq_pid:
            try:
                os.kill(dnsmasq_pid, signal.SIGTERM)
            except:
                pass
        run_command("pkill hostapd; pkill dnsmasq", timeout=2)
        if ap_iface:
            run_command(f"ip addr flush dev {ap_iface}")
            run_command(f"nmcli device set {ap_iface} managed yes 2>/dev/null")
            run_command(f"ip link set {ap_iface} up")
        if wan_iface:
            run_command(f"iptables -t nat -D POSTROUTING -o {wan_iface} -j MASQUERADE 2>/dev/null")
            run_command(f"iptables -D FORWARD -i {ap_iface} -o {wan_iface} -j ACCEPT 2>/dev/null")
            run_command(f"iptables -D FORWARD -i {wan_iface} -o {ap_iface} -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null")
        run_command("sysctl -w net.ipv4.ip_forward=0 > /dev/null")
        for f in ["/tmp/hostapd.conf", "/tmp/dnsmasq.conf"]:
            if os.path.exists(f):
                os.remove(f)
        save_state(None)

def get_current_version():
    script_dir = Path(__file__).resolve().parent
    version_path = script_dir / VERSION_FILE
    if version_path.exists():
        return version_path.read_text().strip()
    return None

def get_remote_version():
    url = f"{REPO_RAW_BASE}/{VERSION_FILE}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.read().decode('utf-8').strip()
    except:
        return None

def parse_version(ver_str):
    try:
        if ver_str.startswith('v'):
            ver_str = ver_str[1:]
        return tuple(map(int, ver_str.split('.')))
    except:
        return None

def is_newer(remote, local):
    rv = parse_version(remote)
    lv = parse_version(local)
    if rv is None or lv is None:
        return remote != local
    return rv > lv

def check_and_update():
    current = get_current_version()
    if not current:
        return

    remote = get_remote_version()
    if not remote:
        return

    if not is_newer(remote, current):
        return

    print(f"\nNew version available: {remote} (current: {current})")

    changelog_url = f"{REPO_RAW_BASE}/{CHANGELOG_FILE}"
    try:
        with urllib.request.urlopen(changelog_url, timeout=5) as resp:
            changelog = resp.read().decode('utf-8')
            print("\n" + "="*50)
            print("           WHAT'S NEW")
            print("="*50)
            print(changelog)
            print("="*50)
    except:
        pass

    if not questionary.confirm("Update now? (script will exit after update)").ask():
        return

    files_to_update = ["app.py", "requirements.txt", "README.md", VERSION_FILE, CHANGELOG_FILE]
    script_dir = Path(__file__).resolve().parent

    print("\nDownloading latest files...")
    for filename in files_to_update:
        url = f"{REPO_RAW_BASE}/{filename}"
        target_path = script_dir / filename
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                content = resp.read()
            target_path.write_bytes(content)
            print(f"  ✔ {filename} updated.")
        except Exception as e:
            print(f"  ✖ Failed to download {filename}: {e}")
            return

    print("\nUpdate completed. Please restart the script (python3 app.py).")
    sys.exit(0)

def auto_start_hotspot():
    state = load_state()
    if state:
        configs = load_configs()
        idx = state.get('config_index')
        if idx is not None and 0 <= idx < len(configs):
            print("Previously running hotspot detected. Restarting...")
            config = configs[idx]
            start_hotspot_process(config)
            print(f"Hotspot '{config['ssid']}' restarted automatically.")
        else:
            save_state(None)

def show_live_log():
    if not is_hotspot_running():
        print("Hotspot server is not running.")
        return
    print("Displaying live hotspot log (press Ctrl+C to return)...")
    try:
        while True:
            time.sleep(1)
            with log_lock:
                if log_buffer:
                    for entry in log_buffer[-10:]:
                        ts = entry['time']
                        status = entry['status']
                        msg = entry['message']
                        color = COLORS.get(status, '')
                        reset = COLORS['RESET']
                        print(f"[{ts}] {color}[{status}]{reset} {msg}")
    except KeyboardInterrupt:
        pass

def view_connected_devices():
    state = load_state()
    if not state or not is_hotspot_running():
        print("Hotspot server is not running.")
        return
    ap_iface = state.get('ap_iface')
    if not ap_iface:
        print("Interface not found in state.")
        return

    if IS_WINDOWS:
        out, _, rc = run_command("netsh wlan show hostednetwork")
        if rc == 0:
            print(out)
        else:
            print("Could not retrieve connected clients on Windows.")
    else:
        out, _, rc = run_command(f"iw dev {ap_iface} station dump")
        if rc == 0:
            if out:
                print(out)
            else:
                print("No connected devices or unsupported.")
        else:
            out, _, _ = run_command("arp -a")
            if out:
                print("Fallback ARP table:")
                print(out)
            else:
                print("Could not retrieve connected devices.")

def manage_hotspot():
    while True:
        configs = load_configs()
        print("\n" + "="*50)
        print("         HOTSPOT MANAGEMENT")
        print("="*50)
        if configs:
            print("Saved configurations:")
            print("-"*50)
            print(f"{'No.':<4} {'SSID':<20} {'AP Iface':<10} {'IP WiFi':<15} {'Internet':<15}")
            print("-"*50)
            for i, cfg in enumerate(configs):
                ssid = cfg.get('ssid', '?')[:18]
                ap = cfg.get('ap_iface', '?')[:8]
                ip = cfg.get('ip_wifi', '?')[:13]
                wan = cfg.get('wan_iface', 'None') or 'None'
                if len(wan) > 12:
                    wan = wan[:12]
                print(f"{i+1:<4} {ssid:<20} {ap:<10} {ip:<15} {wan:<15}")
            print("-"*50)
        else:
            print("No saved configurations.")

        choices = [
            "Create WiFi Hotspot",
            "Edit Configuration",
            "Delete Configuration",
            "Start Hotspot Server",
            "Restart Hotspot Server",
            "Stop Hotspot Server",
            "Monitor Log",
            "View Connected Devices",
            "Back"
        ]
        action = questionary.select("Select action:", choices=choices, use_arrow_keys=True).ask()
        if action == "Back":
            break

        if action == "Create WiFi Hotspot":
            if IS_WINDOWS or IS_TERMUX:
                print("Hotspot creation is only supported on Linux.")
                continue
            ap_iface = get_wireless_iface()
            if not ap_iface:
                print("No wireless interface found.")
                continue
            print(f"Using interface: {ap_iface}")
            ssid = questionary.text("SSID:", default="MyHotspot").ask()
            password = questionary.text("Password (leave blank for open):", default="").ask()
            ip_wifi = questionary.text("IP WiFi (e.g., 192.168.10.1/24):", default="192.168.10.1/24").ask()
            ip_pool = questionary.text("IP Pool (start-end, e.g., 192.168.10.2-192.168.10.50):", default="192.168.10.2-192.168.10.50").ask()
            gateway = questionary.text("Gateway:", default=ip_wifi.split('/')[0]).ask()

            ifaces = get_all_interfaces()
            wan_choices = [iface for iface in ifaces if iface != ap_iface]
            wan_choices.append("No internet (LAN only)")
            wan_selection = questionary.select("Select internet source interface:", choices=wan_choices).ask()
            if wan_selection == "No internet (LAN only)":
                wan_iface = None
            else:
                wan_iface = wan_selection

            config = {
                "ap_iface": ap_iface,
                "ssid": ssid,
                "password": password,
                "ip_wifi": ip_wifi,
                "ip_pool": ip_pool,
                "gateway": gateway,
                "wan_iface": wan_iface
            }
            valid, err = validate_hotspot_config(config)
            if not valid:
                print(f"Error: {err}")
                continue
            configs.append(config)
            save_configs(configs)
            print("Configuration saved.")

        elif action == "Edit Configuration":
            if not configs:
                print("No configurations to edit.")
                continue
            idx = questionary.select("Select configuration to edit:",
                                     choices=[f"{i+1}. {c['ssid']}" for i, c in enumerate(configs)]).ask()
            idx = int(idx.split('.')[0]) - 1
            cfg = configs[idx]
            print(f"Editing '{cfg['ssid']}' (leave blank to keep current value)")
            new_ssid = questionary.text("SSID:", default=cfg['ssid']).ask()
            new_password = questionary.text("Password:", default=cfg.get('password', '')).ask()
            new_ip_wifi = questionary.text("IP WiFi:", default=cfg.get('ip_wifi', '192.168.10.1/24')).ask()
            new_ip_pool = questionary.text("IP Pool:", default=cfg.get('ip_pool', '192.168.10.2-192.168.10.50')).ask()
            new_gateway = questionary.text("Gateway:", default=cfg.get('gateway', new_ip_wifi.split('/')[0])).ask()
            ifaces = get_all_interfaces()
            wan_choices = [iface for iface in ifaces if iface != cfg['ap_iface']]
            wan_choices.append("No internet (LAN only)")
            current_wan = cfg.get('wan_iface')
            default_wan = current_wan if current_wan else "No internet (LAN only)"
            new_wan = questionary.select("Internet source interface:", choices=wan_choices, default=default_wan).ask()
            new_wan = None if new_wan == "No internet (LAN only)" else new_wan

            updated_config = {
                "ap_iface": cfg['ap_iface'],
                "ssid": new_ssid,
                "password": new_password,
                "ip_wifi": new_ip_wifi,
                "ip_pool": new_ip_pool,
                "gateway": new_gateway,
                "wan_iface": new_wan
            }
            valid, err = validate_hotspot_config(updated_config)
            if not valid:
                print(f"Error: {err}")
                continue
            cfg.update(updated_config)
            save_configs(configs)
            print("Configuration updated.")

        elif action == "Delete Configuration":
            if not configs:
                print("No configurations to delete.")
                continue
            idx = questionary.select("Select configuration to delete:",
                                     choices=[f"{i+1}. {c['ssid']}" for i, c in enumerate(configs)]).ask()
            idx = int(idx.split('.')[0]) - 1
            configs.pop(idx)
            save_configs(configs)
            print("Configuration deleted.")

        elif action == "Start Hotspot Server":
            if IS_WINDOWS or IS_TERMUX:
                print("Hotspot server can only run on Linux.")
                continue
            if is_hotspot_running():
                print("A hotspot server is already running. Stop it first.")
                continue
            if not configs:
                print("No saved configurations. Create one first.")
                continue
            idx = questionary.select("Select configuration to start:",
                                     choices=[f"{i+1}. {c['ssid']}" for i, c in enumerate(configs)]).ask()
            idx = int(idx.split('.')[0]) - 1
            cfg = configs[idx]
            print(f"Starting hotspot '{cfg['ssid']}'...")
            try:
                hostapd, dnsmasq = start_hotspot_process(cfg)
                if hostapd and dnsmasq:
                    state = load_state()
                    state['config_index'] = idx
                    save_state(state)
                    print(f"Hotspot '{cfg['ssid']}' is now running.")
                else:
                    print("Failed to start hotspot. Check logs.")
            except Exception as e:
                print(f"Failed to start hotspot: {e}")

        elif action == "Restart Hotspot Server":
            if IS_WINDOWS or IS_TERMUX:
                print("Hotspot server can only run on Linux.")
                continue
            if not configs:
                print("No saved configurations.")
                continue
            idx = questionary.select("Select configuration to restart:",
                                     choices=[f"{i+1}. {c['ssid']}" for i, c in enumerate(configs)]).ask()
            idx = int(idx.split('.')[0]) - 1
            cfg = configs[idx]
            print(f"Restarting hotspot '{cfg['ssid']}'...")
            try:
                stop_hotspot_server()
                time.sleep(1)
                hostapd, dnsmasq = start_hotspot_process(cfg)
                if hostapd and dnsmasq:
                    state = load_state()
                    state['config_index'] = idx
                    save_state(state)
                    print(f"Hotspot '{cfg['ssid']}' restarted.")
                else:
                    print("Failed to restart hotspot.")
            except Exception as e:
                print(f"Failed to restart hotspot: {e}")

        elif action == "Stop Hotspot Server":
            if IS_WINDOWS or IS_TERMUX:
                print("Hotspot server only runs on Linux.")
                continue
            if is_hotspot_running():
                stop_hotspot_server()
            else:
                print("No hotspot server is running.")

        elif action == "Monitor Log":
            if not is_hotspot_running():
                print("Hotspot server is not running. Start it first.")
                continue
            show_live_log()

        elif action == "View Connected Devices":
            view_connected_devices()

def main():
    atexit.register(cleanup_hotspot_on_exit)
    check_and_update()
    auto_start_hotspot()

    while True:
        print_header()
        print()
        pilihan = questionary.select(
            "Select the action to perform:",
            choices=[
                "Display Network Specifications",
                "Display Device Specifications",
                "Ping DNS (8.8.8.8)",
                "Ping Google (google.com)",
                "Ping Router / Gateway",
                "Ping Between Router",
                "Ping Between Clients",
                "Change IP (Static / Dynamic)",
                "Check IP Addresses of All Clients on the Network",
                "Manage Hotspot",
                "Run Wireshark",
                "Exit"
            ],
            use_arrow_keys=True
        ).ask()
        if not pilihan:
            continue

        if pilihan == "Display Network Specifications":
            net_info = get_network_info()
            display_network_info(net_info)
        elif pilihan == "Display Device Specifications":
            dev_info = get_device_info()
            display_device_info(dev_info)
        elif pilihan == "Ping DNS (8.8.8.8)":
            ping_target("8.8.8.8")
        elif pilihan == "Ping Google (google.com)":
            ping_target("google.com")
        elif pilihan == "Ping Router / Gateway":
            _, gw = get_default_interface()
            if gw:
                ping_target(gw)
            else:
                print("Unknown")
        elif pilihan == "Ping Between Router":
            target = questionary.text("Enter router IP address:").ask()
            if target:
                if not is_valid_ipv4(target):
                    print("Invalid IP address.")
                else:
                    ping_target(target)
            else:
                print("IP address required.")
        elif pilihan == "Ping Between Clients":
            target = questionary.text("Enter target IP address:").ask()
            if target:
                if not is_valid_ipv4(target):
                    print("Invalid IP address.")
                else:
                    ping_target(target)
        elif pilihan == "Change IP (Static / Dynamic)":
            ubah_ip_menu()
        elif pilihan == "Check IP Addresses of All Clients on the Network":
            scan_network()
        elif pilihan == "Manage Hotspot":
            manage_hotspot()
        elif pilihan == "Run Wireshark":
            run_wireshark()
        elif pilihan == "Exit":
            print("Goodbye...")
            break
        input("\nPress Enter go back...\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Cancelled.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
