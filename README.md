forced_roaming package provides a mechanism to switch between APs when an
alternative AP is better than the AP the device is currently connected.

Use it as "python3 -m forced_roaming -w WLIF".
You can read help with "python3 -m forced_roaming --help".

It first records the strength of currently connected AP. Then it does a scan
and records the strengths of the APs with the same SSID as the connected AP.
If the strength of current AP is bad (--bad-threshold) and there exists a
better alternative (--diff-from-bad) it disconnects from the current AP. If
the strength of another alternative AP is much better (--diff-threshold) than
the current AP it again disconnects. (And hopefully the wireless
manager of the system will connect to the better alternative.)

If optimized scan is enabled (--optimized-scan) then the scan will be done
only on the channel current connection is on. (And therefore will take only
a fraction of time. Useful if we know that all the alternative APs are
configured to broadcast on the same channel.)

It can be run from a script or a cron job to periodically scan latest status.

Current state of the package is quite basic and it is based on some strong
assumptions. The device must be connected to an AP when the package is run.
All the alternative APs must have the same SSID as the AP the device is
currently connected to. There should be a program managing the wireless
networks (like NetworkManager), it must try to connect to the best AP when
current AP is disconnected and it must be able to associate with alternative
APs.

Features I'd like to add:
- Using NetworkManager (via nmcli interface) to force association with chosen
AP. (Instead of disconnecting and hoping that a wireless manager will connect
to the one we have chosen.)
- Listening to 'iw event' and responding to wireless events immediately.
- We should be able to give a list of APs to use instead of looking for APs
with the same SSID as the currently connected one.
- Running the whole thing like a deamon and periodically running the mechanism
above can be desired. But I'm not sure.
