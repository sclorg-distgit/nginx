%{?scl:%scl_package nginx}

%if 0%{?rhel} > 6
%define use_systemd 1
%else
%define use_systemd 0
%endif

%define use_geoip 0
%define use_perl 0
%global with_gperftools     0
%global with_passenger 1
%global passenger_version 4.0.50

%global  _hardened_build     1
%global  nginx_user          nginx
%global  nginx_group         %{nginx_user}
%global  nginx_home          %{_localstatedir}/lib/nginx
%global  nginx_home_tmp      %{nginx_home}/tmp
%global  nginx_confdir       %{_sysconfdir}/nginx
%global  nginx_datadir       %{_datadir}/nginx
%global  nginx_logdir        %{_root_localstatedir}/log/nginx16
%global  nginx_webroot       %{nginx_datadir}/html

%global service_name %{?scl_prefix}nginx

Name:              %{?scl:%scl_prefix}nginx
Epoch:             1
Version:           1.6.2
Release:           3%{?dist}

Summary:           A high performance web server and reverse proxy server
Group:             System Environment/Daemons
# BSD License (two clause)
# http://www.freebsd.org/copyright/freebsd-license.html
License:           BSD
URL:               http://nginx.org/

Source0:           http://nginx.org/download/nginx-%{version}.tar.gz
Source1:           http://s3.amazonaws.com/phusion-passenger/releases/passenger-%{passenger_version}.tar.gz
Source10:          nginx.service
Source11:          nginx.logrotate
Source12:          nginx.conf
Source13:          action-upgrade.sh
Source15:          nginx.init
Source16:          nginx.sysconfig
Source100:         index.html
Source101:         poweredby.png
Source102:         nginx-logo.png
Source103:         404.html
Source104:         50x.html

# removes -Werror in upstream build scripts.  -Werror conflicts with
# -D_FORTIFY_SOURCE=2 causing warnings to turn into errors.
Patch0:            nginx-auto-cc-gcc.patch
# Build Passenger against Fedora's (renamed) libeio
Patch200:          passenger-4.0.38-libeio.patch

%if 0%{?with_passenger}
BuildRequires: %{?scl:rh-passenger40-}libeio-devel
BuildRequires: %{?scl:rh-passenger40-}libev-devel >= 4.0.0
BuildRequires: %{?scl:rh-passenger40-}rubygem(mizuho)
BuildRequires: %{?scl:ruby193-}ruby
BuildRequires: %{?scl:ruby193-}ruby-devel
BuildRequires: %{?scl:ruby193-}rubygems
BuildRequires: %{?scl:ruby193-}rubygems-devel
BuildRequires: %{?scl:ruby193-}rubygem(rake) >= 0.8.1
BuildRequires: %{?scl:ruby193-}rubygem(rack)
BuildRequires: %{?scl:ruby193-}rubygem(rspec)
BuildRequires: %{?scl:ruby193-}rubygem(mime-types)
BuildRequires: libcurl-devel
BuildRequires: zlib-devel
BuildRequires: pcre-devel
BuildRequires: openssl-devel
%endif

# BuildRequires:     GeoIP-devel
BuildRequires:     gd-devel
%if 0%{?with_gperftools}
BuildRequires:     gperftools-devel
%endif
BuildRequires:     libxslt-devel
BuildRequires:     openssl-devel
BuildRequires:     pcre-devel
BuildRequires:     perl-devel
BuildRequires:     perl(ExtUtils::Embed)
BuildRequires:     zlib-devel
%if 0%{?use_geoip}
Requires:          GeoIP
%endif
Requires:          gd
Requires:          openssl
Requires:          pcre
%if 0%{?use_perl}
Requires:          perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
%endif
Requires(pre):     shadow-utils
Provides:          webserver

%if %{use_systemd}
BuildRequires:     systemd
Requires(post):    systemd
Requires(preun):   systemd
Requires(postun):  systemd
%else
Requires(post):    chkconfig
Requires(preun):   chkconfig, initscripts
Requires(postun):  initscripts
%endif
Requires(post): policycoreutils-python libselinux-utils
%{?scl:Requires:%scl_runtime}

