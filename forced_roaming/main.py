#!/usr/bin/python3
"""forced_roaming module provides a mechanism to switch between APs when an
alternative AP is better than the AP the device is currently connected."""
from scan import rescan_for_better_ap
from wt_wrapper import IwCmd

#TODO: this will be taken with parse args
default_wlif = "wlan0"

def disconnect_from_ap(wlif, new_bssid):
    """Disconnect from the currently associated AP."""
    iw = IwCmd(wlif)
    iw.disconnect(True)

def search_for_better_ap_and_switch(wlif):
    """Look for a better AP and disconnect from the current AP hoping that
    connection manager will connect to the better AP"""
    rescan_for_better_ap(wlif, disconnect_from_ap)

if __name__ == "__main__":
    search_for_better_ap_and_switch(default_wlif)
