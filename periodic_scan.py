#!/usr/bin/python3

#TODO: Do I need to parse stderr or does iw set return code accordingly?
#TODO: Does connection info commands also fail with busy?
#TODO: If we get busy error we should retry after a short timeout!

import subprocess
import re

#conf
my_wlif = "wlp3s0"

def link_cmd(wlif):
    return "sudo iw dev " + wlif + " link"

def station_dump_cmd(wlif):
    return "sudo iw dev " + wlif + " station dump"

def turn_off_cqm_cmd(wlif):
    return "sudo iw dev " + wlif + " cqm rssi off"

def scan_cmd(wlif, ssid="", freq=0):
    base_scan_cmd = "sudo iw dev " + wlif + " scan flush"
    if freq == 0 and ssid == "":
        return base_scan_cmd
    elif freq == 0:
        return base_scan_cmd + " ssid " + ssid
    elif ssid == "":
        return base_scan_cmd + " freq " + freq
    else:
        return base_scan_cmd + " ssid " + ssid + " freq " + freq

def cmd_run(cmd_string):
    try:
        result = subprocess.run(cmd_string.split(' '), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=True)
        return result.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        raise e


match_mac = r"([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})"
match_power = r"((-)?\d+(\.\d+)?) dBm"

match_link_failed = r"Not connected."
match_iw_no_device = r"^command failed: No such device"
match_iw_busy = r="^command failed: Device or resource busy"
match_bssid_from_link = r"Connected to (" + match_mac + ")"
#writing regex for SSID can be quite tricky, just read until EOL
match_ssid_from_link = r"\s+SSID:\s+(.*)$"
match_freq_from_link = r"\s+freq:\s+(\d*)"
match_bssid_from_station_dump = r"Station\s+(" + match_mac + ")"
match_signal = r"\s+signal:\s+(" + match_power +")"
match_avg_signal = r"\s+signal avg:\s+(" + match_power +")"
match_bssid_from_scan = r"^BSS (" + match_mac + ")"
match_is_cur_bssid_from_scan = r"^BSS.*associated$"

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

class ApInfo:
    def __init__(self, bssid, ssid, freq, signal):
        assert bssid is not None, "No bssid"
        self.bssid = bssid
        assert ssid is not None, "No ssid"
        self.ssid = ssid
        assert freq is not None, "No freq"
        self.freq = freq
        assert signal is not None, "No signal"
        self.signal = signal
    def __str__(self):
        return "\n".join(["BSSID: " + self.bssid,
                "SSID: " + self.ssid,
                "Freq: " + self.freq,
                "Signal: " + self.signal])

def handle_iw_cmd_error(e):
    assert e is subprocess.CalledProcessError
    if re.match(match_iw_busy, e.stderr.decode("utf-8")):
        print("Got busy error, retrying...")
        #retry
        return True
    else:
        print("iw command failed:", " ".join(e.cmd))
        if re.match(match_iw_no_device, e.stderr.decode("utf-8")):
            print("Device", wlif, "not found!")
        else:
            print("With output:", e.stderr)
        return False

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
            continue

        res_freq = re.match(match_freq_from_link, l)
        if res_freq is not None:
            freq = res_freq.groups()[0]

    assert ssid, "No ssid"
    assert freq, "No freq"

    for l in station_dump_output.splitlines()[1:]:
        res_signal = re.match(match_signal, l)
        if res_signal:
            signal = res_signal.groups()[0]
            continue

        res_avg_signal = re.match(match_avg_signal, l)
        if res_avg_signal:
            avg_signal = res_avg_signal.groups()[0]

    assert signal, "No signal"
    assert avg_signal, "No average signal"

    return ConnInfo(bssid_from_link, ssid, freq, signal, avg_signal)

def add_last_ap(list, bssid, ssid, freq, signal):
    try:
        list.append(ApInfo(bssid, ssid, freq, signal))
    except AssertionError as e:
        print("Could not add one AP:", " ".join(e.args))
    finally:
        bssid, freq, signal, ssid = [None]*4

def parse_ap_info(scan_output):
    if len(scan_output) == 0:
        print("No APs found!")
        return

    current_bssid = None
    bssid, freq, signal, ssid = [None]*4
    ap_list = []

    for l in scan_output.splitlines():
        res_bssid_from_scan = re.match(match_bssid_from_scan, l)
        if res_bssid_from_scan is not None:
            if bssid is not None:
                add_last_ap(ap_list, bssid, ssid, freq, signal)
            bssid = res_bssid_from_scan.groups()[0]
            res_current_ap = re.match(match_is_cur_bssid_from_scan, l)
            if res_current_ap is not None:
                current_bssid = bssid
            continue

        res_freq = re.match(match_freq_from_link, l)
        if res_freq is not None:
            freq = res_freq.groups()[0]
            continue

        res_signal = re.match(match_signal, l)
        if res_signal is not None:
            signal = res_signal.groups()[0]
            continue

        res_ssid = re.match(match_ssid_from_link, l)
        if res_ssid is not None:
            ssid = res_ssid.groups()[0]
            continue

    add_last_ap(ap_list, bssid, ssid, freq, signal)
    return ap_list, current_bssid


def gather_current_connection_info(wlif):
    #TODO: make this loop a decorator if possible
    while True:
        try:
            link_out = cmd_run(link_cmd(my_wlif))
            station_dump_out = cmd_run(station_dump_cmd(my_wlif))
            break
        except subprocess.CalledProcessError as e:
            if not handle_iw_cmd_error(e):
                return

    return parse_current_connection_info(link_out, station_dump_out)

def gather_ap_info(wlif, ssid="", freq=0):
    while True:
        try:
            scan_out = cmd_run(scan_cmd(wlif, ssid, freq))
            break
        except subprocess.CalledProcessError as e:
            if not handle_iw_cmd_error(e):
                return

    return parse_ap_info(scan_out)

#TODO: below should form the main function
cur_conn_info = gather_current_connection_info(my_wlif)
if cur_conn_info is not None:
    print(cur_conn_info)

#try to disable rssi qualiy check before scan
try:
    cmd_run(turn_off_cqm_cmd(my_wlif))
except subprocess.CalledProcessError as e:
    print("iw command failed:", " ".join(e.cmd))
    print("with output:", e.stderr)

#run scan
ap_list = gather_ap_info(my_wlif)
if ap_list is not None:
    for ap in ap_list[0]:
        print(ap)
    print("current bssid is:", ap_list[1])







