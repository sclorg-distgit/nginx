%{?scl:%scl_package nginx}

%if 0%{?rhel} > 6
%define use_systemd 1
%else
%define use_systemd 0
%endif

%define use_perl 1

%define use_geoip 0
%global with_gperftools     0

%global  _hardened_build     1
%global  nginx_user          nginx
%global  nginx_group         %{nginx_user}
%global  nginx_home          %{_localstatedir}/lib/nginx
%global  nginx_home_tmp      %{nginx_home}/tmp
%global  nginx_confdir       %{_sysconfdir}/nginx
%global  nginx_datadir       %{_datadir}/nginx
%global  nginx_logdir        %{_localstatedir}/log/nginx
%global  nginx_webroot       %{nginx_datadir}/html

%global service_name %{?scl_prefix}nginx

%if 0%{?scl:1}
%global scl_upper %{lua:print(string.upper(string.gsub(rpm.expand("%{scl}"), "-", "_")))}
%endif

%{!?scl_perl_prefix: %global scl_perl_prefix rh-perl526-}
%{!?_nginx_perl_vendorarch: %global _nginx_perl_vendorarch %perl_vendorarch}

%{?filter_setup:
%filter_requires_in %{_nginx_perl_vendorarch}
%filter_provides_in %{_nginx_perl_vendorarch}
%filter_provides_in %{_libdir}/nginx/modules
%filter_setup
}

Name:              %{?scl:%scl_prefix}nginx
Epoch:             1
Version:           1.16.1
Release:           3%{?dist}
Summary:           A high performance web server and reverse proxy server
Group:             System Environment/Daemons
# BSD License (two clause)
# http://www.freebsd.org/copyright/freebsd-license.html
License:           BSD
URL:               http://nginx.org/

Source0:           http://nginx.org/download/nginx-%{version}.tar.gz
Source2:           scl-register-helper.sh
Source3:           daemon-scl-helper.sh
Source10:          nginx.service
Source11:          nginx.logrotate
Source12:          nginx.conf
Source15:          nginx.init
Source16:          nginx.sysconfig
Source100:         index.html
Source101:         poweredby.png
Source102:         nginx-logo.png
Source103:         404.html
Source104:         50x.html
Source200:         README.dynamic

# removes -Werror in upstream build scripts.  -Werror conflicts with
# -D_FORTIFY_SOURCE=2 causing warnings to turn into errors.
Patch0:            nginx-auto-cc-gcc.patch

# downstream patch - changing logs permissions to 664 instead
# previous 644
Patch1:            nginx-1.14.0-logs-perm.patch

# PKCS#11 engine fix
Patch2:            nginx-1.16.0-pkcs11.patch

# https://bugzilla.redhat.com/show_bug.cgi?id=1655530
Patch3:            nginx-1.14.1-perl-module-hardening.patch


BuildRequires:     gd-devel
%if 0%{?with_gperftools}
BuildRequires:     gperftools-devel
%endif
BuildRequires:     libxslt-devel
BuildRequires:     openssl-devel >= 1:1.0.2k
BuildRequires:     pcre-devel
BuildRequires:     zlib-devel
%if 0%{?use_geoip}
BuildRequires:     GeoIP-devel
%endif
Requires:          gd
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

%if 0%{?use_geoip}
%package mod-http-geoip
Group:             System Environment/Daemons
Summary:           Nginx HTTP geoip module
BuildRequires:     GeoIP-devel
Requires:          %{?scl:%scl_prefix}nginx
Requires:          GeoIP

%description mod-http-geoip
%{summary}.
%endif

%package mod-http-image-filter
Group:             System Environment/Daemons
Summary:           Nginx HTTP image filter module
BuildRequires:     gd-devel
Requires:          %{?scl:%scl_prefix}nginx
Requires:          gd

%description mod-http-image-filter
%{summary}.

