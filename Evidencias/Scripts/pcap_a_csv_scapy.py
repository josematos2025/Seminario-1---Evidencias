import sys
import os
import csv
from collections import defaultdict
from scapy.all import PcapReader, IP, TCP, UDP

def procesar_pcap(pcap_path, output_csv, tipo_trafico="normal"):
    if not os.path.exists(pcap_path):
        print(f"[ERROR] No existe el archivo: {pcap_path}")
        return

    print(f"Leyendo '{pcap_path}' de forma iterativa con Scapy...")
    
    flujos_tcp = defaultdict(list)
    flujos_udp = defaultdict(list)
    total_ip = 0

    try:
        # PcapReader lee paquete por paquete en streaming (mucho mas rapido y eficiente en RAM)
        with PcapReader(pcap_path) as pcap_reader:
            for pkt in pcap_reader:
                if not pkt.haslayer(IP):
                    continue

                total_ip += 1
                if total_ip % 50000 == 0:
                    print(f"  ... procesados {total_ip} paquetes IP")

                ip_layer = pkt[IP]
                time_epoch = float(pkt.time)
                ip_src = ip_layer.src
                ip_dst = ip_layer.dst
                length = len(pkt)

                pkt_info = {'time': time_epoch, 'src': ip_src, 'dst': ip_dst, 'len': length}

                if pkt.haslayer(TCP):
                    tcp_layer = pkt[TCP]
                    pair = tuple(sorted([f"{ip_src}:{tcp_layer.sport}", f"{ip_dst}:{tcp_layer.dport}"]))
                    flujos_tcp[pair].append(pkt_info)
                elif pkt.haslayer(UDP):
                    udp_layer = pkt[UDP]
                    pair = tuple(sorted([f"{ip_src}:{udp_layer.sport}", f"{ip_dst}:{udp_layer.dport}"]))
                    flujos_udp[pair].append(pkt_info)

    except Exception as e:
        print(f"[ERROR] Ocurrio un problema leyendo el pcap: {e}")
        return

    print(f"  [+] Total Paquetes IP leídos: {total_ip}")
    print(f"  [+] Flujos TCP agrupados: {len(flujos_tcp)}")
    print(f"  [+] Flujos UDP agrupados: {len(flujos_udp)}")

    filas_csv = []

    # Procesar TCP
    for pair, pkts in flujos_tcp.items():
        if not pkts:
            continue
        src_ip_init = pkts[0]['src']
        dst_ip_init = pkts[0]['dst']
        duration = round(pkts[-1]['time'] - pkts[0]['time'], 6)

        src_bytes = sum(p['len'] for p in pkts if p['src'] == src_ip_init)
        dst_bytes = sum(p['len'] for p in pkts if p['src'] != src_ip_init)
        src_pkts = sum(1 for p in pkts if p['src'] == src_ip_init)
        dst_pkts = sum(1 for p in pkts if p['src'] != src_ip_init)

        filas_csv.append([src_ip_init, dst_ip_init, f"{duration:.6f}", src_bytes, dst_bytes, src_pkts, dst_pkts, tipo_trafico])

    # Procesar UDP
    for pair, pkts in flujos_udp.items():
        if not pkts:
            continue

        sub_flujos = []
        actual = [pkts[0]]
        for p in pkts[1:]:
            if p['time'] - actual[-1]['time'] > 2.0:
                sub_flujos.append(actual)
                actual = [p]
            else:
                actual.append(p)
        sub_flujos.append(actual)

        for sub in sub_flujos:
            src_ip_init = sub[0]['src']
            dst_ip_init = sub[0]['dst']
            duration = round(sub[-1]['time'] - sub[0]['time'], 6)

            src_bytes = sum(p['len'] for p in sub if p['src'] == src_ip_init)
            dst_bytes = sum(p['len'] for p in sub if p['src'] != src_ip_init)
            src_pkts = sum(1 for p in sub if p['src'] == src_ip_init)
            dst_pkts = sum(1 for p in sub if p['src'] != src_ip_init)

            filas_csv.append([src_ip_init, dst_ip_init, f"{duration:.6f}", src_bytes, dst_bytes, src_pkts, dst_pkts, tipo_trafico])

    with open(output_csv, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['src_ip', 'dst_ip', 'duration', 'src_bytes', 'dst_bytes', 'src_pkts', 'dst_pkts', 'type'])
        writer.writerows(filas_csv)

    print(f"  [OK] Guardado en: {output_csv} ({len(filas_csv)} filas)\n")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Uso: python3 pcap_a_csv_scapy.py <pcap> <csv> <tipo>")
        sys.exit(1)
    procesar_pcap(sys.argv[1], sys.argv[2], sys.argv[3])
