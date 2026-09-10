import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_LEDGER_PATH = Path(__file__).parent / "substrate_ledger" / "keddeh_registrar.sqlite"
LEDGER_PATH = Path(os.environ.get("KEX_REGISTRAR_DB", str(DEFAULT_LEDGER_PATH))).expanduser()
SQLITE_BUSY_MS = int(os.environ.get("KEX_SQLITE_BUSY_MS", "5000"))


def _conn():
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(LEDGER_PATH, timeout=max(1.0, SQLITE_BUSY_MS / 1000.0))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_MS}")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def transaction():
    conn = _conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_registrar_db():
    with transaction() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS global_routing (
            domain TEXT PRIMARY KEY,
            ip_address TEXT NOT NULL,
            port INTEGER,
            owner_hash TEXT,
            status TEXT DEFAULT 'ACTIVE');
        CREATE TABLE IF NOT EXISTS commercial_licenses (
            license_id TEXT PRIMARY KEY,
            owner_email TEXT,
            auth_provider TEXT,
            tier TEXT,
            payment_status TEXT);
        CREATE TABLE IF NOT EXISTS zones (
            zone TEXT PRIMARY KEY,
            primary_ns TEXT NOT NULL,
            admin_rname TEXT NOT NULL,
            serial INTEGER NOT NULL,
            refresh INTEGER NOT NULL DEFAULT 3600,
            retry INTEGER NOT NULL DEFAULT 600,
            expire INTEGER NOT NULL DEFAULT 1209600,
            minimum INTEGER NOT NULL DEFAULT 300,
            owner_hash TEXT,
            status TEXT DEFAULT 'ACTIVE');
        CREATE TABLE IF NOT EXISTS zone_records (
            zone TEXT NOT NULL,
            name TEXT NOT NULL,
            rrtype TEXT NOT NULL,
            value TEXT NOT NULL,
            ttl INTEGER NOT NULL DEFAULT 300,
            priority INTEGER,
            status TEXT DEFAULT 'ACTIVE',
            PRIMARY KEY(zone,name,rrtype,value),
            FOREIGN KEY(zone) REFERENCES zones(zone) ON UPDATE CASCADE ON DELETE CASCADE);
        CREATE INDEX IF NOT EXISTS idx_zone_records_lookup
            ON zone_records(zone,name,rrtype,status);
        ''')
        for domain, ip, port in [
            ('os.keddeh', '127.0.0.1', 8081),
            ('api.keddeh', '127.0.0.1', 8081),
            ('market.keddeh', '127.0.0.1', 8082),
        ]:
            conn.execute(
                "INSERT OR IGNORE INTO global_routing(domain,ip_address,port) VALUES(?,?,?)",
                (domain, ip, port),
            )


def resolve_domain(domain: str):
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT ip_address FROM global_routing WHERE domain=? AND status='ACTIVE'",
            (domain.rstrip('.'),),
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def register_domain(domain: str, ip: str, port: int, owner: str):
    with transaction() as conn:
        conn.execute(
            "INSERT INTO global_routing(domain,ip_address,port,owner_hash,status) VALUES(?,?,?,?, 'ACTIVE') "
            "ON CONFLICT(domain) DO UPDATE SET ip_address=excluded.ip_address,port=excluded.port,"
            "owner_hash=excluded.owner_hash,status='ACTIVE'",
            (domain.rstrip('.'), ip, port, owner),
        )
    return True


def register_zone(zone, primary_ns, admin_rname, serial, owner_hash):
    z = zone.rstrip('.')
    with transaction() as conn:
        current = conn.execute("SELECT serial FROM zones WHERE zone=?", (z,)).fetchone()
        requested = int(serial)
        if current and requested < int(current[0]):
            raise ValueError("ZONE_SERIAL_REGRESSION")
        conn.execute(
            '''INSERT INTO zones(zone,primary_ns,admin_rname,serial,owner_hash,status)
               VALUES(?,?,?,?,?,'ACTIVE')
               ON CONFLICT(zone) DO UPDATE SET primary_ns=excluded.primary_ns,
               admin_rname=excluded.admin_rname,serial=excluded.serial,
               owner_hash=excluded.owner_hash,status='ACTIVE' ''',
            (z, primary_ns.rstrip('.'), admin_rname.rstrip('.'), requested, owner_hash),
        )
    return True


def upsert_record(zone, name, rrtype, value, ttl=300, priority=None):
    z = zone.rstrip('.')
    n = name.rstrip('.')
    t = rrtype.upper()
    if int(ttl) <= 0:
        raise ValueError("TTL_MUST_BE_POSITIVE")
    value_out = value.rstrip('.') if t in {'NS', 'CNAME', 'MX'} else value
    with transaction() as conn:
        if not conn.execute("SELECT 1 FROM zones WHERE zone=? AND status='ACTIVE'", (z,)).fetchone():
            raise KeyError(f"ZONE_NOT_ACTIVE:{z}")
        conn.execute(
            '''INSERT INTO zone_records(zone,name,rrtype,value,ttl,priority,status)
               VALUES(?,?,?,?,?,?,'ACTIVE')
               ON CONFLICT(zone,name,rrtype,value) DO UPDATE SET
               ttl=excluded.ttl,priority=excluded.priority,status='ACTIVE' ''',
            (z, n, t, value_out, int(ttl), priority),
        )
    return True


def get_zone(zone):
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT zone,primary_ns,admin_rname,serial,refresh,retry,expire,minimum,owner_hash,status "
            "FROM zones WHERE zone=?",
            (zone.rstrip('.'),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _zone_candidates(qname):
    q = qname.rstrip('.')
    labels = q.split('.') if q else []
    return ['.'.join(labels[i:]) for i in range(len(labels))]


def find_zone(qname):
    candidates = _zone_candidates(qname)
    if not candidates:
        return None
    conn = _conn()
    try:
        placeholders = ','.join('?' for _ in candidates)
        row = conn.execute(
            f"SELECT zone FROM zones WHERE status='ACTIVE' AND zone IN ({placeholders}) "
            "ORDER BY length(zone) DESC LIMIT 1",
            candidates,
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def get_records(qname, rrtype):
    q = qname.rstrip('.')
    t = rrtype.upper()
    candidates = _zone_candidates(q)
    if not candidates:
        return []
    conn = _conn()
    try:
        placeholders = ','.join('?' for _ in candidates)
        row = conn.execute(
            f"SELECT zone FROM zones WHERE status='ACTIVE' AND zone IN ({placeholders}) "
            "ORDER BY length(zone) DESC LIMIT 1",
            candidates,
        ).fetchone()
        if not row:
            return []
        rows = conn.execute(
            "SELECT name,rrtype,value,ttl,priority FROM zone_records "
            "WHERE zone=? AND name=? AND rrtype=? AND status='ACTIVE'",
            (row[0], q, t),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def database_health():
    conn = _conn()
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        zones = conn.execute("SELECT count(*) FROM zones WHERE status='ACTIVE'").fetchone()[0]
        records = conn.execute("SELECT count(*) FROM zone_records WHERE status='ACTIVE'").fetchone()[0]
        return {
            "database": str(LEDGER_PATH),
            "integrity": integrity,
            "active_zones": int(zones),
            "active_records": int(records),
        }
    finally:
        conn.close()


if __name__ == '__main__':
    init_registrar_db()
    print(database_health())
