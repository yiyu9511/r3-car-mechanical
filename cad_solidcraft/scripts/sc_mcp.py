"""Minimal MCP stdio client for solidcraft-cli.

Usage:
  python sc_mcp.py <requests.json> [--connect HOST:PORT] [--wait SEC]

requests.json: JSON array of JSON-RPC objects (initialize added automatically).
Prints each response line as it arrives.
"""
import json
import subprocess
import sys
import threading
import queue

CLI = r"E:\tools\SolidCraft-0.30.1\solidcraft-cli.exe"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    connect = None
    wait = 180
    req_file = args[0]
    rest = args[1:]
    if "--connect" in rest:
        i = rest.index("--connect")
        connect = rest[i + 1]
        del rest[i:i + 2]
    if "--wait" in rest:
        i = rest.index("--wait")
        wait = float(rest[i + 1])

    with open(req_file, encoding="utf-8-sig") as fh:
        reqs = json.load(fh)

    cmd = [CLI, "mcp", "--allow-path", r"E:\car_projects\cad_solidcraft",
           "--allow-path", r"E:\car_projects\freecad"]
    if connect:
        cmd += ["--connect", connect]
    cmd += rest

    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, encoding="utf-8",
                         bufsize=1)

    q = queue.Queue()

    def reader():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def err_reader():
        for line in p.stderr:
            print("[stderr]", line.rstrip(), file=sys.stderr)

    threading.Thread(target=err_reader, daemon=True).start()

    def send(obj):
        data = json.dumps(obj, ensure_ascii=False)
        p.stdin.write(data + "\n")
        p.stdin.flush()

    send({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "dsh-agent", "version": "1.0"}}})

    got_init = None
    import time
    t0 = time.time()
    while got_init is None and time.time() - t0 < 30:
        try:
            line = q.get(timeout=1)
        except queue.Empty:
            continue
        if line is None:
            break
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if obj.get("id") == 0:
            got_init = obj
    if got_init is None:
        print("NO INIT RESPONSE", file=sys.stderr)
        sys.exit(2)
    print("== initialize OK, server:", got_init["result"]["serverInfo"])
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    ids = set()
    for i, r in enumerate(reqs, start=1):
        r = dict(r)
        if r.get("method", "").startswith("notifications/"):
            pass
        else:
            r["id"] = i
            ids.add(i)
        send(r)

    t0 = time.time()
    done = 0
    while done < len(ids) and time.time() - t0 < wait:
        try:
            line = q.get(timeout=1)
        except queue.Empty:
            continue
        if line is None:
            break
        try:
            obj = json.loads(line)
        except ValueError:
            print("[unparsed]", line[:300])
            continue
        if obj.get("id") in ids:
            done += 1
            print(json.dumps(obj, ensure_ascii=False))
        if "method" in obj and "id" in obj and "result" not in obj:
            # server -> client request: answer with empty success
            send({"jsonrpc": "2.0", "id": obj["id"], "result": {}})
            continue
        elif "method" in obj and obj.get("method", "").startswith("notifications/"):
            pass  # server notifications ignored
        else:
            print("[note]", line[:500])
    p.kill()


if __name__ == "__main__":
    main()
