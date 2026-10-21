#!/usr/bin/env bash
# Install / uninstall the socks-tun systemd service.
#   ./install.sh [install|uninstall]
set -euo pipefail
[[ $EUID -eq 0 ]] || exec sudo "$0" "$@"

here=$(cd "$(dirname "$0")" && pwd)
lib=/usr/local/lib/socks-tun

case "${1:-install}" in
install)
    for bin in ip nft python3; do
        command -v "$bin" >/dev/null || { echo "missing: $bin" >&2; exit 1; }
    done
    install -Dm755 "$here/socks-tun"   "$lib/socks-tun"
    install -Dm755 "$here/socks-relay" "$lib/socks-relay"
    install -Dm644 "$here/socks-tun.service" /etc/systemd/system/socks-tun.service
    if [[ -e /etc/socks-tun.conf ]]; then
        echo "keeping existing /etc/socks-tun.conf"
        # Add knobs introduced since it was installed, with their defaults.
        while IFS= read -r line; do
            key=${line%%=*}
            grep -q "^$key=" /etc/socks-tun.conf || { echo "$line" >> /etc/socks-tun.conf; echo "  added $line"; }
        done < <(grep -E '^[A-Z_]+=' "$here/socks-tun.conf")
    else
        install -Dm644 "$here/socks-tun.conf" /etc/socks-tun.conf
    fi

    # shellcheck disable=SC1091
    . /etc/socks-tun.conf
    if [[ "${PROXY_TYPE:-}" == tor ]]; then
        # Tor mode resolves through Tor's DNSPort; make sure torrc has it.
        torrc=/etc/tor/torrc
        if ! grep -qE "^\s*DNSPort\s+${TOR_DNS_PORT}(\s|$)" "$torrc"; then
            cp -a "$torrc" "$torrc.bak.$(date +%Y%m%d-%H%M%S)"
            printf '\n# added by socks-tun install.sh\nDNSPort %s\n' "$TOR_DNS_PORT" >> "$torrc"
            tor -f "$torrc" --verify-config >/dev/null
            systemctl reload-or-restart tor.service
            echo "enabled DNSPort $TOR_DNS_PORT in $torrc"
        fi
    fi

    systemctl daemon-reload
    systemctl enable socks-tun.service
    systemctl restart socks-tun.service
    systemctl --no-pager --lines=5 status socks-tun.service
    ;;
uninstall)
    systemctl disable --now socks-tun.service 2>/dev/null || true
    rm -f /etc/systemd/system/socks-tun.service
    rm -rf "$lib"
    systemctl daemon-reload
    echo "removed; config left at /etc/socks-tun.conf"
    ;;
*)
    echo "usage: $0 [install|uninstall]" >&2; exit 2 ;;
esac
