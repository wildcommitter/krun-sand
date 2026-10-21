# krun-sand

```
krun-sand [-c CONFIG] [-p PRESET] [-e IFACE] [-i IFACE] [-x [-0]] [-n] [-l] [--pull] [--] [ARGS...]
```

Runs the active preset's `command` with `ARGS` appended (xargs-style) in a libkrun microVM, with network pinned to one NIC.

Requires `pasta` (passt), `libkrun`, `/dev/kvm` access, and Python ≥ 3.12.

## Examples

```sh
krun-sand 'uname -a; cat /etc/os-release'        # default preset: sh -c
krun-sand 'exec sh -i'                           # interactive shell
krun-sand -p web                                 # serve $PWD read-only on <ingress-ip>:18080
krun-sand -p tor 'wget -qO- https://check.torproject.org/api/ip'
krun-sand -e wlan0 'wget -qO- ifconfig.me'       # different egress NIC, just this run

printf '%s\n' a 'b c' | krun-sand -p echo -x     # args from stdin (shell-quoted)
find . -name '*.py' -print0 | krun-sand -p lint -x -0

krun-sand -n -p web                              # print pasta cmd + VM plan, don't run
krun-sand -l                                     # list presets (* = active)
krun-sand --pull 'apk --version'                 # re-resolve the image tag first
```

The VM's exit code is `krun-sand`'s exit code.

## Flags

| flag | |
|---|---|
| `-c FILE` | config (default: `$KRUN_SAND_CONFIG`, `./krun-sand.toml`, `~/.config/krun-sand/config.toml`) |
| `-p NAME` | preset to run (overrides `preset =`) |
| `-e IFACE` / `-i IFACE` | override egress / ingress NIC |
| `-x` | append args read from stdin (VM gets no stdin) |
| `-0` | with `-x`, stdin args are NUL-separated |
| `-n` | dry run |
| `-l` | list presets |
| `--pull` | refresh the image even if cached |

## Config

```toml
preset = "shell"                 # active preset

[network]                        # defaults; a preset's `network = {...}` overrides keys
egress  = "enp6s0f0"             # all outbound sockets bound here; run fails if it's down
ingress = "enp6s0f0"             # forwarded ports listen only here (default: egress)
ipv6 = false
host_loopback = false            # true: guest can reach host services via the gateway IP
tcp = ["18080:8080"]             # "hostport:guestport" or "port"
udp = []
dns = ["1.1.1.1"]                # default: host's upstream resolvers (loopback stubs skipped)
addr_from = "enp6s0f0"           # NIC whose addr/routes the netns copies (default: egress)

[presets.web]
image = "docker.io/library/python:3.12-slim"   # any registry; bare names = Docker Hub
command = ["python3", "-m", "http.server", "8080"]  # list or string; empty = image entrypoint
cpus = 1                         # default 2
memory_mib = 512                 # default 2048
workdir = "/srv"                 # default: image WorkingDir, else /
mounts = ["$PWD:/srv:ro"]        # "src:dst[:ro]"; ~ and $VARS expanded
env = { DEBUG = "1" }            # merged over the image's Env; $VARS expanded
read_only = false                # true: root fs read-only (mounts keep their own mode)
network = { tcp = ["18080:8080"] }
```

Use cases as presets:

```toml
# Edit a project, nothing else writable, no network except the LAN NIC
[presets.dev]
image = "docker.io/library/alpine:latest"
command = ["sh", "-c"]
mounts = ["$PWD:/work"]
workdir = "/work"
read_only = true

# Lint files passed via -x, project mounted read-only
[presets.lint]
image = "docker.io/library/python:3.12-slim"
command = ["sh", "-c", "pip -q install ruff && ruff check \"$@\"", "ruff"]
mounts = ["$PWD:/src:ro"]
workdir = "/src"
```

## Behaviour

- **Filesystem:** writes go to a tmpfs overlay and are discarded when the run ends. Mounts are host bind mounts and changes to them persist.
- **Network:** host loopback services are not reachable, and only the listed `tcp`/`udp` ports are forwarded, on the ingress NIC only. DNS also goes out the egress NIC.
- **Guest user:** the guest runs as root. The preset `user` key is rejected.
- **Image cache:** `~/.cache/krun-sand/images/<digest>/`. Delete it to reclaim space.
- **Run state:** `$XDG_RUNTIME_DIR/krun-sand/`. It's removed when the run exits. If `krun-sand` is killed, the VM dies with it.

## socks-tun (Tor / SOCKS5 egress)

Creates the `socks0` device. Traffic bound to it goes through the proxy: TCP via SOCKS5 CONNECT, DNS via Tor's DNSPort or DNS-over-TCP through the proxy, and everything else is dropped.

```sh
socks-tun/install.sh            # installs + starts socks-tun.service (sudo)
socks-tun/install.sh uninstall
sudo /usr/local/lib/socks-tun/socks-tun status
```

Edit `/etc/socks-tun.conf` and restart the service to change settings:

```sh
SOCKS_URL=socks5://user:pass@host:1080   # default: socks5://127.0.0.1:9050 (Tor)
PROXY_TYPE=socks5                        # tor | socks5 (DNS goes to DNS_UPSTREAM)
DNS_UPSTREAM=1.1.1.1:53
```

Then use `egress = "socks0"` with `addr_from = "<LAN NIC>"`, as in the `tor` preset. To test without a VM: `curl --interface socks0 https://check.torproject.org/api/ip`.
