Name:           socks-tun
Version:        0.1.0
Release:        1%{?dist}
Summary:        TUN device whose traffic is relayed through a SOCKS5 proxy
License:        MIT-0
URL:            https://github.com/wildcommitter/krun-sand
Source0:        %{url}/archive/v%{version}/krun-sand-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  systemd-rpm-macros

Requires:       bash
Requires:       iproute
Requires:       nftables
Requires:       python3
Requires:       procps-ng
%{?systemd_requires}
Recommends:     tor

%description
Brings up a TUN device (socks0) that nothing reads from. nftables hands TCP
bound to it to a relay that re-dials it through a SOCKS5 proxy (Tor by
default), DNS goes to Tor's DNSPort or as DNS-over-TCP through the proxy, and
all other traffic is dropped.

With PROXY_TYPE=tor, tor must have a DNSPort matching TOR_DNS_PORT in
/etc/socks-tun.conf, e.g. "DNSPort 127.0.0.1:9053" in /etc/tor/torrc.

%prep
%autosetup -n krun-sand-%{version}
sed -i 's|/usr/local/lib/socks-tun|%{_libexecdir}/socks-tun|g' socks-tun/socks-tun.service

%build
%py3_shebang_fix socks-tun/socks-relay

%install
install -Dpm 0755 socks-tun/socks-tun   %{buildroot}%{_libexecdir}/socks-tun/socks-tun
install -Dpm 0755 socks-tun/socks-relay %{buildroot}%{_libexecdir}/socks-tun/socks-relay
install -Dpm 0644 socks-tun/socks-tun.service %{buildroot}%{_unitdir}/socks-tun.service
install -Dpm 0644 socks-tun/socks-tun.conf    %{buildroot}%{_sysconfdir}/socks-tun.conf

%check
bash -n socks-tun/socks-tun
%{python3} -m py_compile socks-tun/socks-relay
grep -q '^ExecStart=%{_libexecdir}/socks-tun/socks-relay$' socks-tun/socks-tun.service

%post
%systemd_post socks-tun.service

%preun
%systemd_preun socks-tun.service

%postun
%systemd_postun_with_restart socks-tun.service

%files
%license LICENSE
%doc README.md
%dir %{_libexecdir}/socks-tun
%{_libexecdir}/socks-tun/socks-tun
%{_libexecdir}/socks-tun/socks-relay
%{_unitdir}/socks-tun.service
%config(noreplace) %{_sysconfdir}/socks-tun.conf

%changelog
* Wed Oct 21 2026 The krun-sand Authors - 0.1.0-1
- Initial package
