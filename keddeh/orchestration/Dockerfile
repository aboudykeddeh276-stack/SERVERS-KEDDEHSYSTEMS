FROM python:3.11-alpine3.19 AS base_compiler

RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    util-linux

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-alpine3.19 AS application_sandbox

RUN apk add --no-cache \
    util-linux \
    libpq \
    shadow

RUN groupadd -g 10001 agent_team && \
    useradd -u 10001 -g agent_team -m -s /bin/false deployer_kernel

WORKDIR /workspace

COPY --from=base_compiler /root/.local /home/deployer_kernel/.local
COPY . /workspace

RUN chown -R deployer_kernel:agent_team /workspace && \
    chmod -R 750 /workspace

ENV PATH=/home/deployer_kernel/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

USER deployer_kernel

ENTRYPOINT ["python3", "durable_agentic_runtime.py"]
