Summary: Dummy package to fix systemd initscripts configs
Name: vzdummy-systemd-el8
Group: Applications/System
Vendor: Virtuozzo
License: GPL
Version: 1.0
Release: 4%{?dist}
Autoreq: 0
BuildArch: noarch

%description
Dummy package to fix systemd initscripts configs
for running inside Virtuozzo containers

%setup

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/lib/systemd/system
mkdir -p $RPM_BUILD_ROOT/etc/systemd/system/default.target.wants
mkdir -p $RPM_BUILD_ROOT/lib/systemd/system/reboot.target.wants

cat >> $RPM_BUILD_ROOT/usr/lib/systemd/system/vzfifo.service << EOL
#  This file is part of systemd.
#
#  systemd is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.

[Unit]
Description=Tell that Container is started
ConditionPathExists=/proc/vz
ConditionPathExists=!/proc/bc
Requires=quotaon.service systemd-quotacheck.service
After=multi-user.target quotaon.service systemd-quotacheck.service firewalld.service

[Service]
Type=forking
ExecStartPre=-/usr/bin/firewall-cmd --state
ExecStart=/bin/touch /.vzfifo
TimeoutSec=0
RemainAfterExit=no
EOL

ln -s /usr/lib/systemd/system/vzfifo.service \
	$RPM_BUILD_ROOT/etc/systemd/system/default.target.wants/vzfifo.service

cat >> $RPM_BUILD_ROOT/usr/lib/systemd/system/vzreboot.service << EOL
#  This file is part of systemd.
#
#  systemd is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.

[Unit]
Description=Tell that Container is rebooted
ConditionPathExists=/proc/vz
ConditionPathExists=!/proc/bc
Before=systemd-reboot.service
DefaultDependencies=no

[Service]
Type=forking
ExecStart=/bin/touch /reboot
TimeoutSec=0
RemainAfterExit=no
EOL

ln -s /usr/lib/systemd/system/vzreboot.service \
	$RPM_BUILD_ROOT/lib/systemd/system/reboot.target.wants/vzreboot.service

%triggerin -- elfutils-default-yama-scope
# mask unsuported sysctl variables
YAMA_FILE="/usr/lib/sysctl.d/10-default-yama-scope.conf"
if [ -f $YAMA_FILE ]; then
sed -i -e "s/kernel.yama.ptrace_scope.*/# kernel.yama.ptrace_scope = 0/g" \
        $YAMA_FILE
fi
:

%triggerin -- systemd
# mask unsuported sysctl variables
SYSTEMD_FILE="/usr/lib/sysctl.d/50-default.conf"
if [ -f $SYSTEMD_FILE ]; then
sed -i -e "s/fs.protected_hardlinks = 1/# fs.protected_hardlinks = 1/g" \
	-e "s/fs.protected_symlinks = 1/# fs.protected_symlinks = 1/g" \
	-e "s,^net.ipv4\.,# net.ipv4.,g" \
	-e "s,^net.core.default_qdisc,# net.core.default_qdisc,g" \
	-e "s,^kernel\.,# kernel.,g" \
	$SYSTEMD_FILE
fi
:

%triggerin -- firewalld
# change firewalld backend to iptables
FIREWALLD_FILE="/etc/firewalld/firewalld.conf"
if [ -f $FIREWALLD_FILE ]; then
	sed -i -e "s/^IndividualCalls=.*/IndividualCalls=yes/g" \
		-e "s/^IPv6_rpfilter=.*/IPv6_rpfilter=no/g" $FIREWALLD_FILE
fi
:

%triggerin -- systemd-udev
# ignore quotaon failures, systemd bug
SYSTEMD_FILE="/lib/systemd/system/quotaon.service"
if [ -f $SYSTEMD_FILE ]; then
	sed -i -e "s,^ExecStart=/,ExecStart=-/,g" $SYSTEMD_FILE
fi
:

%files
%attr(0644, root, root) /usr/lib/systemd/system/vzfifo.service
%attr(0644, root, root) /usr/lib/systemd/system/vzreboot.service
/etc/systemd/system/default.target.wants/vzfifo.service
/lib/systemd/system/reboot.target.wants/vzreboot.service

%changelog
* Wed Sep 25 2019 Konstantin Volckov <wolf@sw.ru> 1.0-1
- created
