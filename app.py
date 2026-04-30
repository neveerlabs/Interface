#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import socket
import struct
import platform
from threading import Thread
from queue import Queue
import time
import signal
import shlex
import ipaddress
import shutil

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
            ' *  *  *  /*\\  *  *  *',
            '  *  *   /***\\   *  *',
            '   *    /*****\\    *',
            '       /*******\\'
        ]
        text_lines = [
            'Name: Interface',
            'Repos: https:github.com/neveerlabs/Interface.git',
            'Version: v2.7.5',
            'Lost update: 30 April 2026'
        ]
        for i in range(7):
            icon = icon_lines[i]
            text = text_lines[i] if i < len(text_lines) else ''
            print(f"{icon:<28}{text}")
    except Exception:
        print("Name: Interface")
        print("Repos: https:github.com/neveerlabs/Interface.git")
        print("Version: v2.7.5")
        print("Lost update: 30 April 2026")

def main():
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
