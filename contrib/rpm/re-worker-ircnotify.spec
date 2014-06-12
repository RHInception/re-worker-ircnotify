%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global _pkg_name replugin
%global _src_name reworkerircnotify

Name: re-worker-ircnotify
Summary: RE IRC notification worker
Version: 0.0.1
Release: 2%{?dist}

Group: Applications/System
License: AGPLv3
Source0: %{_src_name}-%{version}.tar.gz
Url: https://github.com/rhinception/re-worker-ircnotify

BuildArch: noarch
BuildRequires: python2-devel
BuildRequires: python-setuptools
Requires: re-worker
Requires: python-irc
Requires: python-setuptools

%description
This notification worker handles pushing notifications out through IRC.

%prep
%setup -q -n %{_src_name}-%{version}

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install -O1 --root=$RPM_BUILD_ROOT --record=re-worker-ircnotify-files.txt

%files -f re-worker-ircnotify-files.txt
%doc README.md LICENSE AUTHORS
%dir %{python2_sitelib}/%{_pkg_name}

%changelog
* Thu Jun 12 2014 Steve Milner <stevem@gnulinux.et> - 0.0.1-3
- python-setuptools is required.

* Mon Jun  9 2014 Chris Murphy <chmurphy@redhat.com> - 0.0.1-2
- Fix of rpm dependencies

* Thu Jun  5 2014 Steve Milner <stevem@gnulinux.et> - 0.0.1-1
- First release
