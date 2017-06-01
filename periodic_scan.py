#!/usr/bin/python3
from wt_wrapper import IwCmd
import nmcli_wrapper

#TODO: Properly package this script into a class
#TODO: and get the conf values during init
#TODO: or take them using getopt
wlif = "wlp8s0"
#note that these threshold values are logarithmic!
bad_conn_threshold = -80
diff_from_bad_conn_threshold = -5
diff_threshold = -30

if __name__=="__main__":
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
                    #TODO: Not implemented, just disconnect and hope wireless manager
                    #TODO: connects to the best AP
                    disconnect_cmd()
                    print("Disconnected for a better AP")
            else:
                #only change AP it is significantly better
                if cur_conn_info.signal - alt_aps[0].signal < diff_threshold:
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

