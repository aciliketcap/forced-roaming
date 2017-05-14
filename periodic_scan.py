#!/usr/bin/python3

#TODO: need to handle exception and write negative code

import subprocess
import re

#conf
my_wlif = "wlp3s0"

def link_cmd(wlif):
    return "sudo iw dev " + wlif + " link"

def station_dump_cmd(wlif):
    return "sudo iw dev " + wlif + " station dump"

def cmd_run(cmd_string):
    try:
        result = subprocess.run(cmd_string.split(' '), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=True)
        return result.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        raise e


match_mac = r"([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})"
match_power = r"((-)?\d+) dBm"

match_link_failed = r"Not connected."
match_iw_no_device = r"^command failed: No such device"
match_bssid_from_link = r"Connected to (" + match_mac + ")"
#writing regex for SSID can be quite tricky, just read until EOL
match_ssid_from_link = r"\s+SSID:\s+(.*)$"
match_freq_from_link = r"\s+freq:\s+(\d*)"
match_bssid_from_station_dump = r"Station\s+(" + match_mac + ")"
match_signal = r"\s+signal:\s+(" + match_power +")"
match_avg_signal = r"\s+signal avg:\s+(" + match_power +")"

class ConnInfo:
    def __init__(self, bssid, ssid, freq, signal, avg_signal):
        self.bssid = bssid
        self.ssid = ssid
        self.freq = freq
        self.signal = signal
        self.avg_signal = avg_signal
    def __str__(self):
        return "\n".join(["BSSID: " + self.bssid,
                "SSID: " + self.ssid,
                "Freq: " + self.freq,
                "Signal: " + self.signal,
                "Avg Signal: " + self.avg_signal])

def parse_current_connection_info(link_output, station_dump_output):
    assert re.match(match_link_failed, link_output) is None, "Not connected"
    assert len(station_dump_output) > 0, "Not connected"

    res_bssid_from_link = re.match(match_bssid_from_link, link_output)
    assert res_bssid_from_link is not None, "No bssid from link command"
    bssid_from_link = res_bssid_from_link.groups()[0]

    res_bssid_from_station_dump = re.match(match_bssid_from_station_dump,
                                       station_dump_output)
    assert res_bssid_from_station_dump is not None, "No bssid from station dump command"
    bssid_from_station_dump = res_bssid_from_station_dump.groups()[0]

    if bssid_from_station_dump != bssid_from_link:
        raise ValueError("BSSID's from two commands does not match!")

    for l in link_output.splitlines()[1:]:
        res_ssid = re.match(match_ssid_from_link, l)
        if res_ssid is not None:
            ssid = res_ssid.groups()[0]

        res_freq = re.match(match_freq_from_link, l)
        if res_freq is not None:
            freq = res_freq.groups()[0]

    assert ssid, "No ssid"
    assert freq, "No freq"

    for l in station_dump_output.splitlines()[1:]:
        res_signal = re.match(match_signal, l)
        if res_signal:
            signal = res_signal.groups()[0]

        res_avg_signal = re.match(match_avg_signal, l)
        if res_avg_signal:
            avg_signal = res_avg_signal.groups()[0]

    assert signal, "No signal"
    assert avg_signal, "No average signal"

    return ConnInfo(bssid_from_link, ssid, freq, signal, avg_signal)

def gather_current_connection_info(wlif):
    try:
        link_out = cmd_run(link_cmd(my_wlif))
        station_dump_out = cmd_run(station_dump_cmd(my_wlif))
    except subprocess.CalledProcessError as e:
        print("iw command failed:", " ".join(e.cmd))
        if re.match(match_iw_no_device, e.stderr.decode("utf-8")):
            print("Device", wlif, "not found!")
        else:
            print("With output:", e.stderr)
        return

    return parse_current_connection_info(link_out, station_dump_out)

#control output
cur_conn_info = gather_current_connection_info(my_wlif)
if cur_conn_info is not None:
    print(cur_conn_info)