%description
Nginx is a web server and a reverse proxy server for HTTP, SMTP, POP3 and
IMAP protocols, with a strong focus on high concurrency, performance and low
memory usage.


%prep
%setup -q -n nginx-%{version}
%patch0 -p0

%if 0%{?with_passenger}
tar -xf %{SOURCE1}
pushd passenger-%{passenger_version}
%patch200 -p1 -b .uselibeio
popd
%endif

%build
%if 0%{?with_passenger}
%{?scl:scl enable ruby193 rh-passenger40 - << \EOF}
pushd passenger-%{passenger_version}
export USE_VENDORED_LIBEV=false
export USE_VENDORED_LIBEIO=false
CFLAGS="${CFLAGS:-%optflags}" ; export CFLAGS ;
CXXFLAGS="${CXXFLAGS:-%optflags}" ; export CXXFLAGS ;
FFLAGS="${FFLAGS:-%optflags}" ; export FFLAGS ;

export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8

rake nginx \
    NATIVE_PACKAGING_METHOD=rpm \
    EXTRA_CFLAGS="-fPIC" \
    EXTRA_CXXFLAGS="-fPIC" \
    FS_PREFIX=%{_prefix} \
    FS_BINDIR=%{_bindir} \
    FS_SBINDIR=%{_sbindir} \
    FS_DATADIR=%{_datadir} \
    FS_LIBDIR=%{_libdir} \
    FS_DOCDIR=%{_docdir} \
    RUBYLIBDIR=%{_datadir}/passenger/
    RUBYARCHDIR=%{_libdir}/passenger/
popd
%endif

# nginx does not utilize a standard configure script.  It has its own
# and the standard configure options cause the nginx configure script
# to error out.  This is is also the reason for the DESTDIR environment
# variable.
export DESTDIR=%{buildroot}
./configure \
    --prefix=%{nginx_datadir} \
    --sbin-path=%{_sbindir}/nginx \
    --conf-path=%{nginx_confdir}/nginx.conf \
    --error-log-path=%{nginx_logdir}/error.log \
    --http-log-path=%{nginx_logdir}/access.log \
    --http-client-body-temp-path=%{nginx_home_tmp}/client_body \
    --http-proxy-temp-path=%{nginx_home_tmp}/proxy \
    --http-fastcgi-temp-path=%{nginx_home_tmp}/fastcgi \
    --http-uwsgi-temp-path=%{nginx_home_tmp}/uwsgi \
    --http-scgi-temp-path=%{nginx_home_tmp}/scgi \
    --pid-path=%{_localstatedir}/run/nginx/nginx.pid \
    --lock-path=%{_localstatedir}/lock/subsys/nginx \
    --user=%{nginx_user} \
    --group=%{nginx_group} \
    --with-file-aio \
    --with-ipv6 \
    --with-http_ssl_module \
    --with-http_spdy_module \
    --with-http_realip_module \
    --with-http_addition_module \
    --with-http_xslt_module \
    --with-http_image_filter_module \
%if 0%{?use_geoip}
    --with-http_geoip_module \
%endif
    --with-http_sub_module \
    --with-http_dav_module \
    --with-http_flv_module \
    --with-http_mp4_module \
    --with-http_gunzip_module \
    --with-http_gzip_static_module \
    --with-http_random_index_module \
    --with-http_secure_link_module \
    --with-http_degradation_module \
    --with-http_stub_status_module \
%if 0%{?use_perl}
    --with-http_perl_module \
%endif
    --with-mail \
    --with-mail_ssl_module \
    --with-pcre \
%if 0%{?with_gperftools}
    --with-google_perftools_module \
%endif
%if 0%{?with_passenger}
    --add-module="./passenger-%{passenger_version}/ext/nginx" \
%endif
    --with-debug \
    --with-cc-opt="%{optflags} $(pcre-config --cflags)" \
    --with-ld-opt="$RPM_LD_FLAGS -Wl,-E" # so the perl module finds its symbols

make %{?_smp_mflags}

%if 0%{?with_passenger}
%{?scl:EOF}
%endif

%install
make install DESTDIR=%{buildroot} INSTALLDIRS=vendor

