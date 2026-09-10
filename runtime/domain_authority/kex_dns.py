import socket
import struct
import threading
import time

from kex_registrar_service import find_zone, get_records, get_zone, resolve_domain

TYPE = {'A': 1, 'NS': 2, 'CNAME': 5, 'SOA': 6, 'MX': 15, 'TXT': 16, 'AAAA': 28, 'CAA': 257}
REV = {v: k for k, v in TYPE.items()}
MAX_UDP_QUERY = 4096
MAX_TCP_QUERY = 65535


def enc_name(name):
    name = name.rstrip('.')
    if not name:
        return b'\x00'
    labels = name.split('.')
    out = bytearray()
    total = 1
    for label in labels:
        raw = label.encode('idna')
        if not raw or len(raw) > 63:
            raise ValueError('DNS_LABEL_LENGTH')
        total += 1 + len(raw)
        if total > 255:
            raise ValueError('DNS_NAME_TOO_LONG')
        out.append(len(raw))
        out.extend(raw)
    out.append(0)
    return bytes(out)


def enc_rdata(rrtype, value, priority=None):
    if rrtype == 'A':
        return socket.inet_aton(value)
    if rrtype == 'AAAA':
        return socket.inet_pton(socket.AF_INET6, value)
    if rrtype in ('NS', 'CNAME'):
        return enc_name(value)
    if rrtype == 'MX':
        if priority is None:
            raise ValueError('MX_PRIORITY_REQUIRED')
        return struct.pack('!H', int(priority)) + enc_name(value)
    if rrtype == 'TXT':
        raw = value.encode()
        if len(raw) > 255:
            raise ValueError('TXT_RDATA_TOO_LONG')
        return bytes([len(raw)]) + raw
    if rrtype == 'CAA':
        flags, tag, val = value.split(' ', 2)
        tag_b = tag.encode()
        val_b = val.encode()
        if not 1 <= len(tag_b) <= 255:
            raise ValueError('CAA_TAG_LENGTH')
        return bytes([int(flags), len(tag_b)]) + tag_b + val_b
    raise ValueError(f'UNSUPPORTED_RRTYPE:{rrtype}')


def rr(name, rrtype, value, ttl=300, priority=None):
    if int(ttl) <= 0:
        raise ValueError('TTL_MUST_BE_POSITIVE')
    rd = enc_rdata(rrtype, value, priority)
    return enc_name(name) + struct.pack('!HHIH', TYPE[rrtype], 1, int(ttl), len(rd)) + rd


def soa_rr(zone, z):
    rd = (
        enc_name(z['primary_ns'])
        + enc_name(z['admin_rname'])
        + struct.pack('!IIIII', z['serial'], z['refresh'], z['retry'], z['expire'], z['minimum'])
    )
    return enc_name(zone) + struct.pack('!HHIH', TYPE['SOA'], 1, z['minimum'], len(rd)) + rd


def parse_query(data):
    if len(data) < 12:
        raise ValueError('SHORT_DNS_PACKET')
    txid, flags, qd, an, ns, ar = struct.unpack('!HHHHHH', data[:12])
    if qd != 1:
        raise ValueError('DNS_SINGLE_QUESTION_REQUIRED')
    if flags & 0x8000:
        raise ValueError('DNS_QUERY_REQUIRED')
    i = 12
    labels = []
    total_name_len = 1
    while True:
        if i >= len(data):
            raise ValueError('TRUNCATED_QNAME')
        n = data[i]
        i += 1
        if n == 0:
            break
        if n & 0xC0:
            raise ValueError('COMPRESSED_QNAME_NOT_ACCEPTED')
        if n > 63 or i + n > len(data):
            raise ValueError('BAD_QNAME_LABEL')
        raw = data[i:i + n]
        i += n
        total_name_len += n + 1
        if total_name_len > 255:
            raise ValueError('QNAME_TOO_LONG')
        labels.append(raw.decode('idna'))
    if i + 4 > len(data):
        raise ValueError('TRUNCATED_QUESTION')
    qname = '.'.join(labels).lower()
    qtype, qclass = struct.unpack('!HH', data[i:i + 4])
    if qclass != 1:
        raise ValueError('ONLY_IN_CLASS_SUPPORTED')
    question = data[12:i + 4]
    return txid, flags, qd, qname, qtype, qclass, question


