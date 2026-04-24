#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import socket
import fcntl
import struct
import platform
from threading import Thread
from queue import Queue
import time
import signal

try:
    import questionary
except ImportError:
    print("ERROR: Library 'questionary' Not found. Run: pip install questionary")
    sys.exit(1)

def run_command(command, timeout=5):
    try:
        result = subprocess.run(command, shell=True, capture_output=True,
                                text=True, timeout=timeout)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", -1
    except Exception as e:
        return "", str(e), -1

def run_command_stream(command, timeout=10):
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1,
                            preexec_fn=os.setsid)
    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            print(line, end='')
        proc.wait(timeout=timeout)
        return proc.returncode
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait()
        return -1
    except Exception:
        return -1

def get_default_interface():
    out, _, rc = run_command("ip route show default")
    if rc != 0 or not out:
        return None, None
    parts = out.split()
    if len(parts) < 5:
        return None, None
    return parts[4], parts[2]

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip = socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])
        return ip
    except Exception:
        return None
    finally:
        s.close()

def get_netmask(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        mask = socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x891b,
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])
        return mask
    except Exception:
        return None
    finally:
        s.close()

def get_mac_address(ifname):
    try:
        with open(f"/sys/class/net/{ifname}/address", "r") as f:
            return f.read().strip()
    except Exception:
        return "N/A"

def netmask_to_cidr(netmask):
    try:
        parts = netmask.split('.')
        binary_str = ''.join([bin(int(x)+256)[3:] for x in parts])
        return str(binary_str.count('1'))
    except:
        return None

def check_internet():
    _, _, rc = run_command("ping -c 1 -W 2 8.8.8.8")
    return rc == 0

def get_public_ip():
    out, _, rc = run_command("curl -s --max-time 3 ifconfig.me", timeout=3)
    if rc == 0 and out and re.match(r'^\d+\.\d+\.\d+\.\d+$', out):
        return out
    out, _, rc = run_command("curl -s --max-time 3 api.ipify.org", timeout=3)
    if rc == 0 and out and re.match(r'^\d+\.\d+\.\d+\.\d+$', out):
        return out
    return "Unknown"

def get_connection_method(iface):
    con_name = get_active_connection_name()
    if con_name:
        out, _, rc = run_command(f"nmcli -t -f IP4.METHOD connection show '{con_name}'")
        if rc == 0 and out:
            if 'auto' in out:
                return "Dynamic (DHCP)"
            elif 'manual' in out:
                return "Static"
    out, _, _ = run_command(f"ip -4 -o addr show {iface} 2>/dev/null | grep -v secondary | head -1")
    if "dynamic" in out:
        return "Dynamic (DHCP)"
    elif out:
        return "Static"
    return "Unknown"

def get_network_info():
    info = {}
    iface, gateway = get_default_interface()
    info['interface'] = iface
    info['gateway'] = gateway if gateway else "Unknown"
    if iface:
        info['ip_client'] = get_ip_address(iface)
        info['netmask'] = get_netmask(iface)
        info['mac_address'] = get_mac_address(iface)
        info['connection_status'] = "Connected" if info.get('ip_client') else "Not connected"
        info['method'] = get_connection_method(iface)
        v6_out, _, _ = run_command(f"ip -6 -o addr show dev {iface} scope global 2>/dev/null | awk '{{print $4}}'")
        if v6_out:
            info['ipv6_address'] = ', '.join(v6_out.splitlines())
        else:
            info['ipv6_address'] = "Unknown"
    else:
        info['ip_client'] = None
        info['netmask'] = None
        info['mac_address'] = "N/A"
        info['connection_status'] = "Not connected"
        info['method'] = "Unknown"
        info['ipv6_address'] = "Unknown"
    info['ssid'] = "Unknown"
    if iface and iface.startswith("wl"):
        out, _, _ = run_command("iwgetid -r")
        if out:
            info['ssid'] = out
        else:
            info['ssid'] = "Unknown"
    info['internet_status'] = "Access internet" if check_internet() else "Not internet"
    info['public_ip'] = get_public_ip() if check_internet() else "Unknown"
    return info

def display_network_info(info):
    print("\n==========> NETWORK SPECIFICATIONS <==========")
    print(f"  SSID                : {info.get('ssid','?')}")
    print(f"  Interface           : {info.get('interface','?')}")
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
    info = {'driver': 'N/A', 'bus': 'N/A', 'vendor': 'N/A', 'device': 'N/A'}
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
        else:
            info['vendor_device'] = 'N/A'
    else:
        info['vendor_device'] = 'N/A'
    return info

