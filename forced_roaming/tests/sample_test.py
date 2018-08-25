from unittest import TestCase

from forced_roaming import iw_wrapper

def run_with_retry_flag_for_sample(cmd, flag):
    cmds = cmd.split()
    print(cmds)
    if cmds[-1] == 'link':
        with open("link.good.out") as file:
            return file.read()
    elif cmds[-1] == 'dump':
        with open("station_dump.good.out") as file:
            return file.read()
    else:
        raise AssertionError

class SampleTest(TestCase):
    def simple_parse_test(self):
        iw = iw_wrapper.IwCmd("wlan0")
        iw.run_with_retry_flag = run_with_retry_flag_for_sample
        cur_conn_info = iw.gather_current_connection_info()
        print(cur_conn_info)
        self.assertEqual(cur_conn_info.bssid, "aa:aa:aa:aa:aa:00")
        self.assertEqual(cur_conn_info.ssid, "test")
        self.assertEqual(cur_conn_info.freq, "2417")
        self.assertEqual(cur_conn_info.signal, -20)
        self.assertEqual(cur_conn_info.avg_signal, -21)
