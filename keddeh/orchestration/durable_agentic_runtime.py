"""KEDDEH durable agentic runtime primitives.

This module converts the attached orchestration brief into executable source:
strict Pydantic envelopes, email triage schemas, Redis/pgvector memory
schemas, and a deterministic worker->critic->emit state machine.

Boundary: this is source implementation and local simulator code. It is not a
Temporal/AWS deployment, SMTP mutation, database migration, or production queue
binding until those adapters are wired and read back.
"""

from __future__ import annotations

import abc
import hashlib
import hmac
import sys
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class IntentClass(str, Enum):
    ACTION_REQUIRED = "ACTION_REQUIRED"
    INFORMATION_UPDATE = "INFORMATION_UPDATE"
    ESCALATION = "ESCALATION"
    NOISE = "NOISE"


class PipelineTarget(str, Enum):
    DIRECT_SMTP_EMIT = "DIRECT_SMTP_EMIT"
    HUMAN_APPROVAL_QUEUE = "HUMAN_APPROVAL_QUEUE"
    RESEARCH_FORK_INIT = "RESEARCH_FORK_INIT"
    DROP_LOG = "DROP_LOG"


class NodeDestination(str, Enum):
    WORKER_COMPUTE = "WORKER_COMPUTE"
    CRITIC_VALIDATION = "CRITIC_VALIDATION"
    SYSTEM_ORCHESTRATOR = "SYSTEM_ORCHESTRATOR"
    PRODUCTION_EMIT = "PRODUCTION_EMIT"


class EmailAttachmentHeader(BaseModel):
    attachment_id: str = Field(..., description="Unique hash identifier of the file block.")
    filename: str = Field(..., description="Sanitized file name including extension.")
    content_type: str = Field(..., description="Standard MIME type string.")
    size_bytes: int = Field(..., ge=0, description="Exact file size footprint in bytes.")


class RawEmailPayload(BaseModel):
    message_id: str = Field(..., description="Immutable RFC 5322 compliant message identifier.")
    thread_id: str = Field(..., description="Thread/conversation lineage identifier.")
    sender: EmailStr = Field(..., description="Validated originating email address.")
    recipients: List[EmailStr] = Field(..., min_length=1)
    cc: List[EmailStr] = Field(default_factory=list)
    timestamp: datetime = Field(...)
    subject: str = Field(...)
    body_plain: str = Field(...)
    attachments: List[EmailAttachmentHeader] = Field(default_factory=list)


class CRMClientContext(BaseModel):
    account_id: str
    tier: Literal["ENTERPRISE", "MID_MARKET", "SMB"]
    active_contracts_value_usd: float = Field(..., ge=0)
    sla_response_window_minutes: int = Field(..., ge=1)
    status: Literal["ACTIVE", "CHURN_RISK", "DELINQUENT"]


class VectorThreadSummary(BaseModel):
    historical_thread_id: str
    similarity_score: float = Field(..., ge=0, le=1)
    resolved_resolution: str


class ConsolidatedAssemblyContext(BaseModel):
    raw_input: RawEmailPayload
    crm_metadata: Optional[CRMClientContext] = None
    historical_matches: List[VectorThreadSummary] = Field(default_factory=list)


class IntentTriageMatrix(BaseModel):
    intent_classification: IntentClass
    confidence_score: float = Field(..., ge=0, le=1)
    urgency_weight: int = Field(..., ge=1, le=5)
    financial_risk_exposure_usd: float = Field(default=0.0, ge=0)
    primary_extracted_entities: Dict[str, str] = Field(default_factory=dict)


class ExecutionDraftPayload(BaseModel):
    draft_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    recipient_routing: EmailStr
    response_body_html: str
    required_system_tools: List[str] = Field(default_factory=list)


class CriticEvaluationRubric(BaseModel):
    is_compliant_with_sla: bool
    hallucination_detected: bool
    risk_threshold_breached: bool
    required_prompt_modifications: Optional[str] = None


class RoutingDecisionPayload(BaseModel):
    action_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    target_pipeline: PipelineTarget
    routing_reasoning: str