class KexDNSServer:
    def __init__(self, host='127.0.0.1', port=9053):
        self.host = host
        self.port = port
        self.running = False
        self.udp = None
        self.tcp = None
        self._threads = []

    def start(self):
        if self.running:
            raise RuntimeError('DNS_ALREADY_RUNNING')
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp.settimeout(1.0)
        self.udp.bind((self.host, self.port))

        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp.settimeout(1.0)
        self.tcp.bind((self.host, self.port))
        self.tcp.listen(128)

        self.running = True
        self._threads = [
            threading.Thread(target=self._udp_loop, daemon=True, name='kex-dns-udp'),
            threading.Thread(target=self._tcp_loop, daemon=True, name='kex-dns-tcp'),
        ]
        for thread in self._threads:
            thread.start()

    def stop(self):
        self.running = False
        for sock in (self.udp, self.tcp):
            if sock:
                try:
                    sock.close()
                except OSError:
                    pass
        for thread in self._threads:
            thread.join(timeout=2)

    def _udp_loop(self):
        while self.running:
            try:
                data, addr = self.udp.recvfrom(MAX_UDP_QUERY)
                response = self._build_response(data)
                self.udp.sendto(response, addr)
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception:
                continue

    def _tcp_loop(self):
        while self.running:
            try:
                client, _ = self.tcp.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._tcp_client, args=(client,), daemon=True).start()

    @staticmethod
    def _recv_exact(sock, length):
        buf = bytearray()
        while len(buf) < length:
            part = sock.recv(length - len(buf))
            if not part:
                raise ConnectionError('TRUNCATED_TCP_DNS_MESSAGE')
            buf.extend(part)
        return bytes(buf)

    def _tcp_client(self, client):
        client.settimeout(5)
        try:
            header = self._recv_exact(client, 2)
            length = struct.unpack('!H', header)[0]
            if length < 12 or length > MAX_TCP_QUERY:
                raise ValueError('BAD_TCP_DNS_LENGTH')
            data = self._recv_exact(client, length)
            response = self._build_response(data)
            client.sendall(struct.pack('!H', len(response)) + response)
        except (OSError, ValueError, ConnectionError):
            pass
        finally:
            client.close()

    def _build_response(self, data):
        txid, qflags, qd, qname, qtype, qclass, question = parse_query(data)
        zone = find_zone(qname)
        qr = 0x8000
        aa = 0x0400
        rd = qflags & 0x0100
        answers = []
        authority = []
        rcode = 0

        if not zone:
            rcode = 3
        else:
            z = get_zone(zone)
            rrtype = REV.get(qtype)
            if rrtype == 'SOA' and qname == zone:
                answers.append(soa_rr(zone, z))
            elif rrtype:
                records = get_records(qname, rrtype)
                if rrtype == 'A' and not records:
                    ip = resolve_domain(qname)
                    if ip:
                        records = [{'name': qname, 'type': 'A', 'value': ip, 'ttl': 60, 'priority': None}]
                for record in records:
                    answers.append(
                        rr(
                            record['name'],
                            record['type'],
                            record['value'],
                            record['ttl'],
                            record.get('priority'),
                        )
                    )
            if not answers:
                any_records = []
                for typ in REV.values():
                    any_records.extend(get_records(qname, typ))
                if not any_records and qname != zone and not resolve_domain(qname):
                    rcode = 3
                authority.append(soa_rr(zone, z))

        flags = qr | aa | rd | rcode
        header = struct.pack('!HHHHHH', txid, flags, qd, len(answers), len(authority), 0)
        return header + question + b''.join(answers) + b''.join(authority)


def start_dns_mesh(host='127.0.0.1', port=9053):
    server = KexDNSServer(host, port)
    server.start()
    return server


if __name__ == '__main__':
    server = start_dns_mesh()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
