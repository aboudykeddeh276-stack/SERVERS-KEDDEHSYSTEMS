# KEDDEH systemd + WebAssembly module packaging

This directory adds a uniform execution envelope around the existing SERVERS-KEDDEHSYSTEMS modules without replacing their source, authority boundaries, ledgers, schedulers, or receipts.

## What is packaged

Every logical repository module has a `module.index.json` containing:

- exact source paths and authority class;
- native, data-only, library, or external execution class;
- systemd unit instance and activation guard;
- WIT world and WebAssembly adapter artifact contract;
- declared VFS, network, dependency, lifecycle, and evidence surfaces;
- separate state and phase roots;
- distinct generator and verifier identities;
- a promotion state that cannot claim deployment before host and external readback.

The aggregate `runtime.index.json` is the only module discovery surface. The schema is `module-index.schema.json`.

## Install and validate

```bash
python3 packaging/bin/keddeh-index.py --root .
sudo packaging/install.sh --source .
systemctl status keddeh-runtime.target
```

Installation validates indexes and units, installs immutable code under `/opt/keddeh/SERVERS-KEDDEHSYSTEMS`, configuration under `/etc/keddeh`, and mutable state under `/var/lib/keddeh`. It does not automatically activate DNS, mesh, registrar, or external network listeners.

Activate an instance only after binding its required environment and authority dependencies:

```bash
sudo systemctl edit keddeh-module@runtime-backbone.service
# Add KEDDEH_ALLOW_ACTIVATION=1 plus the module's required environment.
sudo systemctl enable --now keddeh-module@runtime-backbone.service
sudo systemctl start keddeh-module-health@runtime-backbone.service
```

## WebAssembly build

The portable guest is a deterministic WASI command adapter. The WIT file is the stable interface contract. The Rust host verifies the artifact hash and starts Wasmtime with only declared preopens.

```bash
rustup target add wasm32-wasip1
cargo build --release --target wasm32-wasip1 --manifest-path packaging/wasm/guest/Cargo.toml
cargo build --release --manifest-path packaging/wasm/host/Cargo.toml
sha256sum target/wasm32-wasip1/release/keddeh_module_guest.wasm
```

Write the resulting SHA-256 into a signed release copy of `packaging/wasm/package.template.json`. A null hash is accepted only for CI assembly with the host's explicit `--allow-unpinned` flag; it is rejected by production execution.

## Promotion gates

`SOURCE_DEFINED_PENDING_BUILD_AND_RUNTIME_READBACK` means only that the source package exists. Promotion requires, in order:

1. index, unit, Python, Rust, and WASM build validation;
2. immutable artifact hashes;
3. named host/runtime identity;
4. systemd activation and restart receipt;
5. module-specific health readback;
6. external observer receipt for public listeners;
7. independent verifier identity and receipt.

Repository publication, a workbook row, email, or status prose is not deployment proof.