%if 0%{?use_perl}
%package mod-http-perl
Group:             System Environment/Daemons
Summary:           Nginx HTTP perl module
BuildRequires:     %{scl_perl_prefix}perl-devel
%if 0%{?fedora} >= 24
BuildRequires:     %{scl_perl_prefix}perl-generators
%endif
BuildRequires:     %{scl_perl_prefix}perl(ExtUtils::Embed)
Requires:          %{?scl:%scl_prefix}nginx
Requires:          %{scl_perl_prefix}perl(:MODULE_COMPAT_%(%{?scl:scl enable %{scl_perl} '}eval "`%{__perl} -V:version`"; echo $version%{?scl:'}))
Requires:          %{scl_perl_prefix}perl(constant)

%description mod-http-perl
%{summary}.
%endif

%package mod-http-xslt-filter
Group:             System Environment/Daemons
Summary:           Nginx XSLT module
BuildRequires:     libxslt-devel
Requires:          %{?scl:%scl_prefix}nginx

%description mod-http-xslt-filter
%{summary}.

%package mod-mail
Group:             System Environment/Daemons
Summary:           Nginx mail modules
Requires:          %{?scl:%scl_prefix}nginx

%description mod-mail
%{summary}.

%package mod-stream
Group:             System Environment/Daemons
Summary:           Nginx stream modules
Requires:          %{?scl:%scl_prefix}nginx

%description mod-stream
%{summary}.


%prep
%setup -q -n nginx-%{version}
%patch0 -p0
%patch1 -p1
%patch2 -p1
%patch3 -p1
cp %{SOURCE200} .

%build
%if 0%{?use_perl}
%{?scl:scl enable %{scl_perl} - << \EOF}
%endif
set -x

# nginx does not utilize a standard configure script.  It has its own
# and the standard configure options cause the nginx configure script
# to error out.  This is is also the reason for the DESTDIR environment
# variable.
export DESTDIR=%{buildroot}
./configure \
    --prefix=%{nginx_datadir} \
    --sbin-path=%{_sbindir}/nginx \
    --modules-path=%{_libdir}/nginx/modules \
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
    --with-http_v2_module \
    --with-http_auth_request_module \
    --with-http_realip_module \
    --with-stream_ssl_preread_module \
    --with-http_addition_module \
    --with-http_xslt_module=dynamic \
    --with-http_image_filter_module=dynamic \
%if 0%{?use_geoip}
    --with-http_geoip_module=dynamic \
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
    --with-http_slice_module \
    --with-http_stub_status_module \
%if 0%{?use_perl}
    --with-http_perl_module=dynamic \
%endif
    --with-mail=dynamic \
    --with-mail_ssl_module \
    --with-pcre \
    --with-pcre-jit \
    --with-stream=dynamic \
    --with-stream_ssl_module \
%if 0%{?with_gperftools}
    --with-google_perftools_module \
%endif
    --with-debug \
    --with-cc-opt="%{optflags} $(pcre-config --cflags)" \
    --with-ld-opt="$RPM_LD_FLAGS -Wl,-E" # so the perl module finds its symbols

make %{?_smp_mflags}
%if 0%{?use_perl}
%{?scl:EOF}
%endif

%install
#include helper script for creating register stuff
export _SR_BUILDROOT=%{buildroot}
export _SR_SCL_SCRIPTS=%{?_scl_scripts}
source %{SOURCE2}

%if 0%{?use_perl}
%{?scl:scl enable %{scl_perl} - << \EOF}
%endif
set -x
make install DESTDIR=%{buildroot} INSTALLDIRS=vendor \
     INSTALLVENDORARCH=%{_nginx_perl_vendorarch} \
     INSTALLVENDORMAN3DIR=%{_mandir}/man3
%if 0%{?use_perl}
%{?scl:EOF}
%endif