class RedisSessionState(BaseModel):
    actor_id: str
    active_thread_lock: bool = True
    current_state_node: str
    volatile_kv_cache: Dict[str, str] = Field(default_factory=dict)
    ttl_seconds_remaining: int = Field(default=3600, ge=0)

    @field_validator("actor_id")
    @classmethod
    def validate_hash_format(cls, value: str) -> str:
        if not value.isalnum():
            raise ValueError("actor_id must be strict alphanumeric text")
        return value


class MemoryCachePacket(BaseModel):
    query_signature_hash: str
    cached_completion_payload: str
    execution_latency_ms: float = Field(..., ge=0)
    idempotency_token: str

    def verify_integrity(self, system_secret: bytes) -> bool:
        expected_token = hmac.new(
            system_secret,
            self.query_signature_hash.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(self.idempotency_token, expected_token)


class VectorIndexingContext(BaseModel):
    document_uuid: str
    semantic_embedding_vector: List[float]
    payload_metadata_json: Dict[str, str]
    cosine_distance_threshold: float = Field(default=0.85, ge=0, le=1)

    @field_validator("semantic_embedding_vector")
    @classmethod
    def enforce_fixed_dimensionality(cls, value: List[float]) -> List[float]:
        if len(value) not in (1536, 3072):
            raise ValueError("semantic_embedding_vector must contain 1536 or 3072 dimensions")
        return value


class ExecutionTrace(BaseModel):
    task_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    execution_line_code: str
    allocated_memory_mb: int = Field(default=256, ge=16)
    target_ports_verified: List[int] = Field(default_factory=list)

    @field_validator("target_ports_verified")
    @classmethod
    def validate_ports(cls, ports: List[int]) -> List[int]:
        for port in ports:
            if port < 1 or port > 65535:
                raise ValueError(f"invalid TCP/UDP port: {port}")
        return ports


class ValidationFeedback(BaseModel):
    is_compliant: bool
    error_signature: Optional[str] = None
    remediation_instructions: Optional[str] = None


class AgentMessageEnvelope(BaseModel):
    envelope_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    origin_node: NodeDestination
    destination_node: NodeDestination
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload_trace: ExecutionTrace
    validation_results: Optional[ValidationFeedback] = None
    loop_iteration_count: int = Field(default=0, ge=0)


class BaseActorNode(abc.ABC):
    @abc.abstractmethod
    def handle_envelope(self, envelope: AgentMessageEnvelope) -> AgentMessageEnvelope:
        raise NotImplementedError


class OperationalWorkerNode(BaseActorNode):
    def __init__(self, node_id: NodeDestination = NodeDestination.WORKER_COMPUTE):
        self.node_id = node_id

    def handle_envelope(self, envelope: AgentMessageEnvelope) -> AgentMessageEnvelope:
        sys.stdout.write(
            f"[{datetime.now(timezone.utc).isoformat()}] [NODE_EXEC] "
            f"[{self.node_id}] Processing payload transaction: {envelope.envelope_id}\n"
        )
        sys.stdout.flush()

        current_trace = envelope.payload_trace
        current_code = current_trace.execution_line_code

        if envelope.validation_results and not envelope.validation_results.is_compliant:
            patch_directive = envelope.validation_results.remediation_instructions or "remove invalid operations"
            updated_code = (
                f"# PATCHED VIA CRITIC DIRECTIVE: {patch_directive}\n"
                + current_code.replace("import os", "# SYSTEM_IMPORT_BLOCKED")
                .replace("subprocess", "# SUBPROCESS BLOCKED")
                .replace("os.system", "# SYSTEM_CALL_BLOCKED")
                .replace("rm -rf", "REMOVED_DANGEROUS_DELETE")
            )
        else:
            updated_code = current_code

        updated_trace = ExecutionTrace(
            task_id=current_trace.task_id,
            execution_line_code=updated_code,
            allocated_memory_mb=current_trace.allocated_memory_mb,
            target_ports_verified=current_trace.target_ports_verified,
        )

        return AgentMessageEnvelope(
            origin_node=self.node_id,
            destination_node=NodeDestination.CRITIC_VALIDATION,
            payload_trace=updated_trace,
            loop_iteration_count=envelope.loop_iteration_count,
        )


class ArchitecturalCriticNode(BaseActorNode):
    def __init__(
        self,
        node_id: NodeDestination = NodeDestination.CRITIC_VALIDATION,
        error_budget_max: int = 3,
    ):
        self.node_id = node_id
        self.error_budget_max = error_budget_max

    def handle_envelope(self, envelope: AgentMessageEnvelope) -> AgentMessageEnvelope:
        sys.stdout.write(
            f"[{datetime.now(timezone.utc).isoformat()}] [NODE_EXEC] "
            f"[{self.node_id}] Validating execution trace from source: {envelope.origin_node}\n"
        )
        sys.stdout.flush()

        trace = envelope.payload_trace
        code_payload = trace.execution_line_code
        current_iteration = envelope.loop_iteration_count + 1

        has_forbidden_import = "import os" in code_payload or "subprocess" in code_payload
        has_forbidden_call = "os.system" in code_payload or "rm -rf" in code_payload
        has_empty_payload = len(code_payload.strip()) == 0

        if has_forbidden_import or has_forbidden_call or has_empty_payload:
            if current_iteration >= self.error_budget_max:
                return AgentMessageEnvelope(
                    origin_node=self.node_id,
                    destination_node=NodeDestination.SYSTEM_ORCHESTRATOR,
                    payload_trace=trace,
                    validation_results=ValidationFeedback(
                        is_compliant=False,
                        error_signature="EXHAUSTED_REMEDIATION_BUDGET",
                        remediation_instructions="Execution terminated due to structural violations.",
                    ),
                    loop_iteration_count=current_iteration,
                )

            return AgentMessageEnvelope(
                origin_node=self.node_id,
                destination_node=NodeDestination.WORKER_COMPUTE,
                payload_trace=trace,
                validation_results=ValidationFeedback(
                    is_compliant=False,
                    error_signature="SECURITY_POLICY_VIOLATION" if not has_empty_payload else "EMPTY_EXECUTION_TRACE",
                    remediation_instructions="Remove unauthorized system commands and clean target strings immediately.",
                ),
                loop_iteration_count=current_iteration,
            )

        return AgentMessageEnvelope(
            origin_node=self.node_id,
            destination_node=NodeDestination.PRODUCTION_EMIT,
            payload_trace=trace,
            validation_results=ValidationFeedback(is_compliant=True),
            loop_iteration_count=current_iteration,
        )


class WorkerCriticPipeline:
    def __init__(self, error_budget_max: int = 3):
        self.worker = OperationalWorkerNode()
        self.critic = ArchitecturalCriticNode(error_budget_max=error_budget_max)

    def run(self, trace: ExecutionTrace) -> AgentMessageEnvelope:
        envelope = AgentMessageEnvelope(
            origin_node=NodeDestination.SYSTEM_ORCHESTRATOR,
            destination_node=NodeDestination.WORKER_COMPUTE,
            payload_trace=trace,
        )

        while envelope.destination_node not in {
            NodeDestination.PRODUCTION_EMIT,
            NodeDestination.SYSTEM_ORCHESTRATOR,
        }:
            if envelope.destination_node == NodeDestination.WORKER_COMPUTE:
                envelope = self.worker.handle_envelope(envelope)
            elif envelope.destination_node == NodeDestination.CRITIC_VALIDATION:
                envelope = self.critic.handle_envelope(envelope)
            else:
                raise RuntimeError(f"unhandled destination: {envelope.destination_node}")

        return envelope


def main() -> int:
    initial_trace = ExecutionTrace(
        execution_line_code="import os\ndef run_task():\n    os.system('rm -rf /')\n    return True",
        target_ports_verified=[5432],
    )
    result = WorkerCriticPipeline(error_budget_max=3).run(initial_trace)
    print(f"[FINAL_PIPELINE_RESULT_STATE]: {result.destination_node}")
    print(f"[FINAL_LOOP_COUNT]: {result.loop_iteration_count}")
    print(f"[FINAL_OUTPUT_SCRIPT_SURFACE]:\n{result.payload_trace.execution_line_code}")
    return 0 if result.destination_node == NodeDestination.PRODUCTION_EMIT else 1


if __name__ == "__main__":
    raise SystemExit(main())
