%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name: ibm
Version: PLEASE_LEAVE_BLANK
Release: 1%{?dist}
Summary: Inteface Burst Monitor
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

%files
%defattr(-,root,eosadmin,-)
%{python_sitelib}/ibm_lib.py*
%{python_sitelib}/ibm-%{version}-py2.7.egg-info
%config(noreplace) /persist/sys/ibm/ibm.json
%config /persist/sys/ibm/ibm


%changelog
* Tue Oct 23 2014 Andrei Dvornic <andrei@arista.com> - %{version}-1
- Initial release