find %{buildroot} -type f -name .packlist -exec rm -f '{}' \;
find %{buildroot} -type f -name perllocal.pod -exec rm -f '{}' \;
find %{buildroot} -type f -empty -exec rm -f '{}' \;
find %{buildroot} -type f -iname '*.so' -exec chmod 0755 '{}' \;

install -D -p -m 0755 %{SOURCE3} \
    %{buildroot}%{_libexecdir}/nginx-scl-helper

%if %{use_systemd}
install -p -D -m 0644 %{SOURCE10} \
    %{buildroot}%{_unitdir}/%{?scl:%scl_prefix}nginx.service

sed -i 's|\$sbindir|%{_sbindir}|' \
    %{buildroot}%{_unitdir}/%{?scl:%scl_prefix}nginx.service
sed -i 's|\$localstatedir|%{_localstatedir}|' \
    %{buildroot}%{_unitdir}/%{?scl:%scl_prefix}nginx.service
sed -i 's|\$libexecdir|%{_libexecdir}|' \
    %{buildroot}%{_unitdir}/%{?scl:%scl_prefix}nginx.service
touch -r %{SOURCE10} \
    %{buildroot}%{_unitdir}/%{?scl:%scl_prefix}nginx.service

scl_reggen %{name} --cpfile %{_unitdir}/%{?scl:%scl_prefix}nginx.service

%else
install -p -D -m 0755 %{SOURCE15} \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx

sed -i 's|\$sbindir|%{_sbindir}|' \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx
sed -i 's|\$localstatedir|%{_localstatedir}|' \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx
sed -i 's|\$sysconfdir|%{_sysconfdir}|' \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx
sed -i 's|\$sclprefix|%scl_prefix|g' \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx
sed -i 's|\$sclname|%scl|g' \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx
sed -i 's|\$upperscl|%{scl_upper}|g' \
    %{buildroot}/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx
scl_reggen %{name} --cpfile %{_root_initddir}/%{?scl:%scl_prefix}nginx

install -p -D -m 0644 %{SOURCE16} \
    %{buildroot}/%{_sysconfdir}/sysconfig/%{?scl:%scl_prefix}nginx

sed -i 's|\$sysconfdir|%{_sysconfdir}|' \
    %{buildroot}/%{_sysconfdir}/sysconfig/%{?scl:%scl_prefix}nginx
scl_reggen %{name} --mkdir %{_sysconfdir}/sysconfig
scl_reggen %{name} --cpfile %{_sysconfdir}/sysconfig/%{?scl:%scl_prefix}nginx
%endif

install -p -D -m 0644 %{SOURCE11} \
    %{buildroot}/etc/logrotate.d/%{?scl:%scl_prefix}nginx

sed -i 's|\$logdir|%{nginx_logdir}|' \
    %{buildroot}/etc/logrotate.d/%{?scl:%scl_prefix}nginx
sed -i 's|\$localstatedir|%{_localstatedir}|' \
    %{buildroot}/etc/logrotate.d/%{?scl:%scl_prefix}nginx
scl_reggen %{name} --cpfile %{_root_sysconfdir}/logrotate.d/%{?scl:%scl_prefix}nginx

install -p -d -m 0755 %{buildroot}%{nginx_confdir}/conf.d
install -p -d -m 0755 %{buildroot}%{nginx_confdir}/default.d

install -p -d -m 0700 %{buildroot}%{nginx_home}
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}/client_body
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}/proxy
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}/fastcgi
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}/uwsgi
install -p -d -m 0700 %{buildroot}%{nginx_home_tmp}/scgi
install -p -d -m 0700 %{buildroot}%{nginx_logdir}
install -p -d -m 0755 %{buildroot}%{nginx_webroot}