find %{buildroot} -type f -name .packlist -exec rm -f '{}' \;
find %{buildroot} -type f -name perllocal.pod -exec rm -f '{}' \;
find %{buildroot} -type f -empty -exec rm -f '{}' \;
find %{buildroot} -type f -iname '*.so' -exec chmod 0755 '{}' \;
%if %{use_systemd}
install -p -D -m 0644 %{SOURCE10} \
    %{buildroot}%{_unitdir}/%{?scl:%scl_prefix}nginx.service

sed -i 's|\$sbindir|%{_sbindir}|' \
    %{buildroot}%{_unitdir}/%{?scl:%scl_prefix}nginx.service
sed -i 's|\$localstatedir|%{_localstatedir}|' \
    %{buildroot}%{_unitdir}/%{?scl:%scl_prefix}nginx.service

# Install action scripts
mkdir -p $RPM_BUILD_ROOT%{_root_libexecdir}/initscripts/legacy-actions/%{?scl:%scl_prefix}nginx
for f in upgrade; do
	install -p -m 755 $RPM_SOURCE_DIR/action-${f}.sh \
			$RPM_BUILD_ROOT%{_root_libexecdir}/initscripts/legacy-actions/%{?scl:%scl_prefix}nginx/${f}
	sed -i 's|\$nginxservice|%{?scl:%scl_prefix}nginx|' \
		$RPM_BUILD_ROOT%{_root_libexecdir}/initscripts/legacy-actions/%{?scl:%scl_prefix}nginx/${f}
	sed -i 's|\$localstatedir|%{_localstatedir}|' \
		$RPM_BUILD_ROOT%{_root_libexecdir}/initscripts/legacy-actions/%{?scl:%scl_prefix}nginx/${f}
done

%else
install -p -D -m 0755 %{SOURCE15} \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx

sed -i 's|\$sbindir|%{_sbindir}|' \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx
sed -i 's|\$localstatedir|%{_localstatedir}|' \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx
sed -i 's|\$sysconfdir|%{_sysconfdir}|' \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx
sed -i 's|\$scl|%scl_prefix|' \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx


install -p -D -m 0644 %{SOURCE16} \
    %{buildroot}/etc/sysconfig/%{?scl:%scl_prefix}nginx

sed -i 's|\$sysconfdir|%{_sysconfdir}|' \
    %{buildroot}/etc/sysconfig/%{?scl:%scl_prefix}nginx
%endif

install -p -D -m 0644 %{SOURCE11} \
    %{buildroot}/etc/logrotate.d/%{?scl:%scl_prefix}nginx

sed -i 's|\$logdir|%{nginx_logdir}|' \
    %{buildroot}/etc/logrotate.d/%{?scl:%scl_prefix}nginx
sed -i 's|\$localstatedir|%{_localstatedir}|' \
    %{buildroot}/etc/logrotate.d/%{?scl:%scl_prefix}nginx

install -p -d -m 0755 %{buildroot}%{nginx_confdir}/conf.d
install -p -d -m 0700 %{buildroot}%{nginx_home}
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}/client_body
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}/proxy
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}/fastcgi
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}/uwsgi
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}/scgi
install -p -d -m 0700 %{buildroot}%{nginx_logdir}
install -p -d -m 0755 %{buildroot}%{nginx_webroot}

install -p -m 0644 %{SOURCE12} \
    %{buildroot}%{nginx_confdir}

# Change the nginx.conf paths
sed -i 's|\$datadir|%{_datadir}|' \
    %{buildroot}%{nginx_confdir}/nginx.conf
sed -i 's|\$sysconfdir|%{_sysconfdir}|' \
    %{buildroot}%{nginx_confdir}/nginx.conf
sed -i 's|\$localstatedir|%{_localstatedir}|' \
    %{buildroot}%{nginx_confdir}/nginx.conf
sed -i 's|\$logdir|%{nginx_logdir}|' \
    %{buildroot}%{nginx_confdir}/nginx.conf

touch -r %{SOURCE12} %{buildroot}%{nginx_confdir}/nginx.conf

