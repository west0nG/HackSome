"""Runtime-neutral one-turn execution for ephemeral Workers and Verifiers.

Give an agent a task → build the argv via the spec's runtime adapter → run it
headless inside the (already running) container via `docker exec` → let the
adapter parse the transcript → return a structured RunResult.

Runtime-neutral since 07-07 codex-runtime: argv building and output parsing
belong to agent.runtimes (runtime_for(spec)); this module keeps ONLY the
docker-exec assembly and the credential mutual-exclusion injection.
"""

import shlex
import subprocess

from agent.credentials import ALL_CREDENTIAL_VARS, CredentialSource, injection_env
from agent.runtimes import runtime_for
from agent.runtimes.base import RunRequest, RunResult
from agent.spec import AgentSpec, credential_for

# In-container mount point of the per-Agent home prepared by its lifecycle
# manager; materialize_home writes into the same directory host-side.
# run_task derives the runtime's home env from it so the CLI reads exactly
# where the loadout landed (codex: CODEX_HOME=<mount>/codex; claude:
# CLAUDE_CONFIG_DIR=<mount>, its default — explicit either way).
AGENT_HOME_MOUNT = "/home/kasm-user/.claude"

# parse_output error prefixes meaning "the CLI produced no terminal event at
# all" (claude: no result event; codex: no turn.completed) — the one case
# where stderr (CLI not found / bad flags) is the useful debugging signal.
_NO_EVENT_ERRORS = ("no result event", "no turn.completed")


def run_task(
    spec: AgentSpec,
    task: str,
    *,
    container: str,
    creds: CredentialSource | None = None,
    timeout: int = 300,
    system_prompt: str | None = None,
    resume_token: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> RunResult:
    """Run `task` as `spec`'s agent inside the running `container`.

    Builds the runtime argv → `docker exec` (with mutually-exclusive
    credential env) → adapter-parses the output → RunResult.

    `resume_token` continues an existing runtime session; this is the Worker
    Manager's same-Goal FAIL/rework seam. Without one, the runtime creates a
    fresh session. `extra_env` injects additional non-credential context into
    the `docker exec`; credential vars in `extra_env` are ignored to preserve
    mutual exclusion."""
    creds = creds or credential_for(spec)
    runtime = runtime_for(spec)
    sp = system_prompt if system_prompt is not None else spec.read_system_prompt()
    req = RunRequest(
        prompt=task,
        charter=sp,
        # mcp_config may be yaml-relative since 07-03 mcp-loadout (mcp/<role>.json);
        # resolve against the yaml's dir, never the process cwd.
        mcp_config=spec.resolve(spec.mcp_config) if spec.mcp_config else None,
        model=spec.model,
        effort=spec.effort,
        resume_token=resume_token,
        bypass_permissions=spec.bypass_permissions,
    )
    argv = runtime.build_argv(req)

    # Mutually-exclusive credential injection (clears the other cred vars), plus
    # the runtime's home env (points the CLI at the materialized loadout), plus
    # any non-credential env the caller added.
    inject = dict(injection_env(creds))
    for k, v in runtime.home_env(AGENT_HOME_MOUNT).items():
        if k not in ALL_CREDENTIAL_VARS:
            inject[k] = v
    for k, v in (extra_env or {}).items():
        if k not in ALL_CREDENTIAL_VARS:
            inject[k] = v
    env_flags: list[str] = []
    for k, v in inject.items():
        env_flags += ["-e", f"{k}={v}"]

    docker_cmd = ["docker", "exec", *env_flags, container, "bash", "-lc", shlex.join(argv)]
    try:
        r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return RunResult(
            ok=False,
            text="",
            error="timeout",
            cost_usd=None,
            raw_tail="",
            raw_output=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
        )

    res = runtime.parse_output(r.stdout, r.returncode)
    res.raw_output = r.stdout or ""
    res.stderr = r.stderr or ""
    if r.stderr and any(m in (res.error or "") for m in _NO_EVENT_ERRORS):
        # surface stderr (e.g. CLI not found / bad flags) for debugging
        res.raw_tail = (r.stdout[-400:] + "\n--stderr--\n" + r.stderr[-400:]).strip()
    return res