scl_reggen %{name} --mkdir %{nginx_confdir}/conf.d
scl_reggen %{name} --mkdir %{nginx_confdir}/default.d
scl_reggen %{name} --mkdir %{nginx_home}
scl_reggen %{name} --mkdir %{nginx_home_tmp}
scl_reggen %{name} --mkdir %{nginx_home_tmp}/client_body
scl_reggen %{name} --mkdir %{nginx_home_tmp}/proxy
scl_reggen %{name} --mkdir %{nginx_home_tmp}/fastcgi
scl_reggen %{name} --mkdir %{nginx_home_tmp}/uwsgi
scl_reggen %{name} --mkdir %{nginx_home_tmp}/scgi
scl_reggen %{name} --mkdir %{nginx_logdir}
scl_reggen %{name} --mkdir %{nginx_webroot}

scl_reggen %{name} --chmod 0755 %{nginx_confdir}/conf.d
scl_reggen %{name} --chmod 0755 %{nginx_confdir}/default.d
scl_reggen %{name} --chmod 0700 %{nginx_home}
scl_reggen %{name} --chmod 0700 %{nginx_home_tmp}
scl_reggen %{name} --chmod 0700 %{nginx_home_tmp}/client_body
scl_reggen %{name} --chmod 0700 %{nginx_home_tmp}/proxy
scl_reggen %{name} --chmod 0700 %{nginx_home_tmp}/fastcgi
scl_reggen %{name} --chmod 0700 %{nginx_home_tmp}/uwsgi
scl_reggen %{name} --chmod 0700 %{nginx_home_tmp}/scgi
scl_reggen %{name} --chmod 0700 %{nginx_logdir}
scl_reggen %{name} --chmod 0755 %{nginx_webroot}

scl_reggen %{name} --cpfile %{nginx_confdir}/fastcgi.conf
scl_reggen %{name} --cpfile %{nginx_confdir}/fastcgi.conf.default
scl_reggen %{name} --cpfile %{nginx_confdir}/fastcgi_params
scl_reggen %{name} --cpfile %{nginx_confdir}/fastcgi_params.default
scl_reggen %{name} --cpfile %{nginx_confdir}/koi-utf
scl_reggen %{name} --cpfile %{nginx_confdir}/koi-win
scl_reggen %{name} --cpfile %{nginx_confdir}/mime.types
scl_reggen %{name} --cpfile %{nginx_confdir}/mime.types.default
scl_reggen %{name} --cpfile %{nginx_confdir}/nginx.conf
scl_reggen %{name} --cpfile %{nginx_confdir}/nginx.conf.default
scl_reggen %{name} --cpfile %{nginx_confdir}/scgi_params
scl_reggen %{name} --cpfile %{nginx_confdir}/scgi_params.default
scl_reggen %{name} --cpfile %{nginx_confdir}/uwsgi_params
scl_reggen %{name} --cpfile %{nginx_confdir}/uwsgi_params.default
scl_reggen %{name} --cpfile %{nginx_confdir}/win-utf


scl_reggen %{name} --runafterregister "semanage fcontext -a -e /var/log/nginx %{nginx_logdir} >/dev/null 2>&1 || :"
scl_reggen %{name} --runafterregister "restorecon -R %{nginx_logdir} >/dev/null 2>&1 || :"
scl_reggen %{name} --runafterregister "semanage fcontext -a -e %{_root_sysconfdir}/nginx %{nginx_confdir} >/dev/null 2>&1 || :"
scl_reggen %{name} --runafterregister "restorecon -R %{nginx_confdir} >/dev/null 2>&1 || :"
scl_reggen %{name} --runafterregister "semanage fcontext -a -e %{_root_localstatedir}/lib/nginx %{_localstatedir}/lib/nginx >/dev/null 2>&1 || :"
scl_reggen %{name} --runafterregister "restorecon -R %{_localstatedir}/lib/nginx >/dev/null 2>&1 || :"
scl_reggen %{name} --runafterregister "semanage fcontext -a -e %{_root_localstatedir}/run/nginx %{_localstatedir}/run/nginx >/dev/null 2>&1 || :"
scl_reggen %{name} --runafterregister "restorecon -R %{_localstatedir}/run/nginx >/dev/null 2>&1 || :"

