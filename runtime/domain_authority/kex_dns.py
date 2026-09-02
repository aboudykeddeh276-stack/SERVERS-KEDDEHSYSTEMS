import socket,struct,threading,time
from kex_registrar_service import find_zone,get_zone,get_records,resolve_domain

TYPE={'A':1,'NS':2,'CNAME':5,'SOA':6,'MX':15,'TXT':16,'AAAA':28,'CAA':257}
REV={v:k for k,v in TYPE.items()}

def enc_name(name):
    name=name.rstrip('.')
    return b''.join(bytes([len(x)])+x.encode() for x in name.split('.'))+b'\x00'

def enc_rdata(rrtype,value,zone=None):
    if rrtype=='A': return socket.inet_aton(value)
    if rrtype=='AAAA': return socket.inet_pton(socket.AF_INET6,value)
    if rrtype in ('NS','CNAME'): return enc_name(value)
    if rrtype=='TXT':
        b=value.encode();return bytes([len(b)])+b
    if rrtype=='CAA':
        flags,tag,val=value.split(' ',2); tb=tag.encode();vb=val.encode();return bytes([int(flags),len(tb)])+tb+vb
    raise ValueError(rrtype)

def rr(name,rrtype,value,ttl=300):
    rd=enc_rdata(rrtype,value);return enc_name(name)+struct.pack('!HHIH',TYPE[rrtype],1,int(ttl),len(rd))+rd

def soa_rr(zone,z):
    rd=enc_name(z['primary_ns'])+enc_name(z['admin_rname'])+struct.pack('!IIIII',z['serial'],z['refresh'],z['retry'],z['expire'],z['minimum'])
    return enc_name(zone)+struct.pack('!HHIH',TYPE['SOA'],1,z['minimum'],len(rd))+rd

def parse_query(data):
    if len(data)<12: raise ValueError('short DNS packet')
    txid,flags,qd,an,ns,ar=struct.unpack('!HHHHHH',data[:12]);i=12;labels=[]
    while True:
        n=data[i];i+=1
        if n==0:break
        labels.append(data[i:i+n].decode());i+=n
    qname='.'.join(labels);qtype,qclass=struct.unpack('!HH',data[i:i+4]);return txid,flags,qd,qname,qtype,qclass,data[12:i+4]

class KexDNSServer:
    def __init__(self,host='127.0.0.1',port=9053):self.host=host;self.port=port;self.running=False;self.udp=None;self.tcp=None
    def start(self):
        self.running=True
        self.udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);self.udp.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);self.udp.bind((self.host,self.port))
        self.tcp=socket.socket(socket.AF_INET,socket.SOCK_STREAM);self.tcp.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);self.tcp.bind((self.host,self.port));self.tcp.listen(32)
        threading.Thread(target=self._udp_loop,daemon=True).start();threading.Thread(target=self._tcp_loop,daemon=True).start()
    def stop(self):
        self.running=False
        for s in (self.udp,self.tcp):
            try:s.close()
            except:pass
    def _udp_loop(self):
        while self.running:
            try:
                d,a=self.udp.recvfrom(4096);r=self._build_response(d);self.udp.sendto(r,a)
            except OSError:break
            except Exception:continue
    def _tcp_loop(self):
        while self.running:
            try:c,_=self.tcp.accept()
            except OSError:break
            threading.Thread(target=self._tcp_client,args=(c,),daemon=True).start()
    def _tcp_client(self,c):
        try:
            h=c.recv(2)
            if len(h)!=2:return
            n=struct.unpack('!H',h)[0];d=b''
            while len(d)<n:
                b=c.recv(n-len(d));
                if not b:break
                d+=b
            r=self._build_response(d);c.sendall(struct.pack('!H',len(r))+r)
        finally:c.close()
    def _build_response(self,data):
        txid,qflags,qd,qname,qtype,qclass,question=parse_query(data);zone=find_zone(qname)
        aa=0x0400; qr=0x8000; rd=qflags&0x0100
        answers=[];authority=[];rcode=0
        if not zone:
            rcode=3
        else:
            z=get_zone(zone); t=REV.get(qtype)
            if t=='SOA' and qname==zone: answers.append(soa_rr(zone,z))
            elif t:
                recs=get_records(qname,t)
                if t=='A' and not recs:
                    ip=resolve_domain(qname)
                    if ip: recs=[{'name':qname,'type':'A','value':ip,'ttl':60}]
                for x in recs: answers.append(rr(x['name'],x['type'],x['value'],x['ttl']))
            if not answers:
                anytypes=[]
                for typ in REV.values(): anytypes.extend(get_records(qname,typ))
                if not anytypes and qname!=zone and not resolve_domain(qname): rcode=3
                authority.append(soa_rr(zone,z))
        flags=qr|aa|rd|rcode
        hdr=struct.pack('!HHHHHH',txid,flags,qd,len(answers),len(authority),0)
        return hdr+question+b''.join(answers)+b''.join(authority)

def start_dns_mesh(host='127.0.0.1',port=9053):
    s=KexDNSServer(host,port);s.start();return s

if __name__=='__main__':
    s=start_dns_mesh();
    try:
        while True:time.sleep(1)
    except KeyboardInterrupt:s.stop()
