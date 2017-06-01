#!/usr/bin/python3

#TODO: Do I need to parse stderr or does iw set return code accordingly?
#TODO: Does connection info commands also fail with busy?
#TODO: If we get busy error we should retry after a short timeout!

import re
import subprocess
from cmd import Cmd

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
                "Signal: " + str(self.signal),
                "Avg Signal: " + str(self.avg_signal)])

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
                "Signal: " + str(self.signal)])

class IwCmd(Cmd):
    def __init__(self, wlif):
        self.wlif = wlif
        self.dev_cmd = "sudo iw dev " + wlif

    #regex for parsing iw cmd output
    match_mac = r"([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})"
    match_power = r"((-)?\d+(\.\d+)?) dBm"

    match_link_failed = r"Not connected."
    match_iw_no_device = r"^command failed: No such device"
    match_iw_busy = r"^command failed: Device or resource busy"
    match_bssid_from_link = r"Connected to (" + match_mac + ")"
    #writing regex for SSID can be quite tricky, just read until EOL
    match_ssid_from_link = r"\s+SSID:\s+(.*)$"
    match_freq_from_link = r"\s+freq:\s+(\d*)"
    match_bssid_from_station_dump = r"Station\s+(" + match_mac + ")"
    match_signal = r"\s+signal:\s+(" + match_power +")"
    match_avg_signal = r"\s+signal avg:\s+(" + match_power +")"
    match_bssid_from_scan = r"^BSS (" + match_mac + ")"
    match_is_cur_bssid_from_scan = r"^BSS.*associated$"

    #shell command execution mechanism
    def run_with_retry_flag(self, iw_cmd, retry = False):
        while True:
            try:
                out = self.run(iw_cmd)
                break
            except subprocess.CalledProcessError as e:
                if retry:
                    if re.match(self.match_iw_busy, e.stderr.decode("utf-8")):
                        print("Got busy error, retrying...")
                        continue
                print("iw command failed:", " ".join(e.cmd))
                if re.match(self.match_iw_no_device, e.stderr.decode("utf-8")):
                    print("Device", self.wlif, "not found!")
                else:
                    print("With output:", e.stderr)
                return
        return out

    def link(self, retry = False):
        return self.run_with_retry_flag(self.dev_cmd + " link", retry)

    def station_dump(self, retry = False):
        return self.run_with_retry_flag(self.dev_cmd + " station dump", retry)

    def turn_off_cqm(self, retry = False):
        return self.run_with_retry_flag(self.dev_cmd + " cqm rssi off", retry)

    def scan(self, ssid="", freq=0, retry = False):
        base_scan_cmd = self.dev_cmd + " scan flush"
        if freq == 0 and ssid == "":
            return self.run_with_retry_flag(base_scan_cmd, retry)
        elif freq == 0:
            return self.run_with_retry_flag(base_scan_cmd + " ssid " + ssid, retry)
        elif ssid == "":
            return self.run_with_retry_flag(base_scan_cmd + " freq " + freq, retry)
        else:
            return self.run_with_retry_flag(base_scan_cmd + " ssid " + ssid + " freq " +
                                  freq, retry)

    def disconnect(self, retry = False):
        return self.run_with_retry_flag(self.dev_cmd + " disconnect", retry)

    #parse output using regex
    def parse_current_connection_info(self, link_output, station_dump_output):
        print(link_output)
        assert re.match(self.match_link_failed, link_output) is None, "Not connected"
        assert len(station_dump_output) > 0, "Not connected"

        res_bssid_from_link = re.match(self.match_bssid_from_link, link_output)
        assert res_bssid_from_link is not None, "No bssid from link command"
        bssid_from_link = res_bssid_from_link.groups()[0]

        res_bssid_from_station_dump = re.match(self.match_bssid_from_station_dump,
                                           station_dump_output)
        assert res_bssid_from_station_dump is not None, "No bssid from station dump command"
        bssid_from_station_dump = res_bssid_from_station_dump.groups()[0]

        if bssid_from_station_dump != bssid_from_link:
            raise ValueError("BSSID's from two commands does not match!")

        for l in link_output.splitlines()[1:]:
            res_ssid = re.match(self.match_ssid_from_link, l)
            if res_ssid is not None:
                ssid = res_ssid.groups()[0]
                continue

            res_freq = re.match(self.match_freq_from_link, l)
            if res_freq is not None:
                freq = res_freq.groups()[0]

        if 'ssid' not in locals():
            raise AssertionError("No ssid")
        if 'freq' not in locals():
            raise AssertionError("No freq")

        for l in station_dump_output.splitlines()[1:]:
            res_signal = re.match(self.match_signal, l)
            if res_signal:
                signal = int(res_signal.groups()[1])
                continue

            res_avg_signal = re.match(self.match_avg_signal, l)
            if res_avg_signal:
                avg_signal = int(res_avg_signal.groups()[1])

        if 'signal' not in locals():
            raise AssertionError("No signal")
        if 'avg_signal' not in locals():
            raise AssertionError("No average signal")

        return ConnInfo(bssid_from_link, ssid, freq, signal, avg_signal)

    def add_ap_to_list(self, list, bssid, ssid, freq, signal):
        try:
            list.append(ApInfo(bssid, ssid, freq, signal))
        except AssertionError as e:
            print("Could not add one AP:", " ".join(e.args))
        finally:
            bssid, freq, signal, ssid = [None]*4

    def parse_ap_info(self, scan_output):
        if len(scan_output) == 0:
            print("No APs found!")
            return

        current_bssid = None
        bssid, freq, signal, ssid = [None]*4
        ap_list = []

        for l in scan_output.splitlines():
            res_bssid_from_scan = re.match(self.match_bssid_from_scan, l)
            if res_bssid_from_scan is not None:
                if bssid is not None:
                    self.add_ap_to_list(ap_list, bssid, ssid, freq, signal)
                bssid = res_bssid_from_scan.groups()[0]
                res_current_ap = re.match(self.match_is_cur_bssid_from_scan, l)
                if res_current_ap is not None:
                    current_bssid = bssid
                continue

            res_freq = re.match(self.match_freq_from_link, l)
            if res_freq is not None:
                freq = res_freq.groups()[0]
                continue

            res_signal = re.match(self.match_signal, l)
            if res_signal is not None:
                signal = int(float(res_signal.groups()[1]))
                continue

            res_ssid = re.match(self.match_ssid_from_link, l)
            if res_ssid is not None:
                ssid = res_ssid.groups()[0]
                continue

        self.add_ap_to_list(ap_list, bssid, ssid, freq, signal)
        return ap_list, current_bssid

    #run commands, parse output into data classes
    def gather_current_connection_info(self):
        link_out = self.link(True)
        assert link_out is not None, "Unable to read current link"

        station_dump_out = self.station_dump(True)
        assert station_dump_out is not None, "Unable to dump station"

        return self.parse_current_connection_info(link_out, station_dump_out)

    def gather_ap_info(self, ssid="", freq=0):
        return self.parse_ap_info(self.scan(ssid, freq, True))

