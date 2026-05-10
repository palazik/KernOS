# Run KernOS setup on first login
if [ ! -f /tmp/.kernos-setup-done ]; then
    /root/kernos-setup.sh
    touch /tmp/.kernos-setup-done
fi

fastfetch --config /etc/fastfetch/config.jsonc
