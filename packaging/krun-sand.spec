Name:           krun-sand
Version:        0.1.0
Release:        1%{?dist}
Summary:        Run commands in a libkrun microVM with NIC-pinned networking
License:        MIT-0
URL:            https://github.com/wildcommitter/krun-sand
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
# libkrun only exists where KVM guests are supported.
ExclusiveArch:  x86_64 aarch64 noarch

BuildRequires:  python3-devel >= 3.12

Requires:       python3 >= 3.12
Requires:       iproute
Requires:       passt
# Full subuid/subgid mapping for the sandbox's user namespace.
Requires:       /usr/bin/newuidmap
Requires:       /usr/bin/newgidmap
# dlopen'ed via ctypes, so not picked up automatically. Both arches are 64-bit.
Requires:       libkrun.so.1()(64bit)
Suggests:       socks-tun

%description
Runs a preset command, with extra arguments appended xargs-style, inside a
libkrun microVM. Images are pulled straight from OCI registries; pasta
provides the network namespace with all egress bound to one interface and
forwarded ports listening only on one interface.

%prep
%autosetup -n %{name}-%{version}

%build
%py3_shebang_fix krun-sand

%install
install -Dpm 0755 krun-sand %{buildroot}%{_bindir}/krun-sand

%check
%{python3} -m py_compile krun-sand
./krun-sand -c krun-sand.toml -l

%files
%license LICENSE
%doc README.md krun-sand.toml
%{_bindir}/krun-sand

%changelog
* Wed Oct 21 2026 The krun-sand Authors - 0.1.0-1
- Initial package