install -p -m 0644 %{SOURCE100} \
    %{buildroot}%{nginx_webroot}
install -p -m 0644 %{SOURCE101} %{SOURCE102} \
    %{buildroot}%{nginx_webroot}
install -p -m 0644 %{SOURCE103} %{SOURCE104} \
    %{buildroot}%{nginx_webroot}

install -p -D -m 0644 %{_builddir}/nginx-%{version}/man/nginx.8 \
    %{buildroot}%{_mandir}/man8/nginx.8

%if 0%{?scl:1} && 0%{?use_perl}
# pm man page is installed to bad directory for some reason... Move it to
# the proper one.
mkdir -p %{buildroot}%{_mandir}/man3/
mv %{buildroot}/usr/share/man/man3/* %{buildroot}%{_mandir}/man3/
%endif

mkdir -p %{buildroot}%{_localstatedir}/run/nginx

# Replaces variables in man page with proper values
sed -i 's|\%\%PREFIX\%\%|%{nginx_datadir}|' \
    %{buildroot}%{_mandir}/man8/nginx.8
sed -i 's|\%\%PID_PATH\%\%|%{_localstatedir}/run/nginx/nginx.pid|' \
    %{buildroot}%{_mandir}/man8/nginx.8
sed -i 's|\%\%CONF_PATH\%\%|%{nginx_confdir}/nginx.conf|' \
    %{buildroot}%{_mandir}/man8/nginx.8
sed -i 's|\%\%ERROR_LOG_PATH\%\%|%{nginx_logdir}/error.log|' \
    %{buildroot}%{_mandir}/man8/nginx.8

%pre
getent group %{nginx_group} > /dev/null || groupadd -r %{nginx_group}
getent passwd %{nginx_user} > /dev/null || \
    useradd -r -d %{nginx_home} -g %{nginx_group} \
    -s /sbin/nologin -c "Nginx web server" %{nginx_user}
exit 0

%post
restorecon -R %{_scl_root} >/dev/null 2>&1 || :
semanage fcontext -a -e /var/log/nginx %{nginx_logdir} >/dev/null 2>&1 || :
restorecon -R %{nginx_logdir} >/dev/null 2>&1 || :
%if %{use_systemd}
%systemd_post %{service_name}.service
%else
semanage fcontext -a -e /etc/rc.d/init.d/nginx /etc/rc.d/init.d/%{?scl:%scl_prefix}nginx >/dev/null 2>&1 || :
restorecon -R /etc/rc.d/init.d/%{?scl:%scl_prefix}nginx >/dev/null 2>&1 || :
if [ $1 -eq 1 ]; then
    /sbin/chkconfig --add %{name}
fi
%endif
if [ $1 -eq 2 ]; then
    # Make sure these directories are not world readable.
    chmod 700 %{nginx_home}
    chmod -R 700 %{nginx_home_tmp}
    chmod 700 %{nginx_logdir}
fi

%preun
%if %{use_systemd}
%systemd_preun %{service_name}.service
%else
if [ $1 -eq 0 ]; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi
%endif

%postun
%if %{use_systemd}
%systemd_postun %{service_name}.service
%else
if [ $1 -eq 2 ]; then
    /sbin/service %{name} upgrade || :
fi
%endif

%files
%doc LICENSE CHANGES README
%{nginx_datadir}/
%{_sbindir}/nginx
%if 0%{?use_perl}
%{_mandir}/man3/nginx.3pm*
%endif
%{_mandir}/man8/nginx.8*
%if %{use_systemd}
%{_unitdir}/%{service_name}.service
%dir %{_root_libexecdir}/initscripts/legacy-actions/%{?scl:%scl_prefix}nginx
%{_root_libexecdir}/initscripts/legacy-actions/%{?scl:%scl_prefix}nginx/*
%else
/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx
%config(noreplace) /etc/sysconfig/%{?scl:%scl_prefix}nginx
%endif
%dir %{nginx_confdir}
%dir %{nginx_confdir}/conf.d
%config(noreplace) %{nginx_confdir}/fastcgi.conf
%config(noreplace) %{nginx_confdir}/fastcgi.conf.default
%config(noreplace) %{nginx_confdir}/fastcgi_params
%config(noreplace) %{nginx_confdir}/fastcgi_params.default
%config(noreplace) %{nginx_confdir}/koi-utf
%config(noreplace) %{nginx_confdir}/koi-win
%config(noreplace) %{nginx_confdir}/mime.types
%config(noreplace) %{nginx_confdir}/mime.types.default
%config(noreplace) %{nginx_confdir}/nginx.conf
%config(noreplace) %{nginx_confdir}/nginx.conf.default
%config(noreplace) %{nginx_confdir}/scgi_params
%config(noreplace) %{nginx_confdir}/scgi_params.default
%config(noreplace) %{nginx_confdir}/uwsgi_params
%config(noreplace) %{nginx_confdir}/uwsgi_params.default
%config(noreplace) %{nginx_confdir}/win-utf
%config(noreplace) /etc/logrotate.d/%{?scl:%scl_prefix}nginx
%if 0%{?use_perl}
%dir %{perl_vendorarch}/auto/nginx
%{perl_vendorarch}/nginx.pm
%{perl_vendorarch}/auto/nginx/nginx.so
%endif
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_home}
%attr(700,%{nginx_user},%{nginx_group}) %{nginx_home_tmp}
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_logdir}
%attr(700,%{nginx_user},%{nginx_group}) %dir %{_localstatedir}/run/nginx

%changelog
* Wed Jan 21 2015 Jan Kaluza <jkaluza@redhat.com> - 1:1.6.2-3
- set use_systemd only on RHEL7

* Mon Jan 19 2015 Jan Kaluza <jkaluza@redhat.com> - 1:1.6.2-2
- add support for Phusion Passenger

* Tue Jan 06 2015 Jan Kaluza <jkaluza@redhat.com> - 1:1.6.2-1
- update to version 1.6.2
- do not use conditionals in systemd macros (#1152514)

* Wed Sep 17 2014 Jan Kaluza <jkaluza@redhat.com> - 1:1.6.1-2
- prevent SSL session reuse in unrelated server{} blocks (CVE-2014-3616)

* Wed Aug 06 2014 Jan Kaluza <jkaluza@redhat.com> - 1:1.6.1-1
- update to 1.6.1 (CVE-2014-3556)

* Wed Jul 02 2014 Jan Kaluza <jkaluza@redhat.com> - 1:1.6.0-4
- correct the path for previous SELinux fix (#1088912)

* Wed Jul 02 2014 Jan Kaluza <jkaluza@redhat.com> - 1:1.6.0-3
- fix SELinux context of initscript (#1088912)

* Tue Jun 24 2014 Jan Kaluza <jkaluza@redhat.com> - 1:1.6.0-2
- rebuild because of rename to nginx16

* Mon Jun  9 2014 Joe Orton <jorton@redhat.com> - 1:1.6.0-1
- update to 1.6.0 (#1101921)

* Tue Mar  4 2014 Joe Orton <jorton@redhat.com> - 1:1.4.4-10
- run restorecon in %%post for #1072266

* Tue Mar  4 2014 Joe Orton <jorton@redhat.com> - 1:1.4.4-9
- fix SELinux context for log directory (#1072266)

* Thu Feb 20 2014 Jan Kaluza <jkaluza@redhat.com> - 1:1.4.4-8
- update poweredby logo and show it on default pages (#1065981)

* Wed Jan 15 2014 Jan Kaluza <jkaluza@redhat.com> - 1:1.4.4-7
- call restorecon in post script (#1052935)

* Mon Jan 06 2014 Jan Kaluza <jkaluza@redhat.com> - 1:1.4.4-6
- create temp subdirectories in nginx_home_tmp during installation (#1040470)

* Tue Nov 26 2013 Joe Orton <jorton@redhat.com> - 1:1.4.4-5
- further default config tweak

* Tue Nov 26 2013 Joe Orton <jorton@redhat.com> - 1:1.4.4-4
- update config file for log directory

* Tue Nov 26 2013 Joe Orton <jorton@redhat.com> - 1:1.4.4-3
- change log directory

* Tue Nov 19 2013 Joe Orton <jorton@redhat.com> - 1:1.4.4-1
- update to 1.4.4 (CVE-2013-4547)

* Mon Nov 18 2013 Jan Kaluza <jkaluza@redhat.com> - 1:1.4.2-6
- require scl_runtime

* Mon Nov 18 2013 Jan Kaluza <jkaluza@redhat.com> - 1:1.4.2-5
- improved index.html

* Mon Nov 18 2013 Jan Kaluza <jkaluza@redhat.com> - 1:1.4.2-4
- support for software collections

* Fri Aug 09 2013 Jonathan Steffan <jsteffan@fedoraproject.org> - 1:1.4.2-3
- Add in conditionals to build for non-systemd targets

* Sat Aug 03 2013 Petr Pisar <ppisar@redhat.com> - 1:1.4.2-2
- Perl 5.18 rebuild

* Fri Jul 19 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.4.2-1
- update to upstream release 1.4.2

* Wed Jul 17 2013 Petr Pisar <ppisar@redhat.com> - 1:1.4.1-3
- Perl 5.18 rebuild

* Tue Jun 11 2013 Remi Collet <rcollet@redhat.com> - 1:1.4.1-2
- rebuild for new GD 2.1.0

* Tue May 07 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.4.1-1
- update to upstream release 1.4.1 (#960605, #960606):
  CVE-2013-2028 stack-based buffer overflow when handling certain chunked
  transfer encoding requests

* Sun Apr 28 2013 Dan Horák <dan[at]danny.cz> - 1:1.4.0-2
- gperftools exist only on selected arches

* Fri Apr 26 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.4.0-1
- update to upstream release 1.4.0
- enable SPDY module (new in this version)
- enable http gunzip module (new in this version)
- enable google perftools module and add gperftools-devel to BR
- enable debugging (#956845)
- trim changelog

* Tue Apr 02 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.8-1
- update to upstream release 1.2.8

* Fri Feb 22 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.7-2
- make sure nginx directories are not world readable (#913724, #913735)

* Sat Feb 16 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.7-1
- update to upstream release 1.2.7
- add .asc file

* Tue Feb 05 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.6-6
- use 'kill' instead of 'systemctl' when rotating log files to workaround
  SELinux issue (#889151)

* Wed Jan 23 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.6-5
- uncomment "include /etc/nginx/conf.d/*.conf by default but leave the
  conf.d directory empty (#903065)

* Wed Jan 23 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.6-4
- add comment in nginx.conf regarding "include /etc/nginf/conf.d/*.conf"
  (#903065)

* Wed Dec 19 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.6-3
- use correct file ownership when rotating log files

* Tue Dec 18 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.6-2
- send correct kill signal and use correct file permissions when rotating
  log files (#888225)
- send correct kill signal in nginx-upgrade

* Tue Dec 11 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.6-1
- update to upstream release 1.2.6

* Sat Nov 17 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.5-1
- update to upstream release 1.2.5

* Sun Oct 28 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.4-1
- update to upstream release 1.2.4
- introduce new systemd-rpm macros (#850228)
- link to official documentation not the community wiki (#870733)
- do not run systemctl try-restart after package upgrade to allow the
  administrator to run nginx-upgrade and avoid downtime
- add nginx man page (#870738)
- add nginx-upgrade man page and remove README.fedora
- remove chkconfig from Requires(post/preun)
- remove initscripts from Requires(preun/postun)
- remove separate configuration files in "/etc/nginx/conf.d" directory
  and revert to upstream default of a centralized nginx.conf file
  (#803635) (#842738)

* Fri Sep 21 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.3-1
- update to upstream release 1.2.3

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.2.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Jun 28 2012 Petr Pisar <ppisar@redhat.com> - 1:1.2.1-2
- Perl 5.16 rebuild

* Sun Jun 10 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.1-1
- update to upstream release 1.2.1

* Fri Jun 08 2012 Petr Pisar <ppisar@redhat.com> - 1:1.2.0-2
- Perl 5.16 rebuild

* Wed May 16 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.2.0-1
- update to upstream release 1.2.0

* Wed May 16 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.0.15-4
- add nginx-upgrade to replace functionality from the nginx initscript
  that was lost after migration to systemd
- add README.fedora to describe usage of nginx-upgrade
- nginx.logrotate: use built-in systemd kill command in postrotate script
- nginx.service: start after syslog.target and network.target
- nginx.service: remove unnecessary references to config file location
- nginx.service: use /bin/kill instead of "/usr/sbin/nginx -s" following
  advice from nginx-devel
- nginx.service: use private /tmp

* Mon May 14 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.0.15-3
- fix incorrect postrotate script in nginx.logrotate

* Thu Apr 19 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.0.15-2
- renable auto-cc-gcc patch due to warnings on rawhide

* Sat Apr 14 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.0.15-1
- update to upstream release 1.0.15
- no need to apply auto-cc-gcc patch
- add %%global _hardened_build 1

* Thu Mar 15 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.0.14-1
- update to upstream release 1.0.14
- amend some %%changelog formatting

* Tue Mar 06 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.0.13-1
- update to upstream release 1.0.13
- amend --pid-path and --log-path

* Sun Mar 04 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.0.12-5
- change pid path in nginx.conf to match systemd service file

* Sun Mar 04 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.0.12-3
- fix %%pre scriptlet

* Mon Feb 20 2012 Jamie Nguyen <jamielinux@fedoraproject.org> - 1:1.0.12-2
- update upstream URL
- replace %%define with %%global
- remove obsolete BuildRoot tag, %%clean section and %%defattr
- remove various unnecessary commands
- add systemd service file and update scriptlets
- add Epoch to accommodate %%triggerun as part of systemd migration

* Sun Feb 19 2012 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.0.12-1
- Update to 1.0.12

* Thu Nov 17 2011 Keiran "Affix" Smith <fedora@affix.me> - 1.0.10-1
- Bugfix: a segmentation fault might occur in a worker process if resolver got a big DNS response. Thanks to Ben Hawkes.
- Bugfix: in cache key calculation if internal MD5 implementation wasused; the bug had appeared in 1.0.4.
- Bugfix: the module ngx_http_mp4_module sent incorrect "Content-Length" response header line if the "start" argument was used. Thanks to Piotr Sikora.

* Thu Oct 27 2011 Keiran "Affix" Smith <fedora@affix.me> - 1.0.8-1
- Update to new 1.0.8 stable release

* Fri Aug 26 2011 Keiran "Affix" Smith <fedora@affix.me> - 1.0.5-1
- Update nginx to Latest Stable Release

* Fri Jun 17 2011 Marcela Mašláňová <mmaslano@redhat.com> - 1.0.0-3
- Perl mass rebuild

* Thu Jun 09 2011 Marcela Mašláňová <mmaslano@redhat.com> - 1.0.0-2
- Perl 5.14 mass rebuild

* Wed Apr 27 2011 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.0.0-1
- Update to 1.0.0

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.8.53-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sun Dec 12 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.8.53.5
- Extract out default config into its own file (bug #635776)

* Sun Dec 12 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.8.53-4
- Revert ownership of log dir

* Sun Dec 12 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.8.53-3
- Change ownership of /var/log/nginx to be 0700 nginx:nginx
- update init script to use killproc -p
- add reopen_logs command to init script
- update init script to use nginx -q option

* Sun Oct 31 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.8.53-2
- Fix linking of perl module

* Sun Oct 31 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.8.53-1
- Update to new stable 0.8.53

* Sat Jul 31 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.7.67-2
- add Provides: webserver (bug #619693)

* Sun Jun 20 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.7.67-1
- Update to new stable 0.7.67
- fix bugzilla #591543

* Tue Jun 01 2010 Marcela Maslanova <mmaslano@redhat.com> - 0.7.65-2
- Mass rebuild with perl-5.12.0

* Mon Feb 15 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.7.65-1
- Update to new stable 0.7.65
- change ownership of logdir to root:root
- add support for ipv6 (bug #561248)
- add random_index_module
- add secure_link_module

* Fri Dec 04 2009 Jeremy Hinegardner <jeremy at hinegardner dot org> - 0.7.64-1
- Update to new stable 0.7.64
