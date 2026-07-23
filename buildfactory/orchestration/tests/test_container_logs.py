import subprocess

from orchestration.container_logs import ResidentLogSnapshotter


def test_resident_log_snapshot_is_complete_filtered_and_atomic(tmp_path):
    calls = []
    stdout = "line one\n" + ("x" * 200_000) + "\nline last\n"

    def run(args):
        calls.append(args)
        if args[1] == "ps":
            return subprocess.CompletedProcess(
                args,
                0,
                "new-company-ceo\tceo\n"
                "new-company-builder\tdepartment\n"
                "new-company-worker-1\tworker\n"
                "other-company-ceo\t\n",
                "",
            )
        name = args[-1]
        return subprocess.CompletedProcess(args, 0, stdout + name, "stderr-" + name)

    root = tmp_path / "telemetry" / "services" / "agents"
    snapshotter = ResidentLogSnapshotter(
        root,
        company_id="new-company",
        run_command=run,
    )

    assert snapshotter.snapshot_once() == 2
    assert (root / "new-company-ceo.stdout.log").read_text() == stdout + "new-company-ceo"
    assert (root / "new-company-ceo.stderr.log").read_text() == "stderr-new-company-ceo"
    assert not (root / "new-company-worker-1.stdout.log").exists()
    assert calls[0][4] == "label=foundagent.company=new-company"


def test_failed_snapshot_keeps_last_complete_stream(tmp_path):
    attempts = 0

    def run(args):
        nonlocal attempts
        if args[1] == "ps":
            return subprocess.CompletedProcess(args, 0, "new-company-ceo\tceo\n", "")
        attempts += 1
        if attempts == 1:
            return subprocess.CompletedProcess(args, 0, "complete\n", "")
        return subprocess.CompletedProcess(args, 1, "partial", "daemon unavailable")

    snapshotter = ResidentLogSnapshotter(
        tmp_path,
        company_id="new-company",
        run_command=run,
    )
    assert snapshotter.snapshot_once() == 1
    assert snapshotter.snapshot_once() == 0
    assert (tmp_path / "new-company-ceo.stdout.log").read_text() == "complete\n"
