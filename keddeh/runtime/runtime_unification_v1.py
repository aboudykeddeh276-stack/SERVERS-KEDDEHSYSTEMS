from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
import hmac
import json
from typing import Any


class GateError(AssertionError):
    pass


class ReceiptState(StrEnum):
    EXECUTED_PENDING_VERIFICATION = "EXECUTED_PENDING_VERIFICATION"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"


@dataclass(frozen=True)
class Coordinate:
    observer: str
    layer: str
    state: str
    logical_time: int
    evidence: str
    authority: str

    def complete(self) -> bool:
        return all(
            [
                self.observer,
                self.layer,
                self.state,
                self.logical_time > 0,
                self.evidence,
                self.authority,
            ]
        )


@dataclass(frozen=True)
class CellPrimitive:
    prefix: str
    terminal: str
    sector: str
    genome: str
    lineage: str


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def genome_segment(k: int) -> str:
    if k < 1:
        raise ValueError("k is one-indexed")
    return f"G{1 + ((k - 1) % 12):03d}"


def cell_address(primitive: CellPrimitive) -> str:
    payload = f"{primitive.prefix}|{primitive.terminal}|{primitive.sector}|{primitive.genome}"
    return sha256(payload.encode()).hexdigest()


def rehydration_receipt(root_key: bytes, address: str, lineage: str) -> str:
    return hmac.new(root_key, f"{address}|{lineage}".encode(), sha256).hexdigest()


@dataclass
class PlanVFS:
    cells: dict[str, dict[str, Any]] = field(default_factory=dict)

    def atomic_write(self, address: str, payload: dict[str, Any], receipt: str) -> None:
        if not address or not receipt:
            raise GateError("PlanVFS atomic write requires address and receipt")
        existing = self.cells.get(address)
        if existing and existing["receipt"] != receipt:
            raise GateError("duplicate address with conflicting receipt")
        self.cells[address] = {"payload": payload, "receipt": receipt}

    def read(self, address: str) -> dict[str, Any]:
        if address not in self.cells:
            raise GateError(f"missing PlanVFS cell {address}")
        return self.cells[address]


def strongly_connected_components(graph: dict[str, list[str]]) -> list[set[str]]:
    index = 0
    stack: list[str] = []
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    on_stack: set[str] = set()
    components: list[set[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for target in graph.get(node, []):
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])

        if lowlinks[node] == indices[node]:
            component: set[str] = set()
            while True:
                target = stack.pop()
                on_stack.remove(target)
                component.add(target)
                if target == node:
                    break
            components.append(component)

    for node in graph:
        if node not in indices:
            visit(node)
    return components


def prohibited_synchronous_sccs(graph: dict[str, list[str]]) -> list[set[str]]:
    return [c for c in strongly_connected_components(graph) if len(c) > 1]


def insert_mailbox(graph: dict[str, list[str]], source: str, target: str, mailbox: str) -> dict[str, list[str]]:
    transformed = {node: list(edges) for node, edges in graph.items()}
    if target not in transformed.get(source, []):
        raise GateError("cannot insert mailbox on absent edge")
    transformed[source] = [mailbox if edge == target else edge for edge in transformed[source]]
    transformed[mailbox] = []
    transformed.setdefault(target, [])
    return transformed


@dataclass
class CandidateReceipt:
    actor: str
    address: str
    receipt: str
    state: ReceiptState = ReceiptState.EXECUTED_PENDING_VERIFICATION


@dataclass
class VerifiedReceipt:
    verifier: str
    candidate: CandidateReceipt
    head: str
    coordinate: Coordinate
    state: ReceiptState = ReceiptState.SOURCE_VERIFIED


class IndependentVerifier:
    def __init__(self, verifier_id: str, root_key: bytes) -> None:
        self.verifier_id = verifier_id
        self.root_key = root_key

    def verify(self, candidate: CandidateReceipt, primitive: CellPrimitive, previous_head: str, logical_time: int, vfs: PlanVFS) -> VerifiedReceipt:
        if candidate.actor == self.verifier_id:
            raise GateError("actor cannot verify its own candidate receipt")
        expected_address = cell_address(primitive)
        expected_receipt = rehydration_receipt(self.root_key, expected_address, primitive.lineage)
        if candidate.address != expected_address:
            raise GateError("candidate address does not match reconstructed address")
        if candidate.receipt != expected_receipt:
            raise GateError("candidate receipt does not match reconstructed receipt")
        vfs.read(candidate.address)
        coordinate = Coordinate(
            observer="Observer2",
            layer="runtime-unification-v1",
            state=ReceiptState.SOURCE_VERIFIED,
            logical_time=logical_time,
            evidence=candidate.receipt,
            authority=self.verifier_id,
        )
        if not coordinate.complete():
            raise GateError("verified transition lacks 6D coordinate")
        event = {"receipt": candidate.receipt, "state": coordinate.state, "lambda": logical_time}
        head = sha256(f"{previous_head}|{canonical(event)}".encode()).hexdigest()
        return VerifiedReceipt(self.verifier_id, candidate, head, coordinate)


def qualify_runtime_unification(root_key: bytes = b"keddeh-root-key") -> dict[str, Any]:
    vfs = PlanVFS()
    previous_head = "GENESIS"
    receipts: list[VerifiedReceipt] = []

    for k in range(1, 101):
        primitive = CellPrimitive("KEX", f"terminal-mesh-{k:03d}", "S001", genome_segment(k), f"lambda-{k}")
        address = cell_address(primitive)
        receipt = rehydration_receipt(root_key, address, primitive.lineage)
        vfs.atomic_write(address, {"k": k, "genome": primitive.genome}, receipt)
        candidate = CandidateReceipt("TriadCarrierA", address, receipt)
        verified = IndependentVerifier("Observer2Verifier", root_key).verify(candidate, primitive, previous_head, k, vfs)
        previous_head = verified.head
        receipts.append(verified)

    graph = {"terminal": ["compiler"], "compiler": ["terminal"], "carrier": []}
    initial_sccs = prohibited_synchronous_sccs(graph)
    transformed = insert_mailbox(graph, "compiler", "terminal", "compiler_mailbox")
    remaining_sccs = prohibited_synchronous_sccs(transformed)
    if not initial_sccs or remaining_sccs:
        raise GateError("SCC transform failed to remove prohibited synchronous cycle")

    unique_receipts = {r.candidate.receipt for r in receipts}
    if len(unique_receipts) != 100:
        raise GateError("Triad failover duplicate committed effect detected")

    return {
        "qualified": True,
        "cells": len(vfs.cells),
        "genomes": sorted({cell["payload"]["genome"] for cell in vfs.cells.values()}),
        "final_head": previous_head,
        "initial_sccs": [sorted(c) for c in initial_sccs],
        "remaining_sccs": [sorted(c) for c in remaining_sccs],
        "receipt_state": receipts[-1].state,
        "coordinate_complete": receipts[-1].coordinate.complete(),
    }


if __name__ == "__main__":
    print(json.dumps(qualify_runtime_unification(), indent=2, default=str))
