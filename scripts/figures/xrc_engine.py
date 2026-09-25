"""A small client for the command-line server that ships with X-Ray Calc.

XRC_MCP.exe in the build folder speaks JSON-RPC over stdin and stdout. The
chapter scripts that only calculate curves send one batch of requests
(ch4_engine_data.py to ch8_engine_data.py). A fit is a job: the server returns
a job id at once, and a second request waits for the result. This module keeps
one server process open for that exchange. The book never names the server.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

import local_paths

# Point XRC_MCP_EXE at a copy of the release, not at a build folder that
# changes (and gets locked) under a running job.
EXE = local_paths.get("XRC_MCP_EXE")


class Engine:
    def __init__(self):
        self.work = Path(tempfile.mkdtemp(prefix="xrc_engine_"))
        self.proc = subprocess.Popen([str(EXE), "--workdir", str(self.work)],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     text=True, encoding="utf-8", bufsize=1)
        self.next_id = 0
        self._send("initialize", {})

    def _send(self, method, params):
        self.next_id += 1
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.next_id,
                                          "method": method, "params": params}) + "\n")
        self.proc.stdin.flush()
        while True:
            msg = json.loads(self.proc.stdout.readline())
            if msg.get("id") == self.next_id:
                return msg

    def call(self, name, args):
        msg = self._send("tools/call", {"name": name, "arguments": args})
        res = msg["result"]
        text = res["content"][0]["text"]
        if res.get("isError"):
            raise RuntimeError(f"{name}: {text}")
        return json.loads(text)

    def fit(self, request):
        """Run one fit job to the end and return its result."""
        job = self.call("fit_xrr", request)["job_id"]
        while True:
            r = self.call("job_wait", {"job_id": job, "wait_s": 600})
            if r.get("state") in ("finished", "failed", "cancelled"):
                break
        if r.get("state") != "finished":
            raise RuntimeError(f"fit job {job}: {r}")
        return self.call("job_result", {"job_id": job})

    def describe(self):
        return self.call("describe_server", {})["server"]

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=60)
