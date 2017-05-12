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
    result = subprocess.run(cmd_string.split(' '), stdout=subprocess.PIPE, check=True)
    return result.stdout.decode("utf-8")

match_mac = r"([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})"
match_power = r"((-)?\d+) dBm"

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

#throw instead of returning None in negative code
def parse_current_connection_info(link_output, station_dump_output):
    res_bssid_from_link = re.match(match_bssid_from_link, link_output)
    if res_bssid_from_link is not None:
        bssid_from_link = res_bssid_from_link.groups()[0]
    else:
        raise ValueError("No bssid from link command")

    res_bssid_from_station_dump = re.match(match_bssid_from_station_dump,
                                       station_dump_output)
    if res_bssid_from_station_dump is not None:
        bssid_from_station_dump = res_bssid_from_station_dump.groups()[0]
    else:
        raise ValueError("No bssid from station dump command")

    if bssid_from_station_dump != bssid_from_link:
        raise ValueError("BSSID's from commands does not match!")

    for l in link_output.splitlines()[1:]:
        res_ssid = re.match(match_ssid_from_link, l)
        if res_ssid is not None:
            ssid = res_ssid.groups()[0]

        res_freq = re.match(match_freq_from_link, l)
        if res_freq is not None:
            freq = res_freq.groups()[0]

    try:
        ssid
    except:
        raise ValueError("No ssid")
    try:
        freq
    except:
        raise ValueError("No freq")

    for l in station_dump_output.splitlines()[1:]:
        res_signal = re.match(match_signal, l)
        if res_signal:
            signal = res_signal.groups()[0]

        res_avg_signal = re.match(match_avg_signal, l)
        if res_avg_signal:
            avg_signal = res_avg_signal.groups()[0]

    try:
        signal
    except:
        raise ValueError("No signal")
    try:
        avg_signal
    except:
        raise ValueError("No avg signal")

    return ConnInfo(bssid_from_link, ssid, freq, signal, avg_signal)

def gather_current_connection_info(wlif):
    link_out = cmd_run(link_cmd(my_wlif))
    station_dump_out = cmd_run(station_dump_cmd(my_wlif))

    return parse_current_connection_info(link_out, station_dump_out)


#control output
print(gather_current_connection_info(my_wlif))



