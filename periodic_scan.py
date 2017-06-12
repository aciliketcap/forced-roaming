#!/usr/bin/python3
from wt_wrapper import IwCmd
import nmcli_wrapper
import argparse

#TODO: implement scan period and debug mode
#TODO: print executed commands and execution times in debug mode

#default values for command arguments
#note that these threshold values are logarithmic!
bad_conn_threshold = -80
diff_from_bad_conn_threshold = -5
diff_threshold = -30
scan_period=60

if __name__=="__main__":
    cmd_parser = argparse.ArgumentParser(description="Do periodic scans on "+
                                         "specified wireless interface and "+
                                         "if a better AP broadcasting the "+
                                         "same SSID is found, connect to it.")
    cmd_parser.add_argument('-w', '--wlif', dest='wlif', type=str,
                            required=True, help="Wireless interface to run "+
                            "scans and make connections on.")
    cmd_parser.add_argument('--bad-threshold', dest='bad_conn_threshold',
                            type=int, help="APs with power below this "+
                            "threshold will be considered bad connections "+
                            "and will be changed as soon as there is a "+
                            "slightly better alternative.",
                            default=bad_conn_threshold)
    cmd_parser.add_argument('--diff-from-bad',
                            dest='diff_from_bad_conn_threshold', type=int,
                            help="An alternative to a bad connection must "+
                            "have this much better power in order for us to "+
                            "switch from current bad connection. If we don't "+
                            "use this then we may go back and forth between "+
                            "two bad connections.",
                            default=diff_from_bad_conn_threshold)
    cmd_parser.add_argument('-t', '--diff-threshold', dest='diff_threshold',
                            type=int, help="An alternative AP must have this "+
                            "much better power in order for us to consider "+
                            "switching to it. If we don't use it we may go "+
                            "back and forth between two APs with similar "+
                            "power.",
                            default=diff_threshold)
    cmd_parser.add_argument('-p', '--period', dest='scan_period', type=int,
                            help="Scan period in seconds.",
                            default=scan_period)
    cmd_parser.add_argument('-o', '--optimized-scan', dest='optimized_scan',
                            help="Scan only on the channel current "+
                            "connection uses. Scans take much less time.",
                            action='store_true')
    args = cmd_parser.parse_args()
    try:
        iw = IwCmd(args.wlif)
        try:
            cur_conn_info = iw.gather_current_connection_info()
        except ValueError as e:
            if e.args[0] == "BSSID":
                print("AP changed while gathering info")
                exit(0)
            else:
                #raise e
                exit(0)

        if cur_conn_info is not None:
            print("Current connection")
            print(cur_conn_info)
            print("==================")

        #try to disable rssi qualiy check before scan
        iw.turn_off_cqm()

        #run scan
        if args.optimized_scan:
            ap_list = iw.gather_ap_info(cur_conn_info.ssid, cur_conn_info.freq)
        else:
            ap_list = iw.gather_ap_info()

        if ap_list is not None:
            if ap_list[1] != cur_conn_info.bssid:
                print("AP changed while gathering info")
                exit(0)
            print("List of current APs")
            for ap in ap_list[0]:
                print(ap)
            print("==================")
            print("current bssid is:", ap_list[1])
            print("current signal / avg signal:", cur_conn_info.signal, "/",
                  cur_conn_info.avg_signal)
        else:
            exit(0)

        #check if there is a better AP with stronger power
        #with matching ssid of course
        same_ssid_aps = sorted(filter(lambda ap: ap.ssid == cur_conn_info.ssid, ap_list[0]),
                         key=lambda ap: ap.signal, reverse=True)
        if len(same_ssid_aps) > 1:
            print("APs broadcasting the SSID", cur_conn_info.ssid, "by power")
            for ap in same_ssid_aps:
                if ap.bssid == cur_conn_info.bssid:
                    print("Current AP:", ap.bssid, ap.signal)
                else:
                    print("Alternative AP:", ap.bssid, ap.signal)

            alt_aps = list(filter(lambda ap: ap.bssid != cur_conn_info.bssid,
                                  same_ssid_aps))

            if cur_conn_info.avg_signal < args.bad_conn_threshold:
                #choose best alternative if connection is already too bad
                if cur_conn_info.signal - alt_aps[0].signal < args.diff_from_bad_conn_threshold:
                    #TODO: Not implemented, just disconnect and hope wireless manager
                    #TODO: connects to the best AP
                    disconnect_cmd()
                    print("Disconnected for a better AP")
            else:
                #only change AP it is significantly better
                if cur_conn_info.signal - alt_aps[0].signal < args.diff_threshold:
                    #TODO: Not implemented, just disconnect and hope wireless manager
                    #TODO: connects to the best AP
                    disconnect_cmd()
                    print("Disconnected for a better AP")
            exit(0)

        else:
            print("Only the connected AP exists with the same SSID!")
            exit(0)
    except AssertionError as e:
        print(" ".join(e.args))
        exit(0)

