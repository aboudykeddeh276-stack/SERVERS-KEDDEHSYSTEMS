from __future__ import annotations

import os
import resource
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, Field


class ResourceLimits(BaseModel):
    max_cpu_seconds: int = Field(default=5, ge=1)
    max_memory_bytes: int = Field(default=268435456, ge=16777216)
    max_file_size_bytes: int = Field(default=10485760, ge=1024)
    max_processes: int = Field(default=10, ge=1)


class SandboxExecutionEngine:
    def __init__(self, limits: ResourceLimits, use_unshare: bool = True):
        self.limits = limits
        self.use_unshare = use_unshare

    def _set_resource_limits(self) -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (self.limits.max_cpu_seconds, self.limits.max_cpu_seconds + 1))
        resource.setrlimit(resource.RLIMIT_AS, (self.limits.max_memory_bytes, self.limits.max_memory_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (self.limits.max_file_size_bytes, self.limits.max_file_size_bytes))
        resource.setrlimit(resource.RLIMIT_NPROC, (self.limits.max_processes, self.limits.max_processes))

    def execute_safe_payload(self, target_script: str) -> Dict[str, Any]:
        with tempfile.NamedTemporaryFile("w", suffix=".py", prefix="keddeh_payload_", delete=False) as handle:
            handle.write(target_script)
            temp_path = Path(handle.name)

        try:
            cmd = ["python3", str(temp_path)]
            if self.use_unshare:
                cmd = ["unshare", "--net", "--ipc", "--uts", *cmd]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=self._set_resource_limits,
                text=True,
            )
            stdout, stderr = process.communicate(timeout=self.limits.max_cpu_seconds + 2)
            return {
                "exit_code": process.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "status": "COMPLETED" if process.returncode == 0 else "EXECUTION_ERROR",
                "isolation": "unshare" if self.use_unshare else "rlimit-only",
            }
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return {
                "exit_code": -1,
                "stdout": stdout,
                "stderr": stderr,
                "status": "TIMEOUT_EXHAUSTED",
                "isolation": "unshare" if self.use_unshare else "rlimit-only",
            }
        except Exception as exc:
            return {
                "exit_code": -2,
                "stdout": "",
                "stderr": str(exc),
                "status": "SANDBOX_CRITICAL_FAULT",
                "isolation": "unshare" if self.use_unshare else "rlimit-only",
            }
        finally:
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    result = SandboxExecutionEngine(ResourceLimits(max_cpu_seconds=2), use_unshare=False).execute_safe_payload(
        "print('sandbox alive')"
    )
    print(result)
