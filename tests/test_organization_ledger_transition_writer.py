"""organization-ledger-transition.yml on push: the committed packet supplies the epoch.

Ported in scope from StegVerse-Labs/.github tests/test_organization_ledger_transition_writer.py
(its dispatch-free trigger checks) for an organization installed from StegVerse-org/.github
components/intr-ingress-ledger/v1 whose ledger ref may not exist yet. The writer's own step
scripts are taken from the workflow file and run with bash in a temporary clone whose origin
is an empty bare repository, so the genesis branch is exercised. Nothing is pushed: the run
stops after the self-closure step. Receipts here are exercise evidence on temporary
repositories, not records of the published organization ledger. No clock and no network.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "organization-ledger-transition.yml"
REF = "refs/stegverse/organization-ledger"
PACKET = ".stegverse/intr-destination/self-closure-packet.json"
SCHEMA = "stegverse.intr-destination-self-closure-packet/v1"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
STEPS = ("Bind the designated organization ledger ref and the repository ledger subtree within it",
         "Read the self-closure inputs from the pushed commit's packet",
         "Perform the intr-destination diagnostic self-closure")
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.invalid", "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
           "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z", "GIT_CONFIG_NOSYSTEM": "1",
           # No detached auto-gc or maintenance may still be writing .git when the temp dir is removed.
           "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "gc.auto", "GIT_CONFIG_VALUE_0": "0",
           "GIT_CONFIG_KEY_1": "maintenance.auto", "GIT_CONFIG_VALUE_1": "false"}


def step_script(name: str) -> str:
    """The `run: |` block of the named step, dedented."""
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    start = lines.index("      - name: " + name)
    body, inside = [], False
    for line in lines[start + 1:]:
        if line.startswith("      - name: "):
            break
        if line == "        run: |":
            inside = True
            continue
        if inside:
            if line.strip() and not line.startswith("          "):
                break
            body.append(line[10:])
    assert body, name
    return "\n".join(body) + "\n"


class PushOnPacket(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(self._tmp.name)
        self.ws, self.runner, self.origin = tmp / "ws", tmp / "runner", tmp / "origin.git"
        self.runner.mkdir()
        files = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"], capture_output=True,
                               check=True).stdout.decode().split("\0")
        for rel in filter(None, files):
            src = ROOT / rel
            if src.is_file() and rel != PACKET:
                (self.ws / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, self.ws / rel)
        shim = tmp / "bin"
        shim.mkdir()
        (shim / "python").symlink_to(sys.executable)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "STEGVERSE_"))}
        self.env.update(GIT_ENV)
        self.env["PATH"] = str(shim) + os.pathsep + self.env.get("PATH", "")
        self.git("init", "-q", "--bare", str(self.origin), cwd=tmp)
        self.git("init", "-q")
        self.git("remote", "add", "origin", str(self.origin))

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.ws, env=self.env, capture_output=True,
                              check=True).stdout.decode().strip()

    def commit(self, packet):
        if packet is not None:
            (self.ws / PACKET).parent.mkdir(parents=True, exist_ok=True)
            (self.ws / PACKET).write_text(packet if isinstance(packet, str) else json.dumps(packet),
                                          encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "packet")

    def run_writer(self):
        """Run the writer's steps in order, as the runner would; stop at the first failing step."""
        env = dict(self.env, GITHUB_WORKSPACE=str(self.ws), RUNNER_TEMP=str(self.runner), LEDGER_REF=REF,
                   GITHUB_SHA=self.git("rev-parse", "HEAD"))
        github_env = self.runner / "github_env"
        github_env.write_text("")
        out = ""
        for name in STEPS:
            env["GITHUB_ENV"] = str(github_env)
            done = subprocess.run(["bash", "-e", "-c", step_script(name)], cwd=self.ws, env=env,
                                  capture_output=True, text=True)
            out += done.stdout + done.stderr
            if done.returncode != 0:
                return done.returncode, out, name
            for line in github_env.read_text().splitlines():
                key, _, value = line.partition("=")
                env[key] = value
        return 0, out, None

    def refusal(self, out):
        line = [l for l in out.splitlines() if l.startswith("{") and '"FAIL_CLOSED"' in l][-1]
        result = json.loads(line)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        for field in SIX:
            self.assertTrue(str(result.get(field) or "").strip(), field)
        return result

    def assert_nothing_appended(self):
        refs = subprocess.run(["git", "show-ref"], cwd=self.ws, env=self.env, capture_output=True,
                              text=True).stdout
        self.assertNotIn(REF, refs)

    def test_an_absent_packet_is_a_six_field_refusal_and_nothing_is_appended(self):
        self.commit(None)
        code, out, step = self.run_writer()
        self.assertEqual((code != 0, step), (True, STEPS[1]))
        self.assertEqual(self.refusal(out)["failure_code"], "SELF_CLOSURE_PACKET_ABSENT")
        self.assert_nothing_appended()

    def test_a_malformed_packet_is_a_six_field_refusal_and_nothing_is_appended(self):
        for packet, code_expected in (("{not json", "SELF_CLOSURE_PACKET_UNREADABLE"),
                                      ({"schema": SCHEMA, "communication_id": "c-1"}, "SELF_CLOSURE_HB_EPOCH_UNSUPPLIED"),
                                      ({"schema": SCHEMA, "communication_id": "c-1", "hb_epoch": "40"},
                                       "SELF_CLOSURE_HB_EPOCH_INVALID")):
            with self.subTest(packet=packet):
                self.commit(packet)
                code, out, step = self.run_writer()
                self.assertEqual((code != 0, step), (True, STEPS[1]))
                self.assertEqual(self.refusal(out)["failure_code"], code_expected)
                self.assert_nothing_appended()

    def test_an_epoch_below_the_hb32_anchor_is_refused_before_any_append(self):
        for epoch in (0, 7, 31):
            with self.subTest(epoch=epoch):
                self.commit({"schema": SCHEMA, "communication_id": "c-low", "hb_epoch": epoch})
                code, out, step = self.run_writer()
                self.assertEqual((code != 0, step), (True, STEPS[2]))
                self.assertEqual(self.refusal(out)["failure_code"], "SELF_CLOSURE_HB_EPOCH_PRECEDES_HB32_ANCHOR")
                self.assert_nothing_appended()

    def test_a_path_like_identifier_is_refused_before_any_append(self):
        self.commit({"schema": SCHEMA, "communication_id": "a/../b", "hb_epoch": 40})
        code, out, step = self.run_writer()
        self.assertEqual((code != 0, step), (True, STEPS[2]))
        self.assertEqual(self.refusal(out)["failure_code"], "SELF_CLOSURE_INPUT_INVALID")
        self.assert_nothing_appended()

    def test_a_supplied_epoch_opens_the_ledger_at_genesis_with_derived_from_clock_false(self):
        epoch = 469411750
        self.commit({"schema": SCHEMA, "communication_id": "genesis-test-001", "hb_epoch": epoch})
        code, out, step = self.run_writer()
        self.assertEqual(code, 0, out + str(step))
        self.assertIn("the first append opens it at genesis", out)
        closure = json.loads((self.runner / "results/self-closure/closure.json").read_text())
        self.assertEqual(closure["disposition"], "ALLOW")
        tree = self.git("ls-tree", "-r", "--name-only", REF).splitlines()
        receipts = [p for p in tree if "/receipts/" in "/" + p and p.endswith(".json")]
        self.assertGreaterEqual(len(receipts), 2, tree)
        for path in receipts:
            receipt = json.loads(self.git("show", REF + ":" + path))
            self.assertEqual(receipt["hb_reference"]["epoch"], epoch, path)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False, path)
            self.assertNotIn("sampled_unix_ns", receipt["hb_reference"], path)
        # The same packet replays from the ledger instead of minting another pair.
        tip = self.git("rev-parse", REF)
        code, out, _ = self.run_writer()
        self.assertEqual(code, 0, out)
        again = json.loads((self.runner / "results/self-closure/closure.json").read_text())
        self.assertEqual(again["organization_receipt_sha256"], closure["organization_receipt_sha256"])
        self.assertEqual(self.git("rev-parse", REF), tip)


if __name__ == "__main__":
    unittest.main()
