#!/bin/sh
# auto-generated by SSH service (utility.py)
ssh-keygen -q -t rsa -N "" -f ${sshcfgdir}/ssh_host_rsa_key
chmod 655 ${sshstatedir}
# wait until RSA host key has been generated to launch sshd
$(which sshd) -f ${sshcfgdir}/sshd_config
