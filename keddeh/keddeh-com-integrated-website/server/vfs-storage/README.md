# KEDDEH VFS Storage Boundary

This directory records how KEDDEH VFS and 10 TB storage software should bind to real server hosts.

## Required host mount

The server must expose a real filesystem mount before any 10 TB storage claim is promoted.

Recommended mount path:

```text
/srv/keddeh/vfs
```

Required readback:

```bash
df -h /srv/keddeh/vfs
findmnt /srv/keddeh/vfs
stat /srv/keddeh/vfs
```

## Runtime binding

A KEDDEH service may use the mounted path as a VFS materialization root only after:

1. mount identity is observed;
2. available capacity is read back;
3. service process identity is observed;
4. write/read/delete test passes in a bounded test path;
5. evidence receipt is committed.

## Important distinction

A 10 TB logical namespace is not the same as 10 TB physically provisioned storage. KEDDEH VFS can define the address universe, while the host volume proves materialized capacity.
