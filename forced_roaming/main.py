#!/usr/bin/python3
"""forced_roaming module provides a mechanism to switch between APs when an
alternative AP is better than the AP the device is currently connected."""
import argparse
from scan import rescan_for_better_ap
from wt_wrapper import IwCmd

#default values for command arguments
default_bad_conn_threshold = -80
default_diff_from_bad_conn_threshold = -5
default_diff_threshold = -30
default_scan_period=60

def disconnect_from_ap(wlif, new_bssid):
    """Disconnect from the currently associated AP."""
    iw = IwCmd(wlif)
    iw.disconnect(True)

def search_for_better_ap_and_switch(wlif,
                                    optimized_scan,
                                    bad_conn_threshold,
                                    diff_from_bad_conn_threshold,
                                    diff_threshold):
    """Look for a better AP and disconnect from the current AP hoping that
    connection manager will connect to the better AP"""
    rescan_for_better_ap(wlif,
                         disconnect_from_ap,
                         optimized_scan,
                         bad_conn_threshold,
                         diff_from_bad_conn_threshold,
                         diff_threshold)

if __name__ == "__main__":
    wlif = None
    bad_conn_threshold = None
    diff_from_bad_conn_threshold = None
    diff_threshold = None
    scan_period = None
    optimized_scan = None

    cmd_parser = argparse.ArgumentParser(
        description="Do periodic scans on specified wireless interface and "+
        "if a better AP broadcasting the same SSID is found, connect to it.")
    cmd_parser.add_argument(
        '-w', '--wlif', dest='wlif', type=str, required=True,
        help="Wireless interface to run scans and make connections on.")
    cmd_parser.add_argument(
        '--bad-threshold', dest='bad_conn_threshold', type=int,
        default=default_bad_conn_threshold,
        help="APs with power below this threshold will be considered bad "+
        "connections and will be changed as soon as there is a slightly "+
        "better alternative.")
    cmd_parser.add_argument(
        '--diff-from-bad', dest='diff_from_bad_conn_threshold', type=int,
        default=default_diff_from_bad_conn_threshold,
        help="An alternative to a bad connection must have this much better "+
        "power in order for us to switch from current bad connection. If we "+
        "don't use this then we may go back and forth between two bad "+
        "connections.")
    cmd_parser.add_argument(
        '-t', '--diff-threshold', dest='diff_threshold', type=int,
        default=default_diff_threshold,
        help="An alternative AP must have this much better power in order "+
        "for us to consider switching to it. If we don't use it we may go "+
        "back and forth between two APs with similar power.")
    cmd_parser.add_argument(
        '-p', '--period', dest='scan_period', type=int,
        default=default_scan_period,
        help="Scan period in seconds.")
    cmd_parser.add_argument(
        '-o', '--optimized-scan', dest='optimized_scan',
        help="Scan only on the channel current connection uses. Scans will "+
        "take less time.",
        action='store_true')
    args = cmd_parser.parse_args()
    if wlif is not None:
        search_for_better_ap_and_switch(wlif,
                                        optimized_scan,
                                        bad_conn_threshold,
                                        diff_from_bad_conn_threshold,
                                        diff_threshold)
