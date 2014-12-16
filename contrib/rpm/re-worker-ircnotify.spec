%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global _pkg_name replugin
%global _src_name reworkerircnotify

Name: re-worker-ircnotify
Summary: RE IRC notification worker
Version: 0.0.5
Release: 1%{?dist}

Group: Applications/System
License: AGPLv3
Source0: %{_src_name}-%{version}.tar.gz
Url: https://github.com/rhinception/re-worker-ircnotify

BuildArch: noarch
BuildRequires: python2-devel
BuildRequires: python-setuptools
Requires: re-worker >= 0.0.7
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
%defattr(-, root, root)
%doc README.md LICENSE AUTHORS
%dir %{python2_sitelib}/%{_pkg_name}
%exclude %{python2_sitelib}/%{_pkg_name}/__init__.py*

%changelog
* Tue Dec 16 2014 Steve Milner <stevem@gnulinux.net> - 0.0.5-1
- Now accepts step message format as well.

* Tue Dec  2 2014 Steve Milner <stevem@gnulinux.net> - 0.0.4-1
- Connections no longer clobber eachother.

* Mon Nov 17 2014 Steve Milner <stevem@gnulinux.net> - 0.0.3-1
- Updates to use irc 11.x.

* Wed Oct 29 2014 Ryan Cook <rcook@redhat.com> - 0.0.2-2
- Specified version of irc

* Fri Aug  1 2014 Steve Milner <stevem@gnulinux.net> - 0.0.2-1
- Now using multiprocessing.

* Tue Jun 24 2014 Steve Milner <stevem@gnulinux.net> - 0.0.1-9
- _irc_client should be _irc_transport when joining channels.

* Tue Jun 24 2014 Steve Milner <stevem@gnulinux.net> - 0.0.1-8
- Now waiting till IRC is connected to use IRC connection

* Fri Jun 20 2014 Steve Milner <stevem@gnulinux.net> - 0.0.1-7
- Bug fixes.

* Fri Jun 20 2014 Steve Milner <stevem@gnulinux.net> - 0.0.1-6
- Bug fixes.

* Wed Jun 18 2014 Steve Milner <stevem@gnulinux.net> - 0.0.1-5
- Defattr not being used in files section.

* Tue Jun 17 2014 Ryan Cook <rcook@redhat.com> - 0.0.1-4
- Added exclude __init__.py*

* Thu Jun 12 2014 Steve Milner <stevem@gnulinux.et> - 0.0.1-3
- python-setuptools is required.

* Mon Jun  9 2014 Chris Murphy <chmurphy@redhat.com> - 0.0.1-2
- Fix of rpm dependencies

* Thu Jun  5 2014 Steve Milner <stevem@gnulinux.et> - 0.0.1-1
- First release
