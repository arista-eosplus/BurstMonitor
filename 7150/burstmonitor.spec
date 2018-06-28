%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name: burstmonitor
Version: PLEASE_LEAVE_BLANK
Release: 1%{?dist}
Summary: Interface Burst Monitor
License: BSD-3

Group: Development/Libraries
URL: http://eos.arista.com
Source0: %{name}-%{version}.tar.gz

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
Monitor bursts of traffic on the the configured interfaces.

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%triggerin -- Cli
# When the Cli package is available, install the daemon config command
FastCli -p 15 -c "configure
daemon %{name}
exec /usr/bin/python /persist/sys/burstmonitor/burstmonitor
no shutdown
end"

%triggerun -- Cli
# $1 stores the number of versions of this RPM that will be installed after
#   this uninstall completes.
# $2 stores the number of versions of the target RPM that will be installed
#   after this uninstall completes.
if [ $1 -eq 0 -a $2 -gt 0 ] ; then
  FastCli -p 15 -c "configure
  daemon %{name}
  shutdown
  no daemon %{name}
  end"
fi

%files
%defattr(-,root,eosadmin,-)
%{python_sitelib}/burstmonitor_lib.py*
%{python_sitelib}/burstmonitor-%{version}-py2.7.egg-info
%config(noreplace) /persist/sys/burstmonitor/burstmonitor.json
%config /persist/sys/burstmonitor/burstmonitor

%pre
# pre install of new package
# Not executed during an uninstallation
# $1 == 1 - install
# $1 >= 2 - upgrade
exit 0

%post
# post install of new package.
# Not executed during an uninstallation
# $1 == 1 - install
# $1 >= 2 - upgrade
exit 0

%preun
# preun of old package
# $1 == 0 - uninstall
# $1 == 1 - upgrade
exit 0

%postun
# postun of old package
# $1 == 0 - uninstall
# $1 == 1 - upgrade
if [ $1 -eq 0 ]; then
    rm -rf /persist/sys/burstmonitor
fi
pkill burstmonitor
exit 0

%changelog
* Thu Jun 27 2018 Cheyne Womble <cwomble@arista.com> - %{version}-1
- Don't force remove burstmonitor and configs during upgrade.
* Tue Dec 15 2015 Philip DiLeo <phil@arista.com> - %{version}-1
- Change name of package to burstmonitor.
* Tue Oct 23 2014 Andrei Dvornic <andrei@arista.com> - %{version}-1
- Initial release
