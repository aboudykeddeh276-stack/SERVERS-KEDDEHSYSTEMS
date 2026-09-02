import sqlite3
import os
from pathlib import Path

LEDGER_PATH = Path(__file__).parent / "substrate_ledger" / "keddeh_registrar.sqlite"

def _conn():
    os.makedirs(LEDGER_PATH.parent, exist_ok=True)
    return sqlite3.connect(LEDGER_PATH)

def init_registrar_db():
    conn=_conn(); c=conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS global_routing (
        domain TEXT PRIMARY KEY,
        ip_address TEXT NOT NULL,
        port INTEGER,
        owner_hash TEXT,
        status TEXT DEFAULT 'ACTIVE')''')
    c.execute('''CREATE TABLE IF NOT EXISTS commercial_licenses (
        license_id TEXT PRIMARY KEY, owner_email TEXT, auth_provider TEXT,
        tier TEXT, payment_status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS zones (
        zone TEXT PRIMARY KEY, primary_ns TEXT NOT NULL, admin_rname TEXT NOT NULL,
        serial INTEGER NOT NULL, refresh INTEGER NOT NULL DEFAULT 3600,
        retry INTEGER NOT NULL DEFAULT 600, expire INTEGER NOT NULL DEFAULT 1209600,
        minimum INTEGER NOT NULL DEFAULT 300, owner_hash TEXT, status TEXT DEFAULT 'ACTIVE')''')
    c.execute('''CREATE TABLE IF NOT EXISTS zone_records (
        zone TEXT NOT NULL, name TEXT NOT NULL, rrtype TEXT NOT NULL,
        value TEXT NOT NULL, ttl INTEGER NOT NULL DEFAULT 300,
        priority INTEGER, status TEXT DEFAULT 'ACTIVE',
        PRIMARY KEY(zone,name,rrtype,value))''')
    for domain,ip,port in [('os.keddeh','127.0.0.1',8081),('api.keddeh','127.0.0.1',8081),('market.keddeh','127.0.0.1',8082)]:
        c.execute("INSERT OR IGNORE INTO global_routing(domain,ip_address,port) VALUES(?,?,?)",(domain,ip,port))
    conn.commit();conn.close()

def resolve_domain(domain:str):
    try:
        conn=_conn(); row=conn.execute("SELECT ip_address FROM global_routing WHERE domain=? AND status='ACTIVE'",(domain.rstrip('.'),)).fetchone();conn.close();return row[0] if row else None
    except Exception: return None

def register_domain(domain:str,ip:str,port:int,owner:str):
    conn=_conn();conn.execute("INSERT OR REPLACE INTO global_routing(domain,ip_address,port,owner_hash,status) VALUES(?,?,?,?, 'ACTIVE')",(domain.rstrip('.'),ip,port,owner));conn.commit();conn.close();return True

def register_zone(zone,primary_ns,admin_rname,serial,owner_hash):
    z=zone.rstrip('.')
    conn=_conn();conn.execute('''INSERT OR REPLACE INTO zones(zone,primary_ns,admin_rname,serial,owner_hash,status)
        VALUES(?,?,?,?,?,'ACTIVE')''',(z,primary_ns.rstrip('.'),admin_rname.rstrip('.'),int(serial),owner_hash));conn.commit();conn.close();return True

def upsert_record(zone,name,rrtype,value,ttl=300,priority=None):
    z=zone.rstrip('.'); n=name.rstrip('.')
    conn=_conn();conn.execute('''INSERT OR REPLACE INTO zone_records(zone,name,rrtype,value,ttl,priority,status)
        VALUES(?,?,?,?,?,?,'ACTIVE')''',(z,n,rrtype.upper(),value.rstrip('.') if rrtype.upper() in {'NS','CNAME','MX'} else value,int(ttl),priority));conn.commit();conn.close();return True

def get_zone(zone):
    conn=_conn();r=conn.execute("SELECT zone,primary_ns,admin_rname,serial,refresh,retry,expire,minimum,owner_hash,status FROM zones WHERE zone=?",(zone.rstrip('.'),)).fetchone();conn.close();
    if not r:return None
    keys=['zone','primary_ns','admin_rname','serial','refresh','retry','expire','minimum','owner_hash','status'];return dict(zip(keys,r))

def _zone_candidates(qname):
    q=qname.rstrip('.')
    labels=q.split('.') if q else []
    return ['.'.join(labels[i:]) for i in range(len(labels))]

def find_zone(qname):
    candidates=_zone_candidates(qname)
    if not candidates:return None
    conn=_conn()
    try:
        placeholders=','.join('?' for _ in candidates)
        row=conn.execute(
            f"SELECT zone FROM zones WHERE status='ACTIVE' AND zone IN ({placeholders}) ORDER BY length(zone) DESC LIMIT 1",
            candidates
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def get_records(qname,rrtype):
    q=qname.rstrip('.'); t=rrtype.upper(); candidates=_zone_candidates(q)
    if not candidates:return []
    conn=_conn()
    try:
        placeholders=','.join('?' for _ in candidates)
        row=conn.execute(
            f"SELECT zone FROM zones WHERE status='ACTIVE' AND zone IN ({placeholders}) ORDER BY length(zone) DESC LIMIT 1",
            candidates
        ).fetchone()
        if not row:return []
        rows=conn.execute(
            "SELECT name,rrtype,value,ttl,priority FROM zone_records WHERE zone=? AND name=? AND rrtype=? AND status='ACTIVE'",
            (row[0],q,t)
        ).fetchall()
        return [{'name':r[0],'type':r[1],'value':r[2],'ttl':r[3],'priority':r[4]} for r in rows]
    finally:
        conn.close()

if __name__=='__main__': init_registrar_db()
