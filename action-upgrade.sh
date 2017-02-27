#!/bin/sh
[ ! -f $localstatedir/run/nginx/nginx.pid ] && exit 1
echo "Start new nginx master..."
/bin/systemctl kill --signal=SIGUSR2 $nginxservice
sleep 5
[ ! -f $localstatedir/run/nginx/nginx.pid.oldbin ] && sleep 5
if [ ! -f $localstatedir/run/nginx/nginx.pid.oldbin ]; then
	echo "Failed to start new nginx master."
	exit 1
fi
echo "Stop old nginx master gracefully..."
oldpid=`cat $localstatedir/run/nginx/nginx.pid.oldbin 2>/dev/null`
/bin/kill -s QUIT $oldpid 2>/dev/null
