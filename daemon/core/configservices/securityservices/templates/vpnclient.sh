# -------- CUSTOMIZATION REQUIRED --------
#
# The VPNClient service builds a VPN tunnel to the specified VPN server using
# OpenVPN software and a virtual TUN/TAP device.

# directory containing the certificate and key described below
keydir=${config["keydir"]}

# the name used for a "$keyname.crt" certificate and "$keyname.key" private key.
keyname=${config["keyname"]}

# the public IP address of the VPN server this client should connect with
vpnserver=${config["server"]}

# optional next hop for adding a static route to reach the VPN server
#nexthop="10.0.1.1"

# --------- END CUSTOMIZATION --------

# validate addresses
if [ "$(dpkg -l | grep " sipcalc ")" = "" ]; then
    echo "WARNING: ip validation disabled because package sipcalc not installed
         " > $PWD/vpnclient.log
else
    if [ "$(sipcalc "$vpnserver" "$nexthop" | grep ERR)" != "" ]; then
        echo "ERROR: invalide address $vpnserver or $nexthop " > $PWD/vpnclient.log
    fi
fi

# validate key and certification files
if [ ! -e $keydir\/$keyname.key ] || [ ! -e $keydir\/$keyname.crt ] \
   || [ ! -e $keydir\/ca.crt ] || [ ! -e $keydir\/dh1024.pem ]; then
     echo "ERROR: missing certification or key files under $keydir $keyname.key or $keyname.crt or ca.crt or dh1024.pem" >> $PWD/vpnclient.log
fi

# if necessary, add a static route for reaching the VPN server IP via the IF
vpnservernet=$${}{vpnserver%.*}.0/24
if [ "$nexthop" != "" ]; then
    ip route add $vpnservernet via $nexthop
fi

# create openvpn client.conf
(
cat << EOF
client
dev tun
proto udp
remote $vpnserver 1194
nobind
ca $keydir/ca.crt
cert $keydir/$keyname.crt
key $keydir/$keyname.key
dh $keydir/dh1024.pem
cipher AES-256-CBC
log $PWD/openvpn-client.log
verb 4
daemon
EOF
) > client.conf

openvpn --config client.conf
