"""Build and deploy the all-in-one leaderboard image through Portainer's Docker API.

Run from the repo root. Standard library only. See docs/PORTAINER_DEPLOY.md.

    python deploy/portainer.py build  <tag> [--build-arg KEY=VALUE ...]
    python deploy/portainer.py deploy <tag> [--name leaderboard] [--port 3001] [--env-file FILE]
    python deploy/portainer.py probe  [--name leaderboard] [question ...]
    python deploy/portainer.py logs   [--name leaderboard] [--tail 80]

Configuration (environment variables):
    PORTAINER_URL       e.g. https://portainer.example.org:9443
    PORTAINER_NODE      Swarm node that runs the containers
    PORTAINER_ENDPOINT  Portainer environment id (default 2)
    PORTAINER_TOKEN     API key; falls back to the file ~/.portainer_token
    PORTAINER_INSECURE  1 = skip TLS verification (internal certificate)
"""
import argparse
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ENV_CARRIED_OVER = ("OPENAI_API_KEY", "LETZEVAL_", "GUARDRAIL_")


def _config():
    try:
        url = os.environ["PORTAINER_URL"].rstrip("/")
        node = os.environ["PORTAINER_NODE"]
    except KeyError as missing:
        sys.exit(f"Set {missing} (see the header of this file).")
    token = os.environ.get("PORTAINER_TOKEN")
    if not token:
        with open(os.path.expanduser("~/.portainer_token")) as f:
            token = f.read().strip()
    ctx = ssl.create_default_context()
    if os.environ.get("PORTAINER_INSECURE") == "1":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    base = f"{url}/api/endpoints/{os.environ.get('PORTAINER_ENDPOINT', '2')}/docker"
    return base, node, token, ctx


def call(method, path, body=None, ctype="application/json", timeout=120, on_line=None):
    """One Docker API call, pinned to the node. Returns (status, text)."""
    base, node, token, ctx = _config()
    headers = {"X-API-Key": token, "X-PortainerAgent-Target": node}
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        headers["Content-Type"] = ctype
    req = urllib.request.Request(base + path, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
            if on_line:
                for line in r:
                    on_line(line)
                return r.status, ""
            return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")[:2000]


def _printable(text):
    return "".join(ch for ch in text if ch.isprintable() or ch == "\n")


def build(args):
    tar = subprocess.run(["git", "archive", "--format=tar", "HEAD"], check=True, capture_output=True).stdout
    query = {"t": args.tag, "dockerfile": "deploy/Dockerfile", "rm": "1"}
    if args.build_arg:
        query["buildargs"] = json.dumps(dict(a.split("=", 1) for a in args.build_arg))
    failed = []

    def show(line):
        try:
            msg = json.loads(line)
        except ValueError:
            return
        if "error" in msg:
            failed.append(msg["error"])
        sys.stdout.write(msg.get("stream", ""))
        sys.stdout.flush()

    code, text = call("POST", "/build?" + urllib.parse.urlencode(query), tar,
                      ctype="application/x-tar", timeout=3600, on_line=show)
    if code != 200 or failed:
        sys.exit(f"Build failed (HTTP {code}): {text or failed[0]}")


def deploy(args):
    name, prev = args.name, args.name + "-prev"
    env = {}
    code, text = call("GET", f"/containers/{name}/json")
    if code == 200:
        for item in json.loads(text)["Config"]["Env"]:
            key, _, value = item.partition("=")
            if key.startswith(ENV_CARRIED_OVER):
                env[key] = value
    if args.env_file:
        with open(args.env_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip()

    if code == 200:
        call("POST", f"/containers/{name}/stop?t=5")
        call("DELETE", f"/containers/{prev}?force=true")
        call("POST", f"/containers/{name}/rename?name={prev}")
        call("POST", f"/containers/{prev}/update", {"RestartPolicy": {"Name": "no"}})
        print(f"Previous container kept, stopped, as {prev}")

    host_config = {"RestartPolicy": {"Name": "always", "MaximumRetryCount": 0}}
    if args.port:
        host_config["PortBindings"] = {"3000/tcp": [{"HostIp": "127.0.0.1", "HostPort": str(args.port)}]}
    spec = {"Image": args.tag, "Env": [f"{k}={v}" for k, v in env.items()],
            "ExposedPorts": {"3000/tcp": {}}, "HostConfig": host_config}
    code, text = call("POST", f"/containers/create?name={name}", spec)
    if code != 201:
        sys.exit(f"Create failed (HTTP {code}): {text}")
    code, text = call("POST", f"/containers/{name}/start")
    if code not in (204, 304):
        sys.exit(f"Start failed (HTTP {code}): {text}")
    print(f"{name} started from {args.tag} with env keys: {sorted(env) or 'none (no LLM)'}")
    print("The agent trains for about 3 minutes before the chat answers.")


def probe(args):
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "probe_inside.py"), encoding="utf-8") as f:
        script = f.read()
    cmd = ["/opt/agent/bin/python", "-c", script, *args.questions]
    code, text = call("POST", f"/containers/{args.name}/exec",
                      {"AttachStdout": True, "AttachStderr": True, "Tty": True, "Cmd": cmd})
    if code != 201:
        sys.exit(f"Exec failed (HTTP {code}): {text}")
    exec_id = json.loads(text)["Id"]
    _, out = call("POST", f"/exec/{exec_id}/start", {"Detach": False, "Tty": True}, timeout=300)
    print(_printable(out))


def logs(args):
    code, text = call("GET", f"/containers/{args.name}/logs?stdout=1&stderr=1&tail={args.tail}")
    print(_printable(text) if code == 200 else f"HTTP {code}: {text}")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("build", help="build the image on the node from git HEAD")
    p.add_argument("tag")
    p.add_argument("--build-arg", action="append", metavar="KEY=VALUE")
    p.set_defaults(run=build)

    p = sub.add_parser("deploy", help="replace the running container, keep the old one as <name>-prev")
    p.add_argument("tag")
    p.add_argument("--name", default="leaderboard")
    p.add_argument("--port", type=int, default=3001, help="host port on 127.0.0.1 (0 = none)")
    p.add_argument("--env-file", help="KEY=VALUE lines; overrides the values carried over")
    p.set_defaults(run=deploy)

    p = sub.add_parser("probe", help="check the site, the API and the agent from inside the container")
    p.add_argument("--name", default="leaderboard")
    p.add_argument("questions", nargs="*")
    p.set_defaults(run=probe)

    p = sub.add_parser("logs", help="print the container's last log lines")
    p.add_argument("--name", default="leaderboard")
    p.add_argument("--tail", type=int, default=80)
    p.set_defaults(run=logs)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