def get_device_info():
    info = {}
    info['hostname'] = platform.node()
    out, _, _ = run_command("cat /sys/class/dmi/id/sys_vendor 2>/dev/null")
    info['brand'] = out if out else "Unknown"
    out, _, _ = run_command("cat /sys/class/dmi/id/product_name 2>/dev/null")
    info['model'] = out if out else "Unknown"
    out, _, _ = run_command("cat /sys/class/dmi/id/product_serial 2>/dev/null")
    info['serial'] = out if out else "Unknown"

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
    info['cpu_cores'] = os.cpu_count()

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
            mac, _, _ = run_command(f"cat /sys/class/net/{iface}/address 2>/dev/null")
            speed, _, _ = run_command(f"cat /sys/class/net/{iface}/speed 2>/dev/null")
            hw = get_nic_hardware_info(iface)
            mac = mac if mac else "N/A"
            speed = f"{speed} Mbps" if speed and speed.strip() != '-1' else "N/A"
            driver = hw['driver']
            bus = hw['bus']
            vendor_device = hw['vendor_device']
            info['nics'].append({'name': iface, 'mac': mac, 'speed': speed, 'driver': driver, 'bus': bus, 'vendor_device': vendor_device})

    usb_out, _, _ = run_command("lsusb")
    if usb_out:
        info['usb_devices'] = []
        for line in usb_out.splitlines():
            info['usb_devices'].append(line.strip())
    else:
        info['usb_devices'] = []

    os_release, _, _ = run_command("cat /etc/os-release 2>/dev/null")
    info['os_distro'] = "Unknown"
    info['os_version'] = "Unknown"
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

    bios_vendor, _, _ = run_command("cat /sys/class/dmi/id/bios_vendor 2>/dev/null")
    info['bios_vendor'] = bios_vendor if bios_vendor else "Unknown"
    bios_version, _, _ = run_command("cat /sys/class/dmi/id/bios_version 2>/dev/null")
    info['bios_version'] = bios_version if bios_version else "Unknown"
    bios_date, _, _ = run_command("cat /sys/class/dmi/id/bios_date 2>/dev/null")
    info['bios_date'] = bios_date if bios_date else "Unknown"
    mb_vendor, _, _ = run_command("cat /sys/class/dmi/id/board_vendor 2>/dev/null")
    info['mb_vendor'] = mb_vendor if mb_vendor else "Unknown"
    mb_model, _, _ = run_command("cat /sys/class/dmi/id/board_name 2>/dev/null")
    info['mb_model'] = mb_model if mb_model else "Unknown"

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
    rc = run_command_stream(f"ping -c {count} -W 2 {target}")
    if rc == 0:
        pass
    else:
        print(f"Failed: no response or error")
    print()

def get_active_connection_name():
    out, _, rc = run_command("nmcli -t -f NAME,DEVICE connection show --active")
    if rc != 0 or not out:
        return None
    for line in out.splitlines():
        if ':' in line:
            name, dev = line.split(':', 1)
            if dev == get_default_interface()[0]:
                return name
    return None

def ubah_ip_menu():
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
            cmd = (f"sudo nmcli connection modify '{con_name}' "
                   f"ipv4.method auto ipv4.addresses \"\" ipv4.gateway \"\" ipv4.dns \"\" && "
                   f"sudo ip addr flush dev {iface} && "
                   f"sudo nmcli connection down '{con_name}' && "
                   f"sudo nmcli connection up '{con_name}'")
        else:
            cmd = f"sudo dhclient -r {iface} ; sudo dhclient {iface}"
        out, err, rc = run_command(cmd, timeout=15)
        if rc == 0:
            print("Success! IP address obtained via DHCP.")
        else:
            print(f"Failed: {err}")
        return

    ip = questionary.text("Enter IP address:").ask()
    if not ip:
        print("IP address cannot be empty.")
        return

    default_netmask = get_netmask(iface)
    prompt_netmask = f"Enter subnet mask (leave blank for {default_netmask}):" if default_netmask else "Enter subnet mask:"
    netmask = questionary.text(prompt_netmask).ask()
    if not netmask:
        netmask = default_netmask
    if not netmask:
        print("Subnet mask cannot be determined.")
        return

    gw = questionary.text(f"Enter gateway (leave blank for {gateway}):").ask()
    if not gw:
        gw = gateway
    dns = questionary.text("Enter DNS:").ask()
    if not dns:
        print("DNS cannot be empty.")
        return

    cidr = netmask_to_cidr(netmask)
    if not cidr:
        print("Invalid subnet mask.")
        return

    if use_nmcli:
        confirm = questionary.confirm(
            f"Are you sure you want to apply this configuration to the router?"
        ).ask()
        if not confirm:
            print("Cancelled.")
            return
        cmd = (f"sudo nmcli connection modify '{con_name}' "
               f"ipv4.method manual "
               f"ipv4.addresses {ip}/{cidr} "
               f"ipv4.gateway {gw} "
               f"ipv4.dns {dns} && "
               f"sudo nmcli connection up '{con_name}'")
    else:
        confirm = questionary.confirm(
            f"Are you sure you want to apply this configuration to the router?"
        ).ask()
        if not confirm:
            print("Cancelled.")
            return
        cmd = (f"sudo ip addr flush dev {iface} && "
               f"sudo ip addr add {ip}/{cidr} dev {iface} && "
               f"sudo ip route add default via {gw} && "
               f"echo 'nameserver {dns}' | sudo tee /etc/resolv.conf > /dev/null")

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

    import ipaddress
    try:
        network = ipaddress.IPv4Network(f"{ip_client}/{cidr}", strict=False)
        subnet = f"{network.network_address}/{cidr}"
    except Exception as e:
        print(f"Failed to calculate subnet: {e}")
        return

    print(f"[*] Scanning subnet... {subnet} ...")
    nmap_out, nmap_err, nmap_rc = run_command(f"nmap -sn {subnet}", timeout=20)
    if nmap_rc == 0:
        print("[*] Scan results (nmap):")
        print(nmap_out)
        return

    print("nmap is not available, trying arp-scan...")
    arp_out, arp_err, arp_rc = run_command("arp-scan --localnet", timeout=15)
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
            _, _, r = run_command(f"ping -c 1 -W 1 {addr}")
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

def main():
    while True:
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
                ping_target(target)
            else:
                print("IP address required.")
        elif pilihan == "Ping Between Clients":
            target = questionary.text("Enter target IP address:").ask()
            if target:
                ping_target(target)
        elif pilihan == "Change IP (Static / Dynamic)":
            ubah_ip_menu()
        elif pilihan == "Check IP Addresses of All Clients on the Network":
            scan_network()
        elif pilihan == "Exit":
            print("Goodbye...")
            break
        input("\nPress Enter go back...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Cancelled.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
