"""scan module provides a mechanism to scan APs and then decide whether to
disconnect from the current AP or continue with current one."""
from .iw_wrapper import IwCmd
#TODO: implement debug mode
#TODO: print executed commands and execution times in debug mode

def rescan_for_better_ap(wlif,
                         switch_ap_func,
                         optimized_scan,
                         bad_conn_threshold,
                         diff_from_bad_conn_threshold,
                         diff_threshold):
    #note that threshold values are logarithmic!
    try:
        iw = IwCmd(wlif)
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
        if optimized_scan:
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

            if cur_conn_info.avg_signal < bad_conn_threshold:
                #choose best alternative if connection is already too bad
                if cur_conn_info.signal - alt_aps[0].signal < diff_from_bad_conn_threshold:
                    print("Found a better AP:", alt_aps[0].bssid,
                          "Trying to switch.")
                    switch_ap_func(wlif, alt_aps[0].bssid)
            else:
                #only change AP it is significantly better
                if cur_conn_info.signal - alt_aps[0].signal < diff_threshold:
                    print("Found a better AP:", alt_aps[0].bssid,
                          "Trying to switch.")
                    switch_ap_func(wlif, alt_aps[0].bssid)
            exit(0)

        else:
            print("Only the connected AP exists with the same SSID!")
            exit(0)
    except AssertionError as e:
        print(" ".join(e.args))
        exit(0)