install -p -m 0644 %{SOURCE12} \
    %{buildroot}%{nginx_confdir}

# Change the nginx.conf paths
sed -i 's|\$datadir|%{_datadir}|' \
    %{buildroot}%{nginx_confdir}/nginx.conf
sed -i 's|\$docdir|%{_docdir}|' \
    %{buildroot}%{nginx_confdir}/nginx.conf
sed -i 's|\$sysconfdir|%{_sysconfdir}|' \
    %{buildroot}%{nginx_confdir}/nginx.conf
sed -i 's|\$localstatedir|%{_localstatedir}|' \
    %{buildroot}%{nginx_confdir}/nginx.conf
sed -i 's|\$logdir|%{nginx_logdir}|' \
    %{buildroot}%{nginx_confdir}/nginx.conf

install -p -d -m 0755 %{buildroot}%{_datadir}/nginx/modules
install -p -d -m 0755 %{buildroot}%{_libdir}/nginx/modules

%if 0%{?use_geoip}
echo 'load_module "%{_libdir}/nginx/modules/ngx_http_geoip_module.so";' \
    > %{buildroot}%{_datadir}/nginx/modules/mod-http-geoip.conf
%endif
echo 'load_module "%{_libdir}/nginx/modules/ngx_http_image_filter_module.so";' \
    > %{buildroot}%{_datadir}/nginx/modules/mod-http-image-filter.conf
%if 0%{?use_perl}
cat > %{buildroot}%{_datadir}/nginx/modules/mod-http-perl.conf <<EOF
load_module "%{_libdir}/nginx/modules/ngx_http_perl_module.so";
env PERL5LIB;
env LD_LIBRARY_PATH;
EOF
%endif
echo 'load_module "%{_libdir}/nginx/modules/ngx_http_xslt_filter_module.so";' \
    > %{buildroot}%{_datadir}/nginx/modules/mod-http-xslt-filter.conf
echo 'load_module "%{_libdir}/nginx/modules/ngx_mail_module.so";' \
    > %{buildroot}%{_datadir}/nginx/modules/mod-mail.conf
echo 'load_module "%{_libdir}/nginx/modules/ngx_stream_module.so";' \
    > %{buildroot}%{_datadir}/nginx/modules/mod-stream.conf

touch -r %{SOURCE12} %{buildroot}%{nginx_confdir}/nginx.conf \
      %{buildroot}%{_datadir}/nginx/modules/*.conf

install -p -m 0644 %{SOURCE100} \
    %{buildroot}%{nginx_webroot}
install -p -m 0644 %{SOURCE101} %{SOURCE102} \
    %{buildroot}%{nginx_webroot}
install -p -m 0644 %{SOURCE103} %{SOURCE104} \
    %{buildroot}%{nginx_webroot}

install -p -D -m 0644 %{_builddir}/nginx-%{version}/man/nginx.8 \
    %{buildroot}%{_mandir}/man8/nginx.8

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

%if 0%{?scl:1}
cat << EOF | tee -a %{buildroot}%{?_scl_scripts}/service-environment
# Services are started in a fresh environment without any influence of user's
# environment (like environment variable values). As a consequence,
# information of all enabled collections will be lost during service start up.
# If user needs to run a service under any software collection enabled, this
# collection has to be written into %{scl_upper}_SCLS_ENABLED variable
# in %{?_scl_scripts}/service-environment.
%{scl_upper}_SCLS_ENABLED="%{scl}"
EOF
%endif #scl

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

semanage fcontext -a -e %{_root_sysconfdir}/nginx %{nginx_confdir} >/dev/null 2>&1 || :
restorecon -R %{nginx_confdir} >/dev/null 2>&1 || :

semanage fcontext -a -e %{_root_localstatedir}/lib/nginx %{_localstatedir}/lib/nginx >/dev/null 2>&1 || :
restorecon -R %{_localstatedir}/lib/nginx >/dev/null 2>&1 || :

semanage fcontext -a -e %{_root_localstatedir}/run/nginx %{_localstatedir}/run/nginx >/dev/null 2>&1 || :
restorecon -R %{_localstatedir}/run/nginx >/dev/null 2>&1 || :

%if %{use_systemd}
# Ensure the helper script has the right context.
semanage fcontext -a -t httpd_exec_t %{_root_libexecdir}/nginx-scl-helper >/dev/null 2>&1 || :
restorecon -R %{_libexecdir}/nginx-scl-helper >/dev/null 2>&1 || :
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
%doc LICENSE CHANGES README README.dynamic
%dir %{nginx_datadir}
%{nginx_datadir}/html
%dir %{nginx_datadir}/modules
%{_sbindir}/nginx
%{_mandir}/man8/nginx.8*
%{?scl:%{_libexecdir}/nginx-scl-helper}
%if %{use_systemd}
%{_unitdir}/%{service_name}.service
%else
/etc/rc.d/init.d/%{?scl:%scl_prefix}nginx
%config(noreplace) %{_sysconfdir}/sysconfig/%{?scl:%scl_prefix}nginx
%endif
%dir %{nginx_confdir}
%dir %{nginx_confdir}/conf.d
%dir %{nginx_confdir}/default.d
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
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_home}
%attr(700,%{nginx_user},%{nginx_group}) %{nginx_home_tmp}
%attr(700,%{nginx_user},%{nginx_group}) %dir %{nginx_logdir}
%attr(700,%{nginx_user},%{nginx_group}) %dir %{_localstatedir}/run/nginx
%dir %{_libdir}/nginx
%dir %{_libdir}/nginx/modules

%{?scl: %{_scl_scripts}/register.d/*}
%{?scl: %{_scl_scripts}/register.content/*}
%{?scl: %{_scl_scripts}/deregister.d/*}
%{?scl:%config(noreplace) %{?_scl_scripts}/service-environment}

%if 0%{?use_geoip}
%files mod-http-geoip
%{_datadir}/nginx/modules/mod-http-geoip.conf
%{_libdir}/nginx/modules/ngx_http_geoip_module.so
%endif

%files mod-http-image-filter
%{_datadir}/nginx/modules/mod-http-image-filter.conf
%{_libdir}/nginx/modules/ngx_http_image_filter_module.so

%if 0%{?use_perl}
%files mod-http-perl
%{_datadir}/nginx/modules/mod-http-perl.conf
%{_libdir}/nginx/modules/ngx_http_perl_module.so
%{_nginx_perl_vendorarch}/*
%{_mandir}/man3/nginx.3pm.*
%endif

%files mod-http-xslt-filter
%{_datadir}/nginx/modules/mod-http-xslt-filter.conf
%{_libdir}/nginx/modules/ngx_http_xslt_filter_module.so

%files mod-mail
%{_datadir}/nginx/modules/mod-mail.conf
%{_libdir}/nginx/modules/ngx_mail_module.so

%files mod-stream
%{_datadir}/nginx/modules/mod-stream.conf
%{_libdir}/nginx/modules/ngx_stream_module.so

%changelog
* Thu Aug 29 2019 Lubos Uhliarik <luhliari@redhat.com> - 1:1.16.1-3
- Resolves: #1745696 - CVE-2019-9511 rh-nginx116-nginx: HTTP/2: large amount
  of data request leads to denial of service
- Resolves: #1745689 - CVE-2019-9513 rh-nginx116-nginx: HTTP/2: flood using
  PRIORITY frames resulting in excessive resource consumption
- Resolves: #1745668 - CVE-2019-9516 rh-nginx116-nginx: HTTP/2: 0-length
  headers leads to denial of service

* Tue Aug 06 2019 Luboš Uhliarik <luhliari@redhat.com> - 1:1.16.0-1
- Resolves: #1721187 - RFE: add collection for nginx 1.16
- enable ngx_stream_ssl_preread module

* Wed Aug 08 2018 Luboš Uhliarik <luhliari@redhat.com> - 1:1.14.0-3
- fixed service file and error documents

* Wed Jul 18 2018 Luboš Uhliarik <luhliari@redhat.com> - 1:1.14.0-2
- Resolves: #1470746 - rh-nginx112: unexpected initscpript action

* Thu Jul 12 2018 Luboš Uhliarik <luhliari@redhat.com> - 1:1.14.0-1
- update to version 1.14.0
- Resolves: #1601544 - Switch rh-nginx114 to rh-perl526

* Tue Aug 08 2017 Luboš Uhliarik <luhliari@redhat.com> - 1:1.12.1-2
- Resolves: #1468712 - missing dependency for perl package

* Wed Jul 12 2017 Luboš Uhliarik <luhliari@redhat.com> - 1:1.12.1-1
- update to 1.12.1
- Resolves: CVE-2017-7529 nginx: Integer overflow in nginx range filter module
  leading to memory disclosure

* Tue Jun 13 2017 Luboš Uhliarik <luhliari@redhat.com> - 1:1.12.0-4
- Resolved: #1323835 - RFE: add nginx-auth-ldap to rh-nginx18

* Tue Jun 06 2017 Luboš Uhliarik <luhliari@redhat.com> - 1:1.12.0-1
- update to 1.12.0 (#1447400)

* Thu Mar 23 2017 Joe Orton <jorton@redhat.com> - 1:1.10.2-7
- filter auto-provides from module subpackages (#1434349)
- drop perl vendorarch directory ownership (#1434333)

* Thu Mar  2 2017 Joe Orton <jorton@redhat.com> - 1:1.10.2-6
- run nginx under SCL environment from SysV init script

* Thu Mar  2 2017 Joe Orton <jorton@redhat.com> - 1:1.10.2-5
- filter perl(*) req/prov (#1421927)

* Wed Mar  1 2017 Joe Orton <jorton@redhat.com> - 1:1.10.2-4
- drop explicit Requires for openssl, gd
- run nginx under SCL environment from systemd service
- fix module .conf path in nginx.conf
- pass PERL5LIB, LD_LIBRARY_PATH from env when perl is loaded (#1421927)

* Wed Feb  8 2017 Joe Orton <jorton@redhat.com> - 1:1.10.2-3
- add mod-http-perl

* Thu Jan 19 2017 Joe Orton <jorton@redhat.com> - 1:1.10.2-2
- own libdir/nginx

* Thu Jan 19 2017 Joe Orton <jorton@redhat.com> - 1:1.10.2-1
- update to 1.10.2 (#1404779)
- merge changes from Fedora

* Mon Jun 20 2016 Joe Orton <jorton@redhat.com> - 1:1.8.1-1
- update to 1.8.1 (CVE-2016-0742 CVE-2016-0746 CVE-2016-0747)
- add security fix for CVE-2016-4450

* Fri Nov 13 2015 Jan Kaluza <jkaluza@redhat.com> - 1:1.8.0-4
- fix SELinux context of /var/opt and /etc/opt directories (#1280221)

* Fri Sep 11 2015 Jan Kaluza <jkaluza@redhat.com> - 1:1.8.0-3
- fix bad path to nginx.pid in logrotate configuration (#1260595)

* Tue Aug 11 2015 Jan Kaluza <jkaluza@redhat.com> - 1:1.8.0-2
- move logs to /var/opt/rh/rh-nginx18/log (#1250095)

* Wed Jul 08 2015 Jan Kaluza <jkaluza@redhat.com> - 1:1.8.0-1
- update to version 1.8.0

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
- uncomment "include /etc/nginx/conf.d/*.conf" by default but leave the
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
