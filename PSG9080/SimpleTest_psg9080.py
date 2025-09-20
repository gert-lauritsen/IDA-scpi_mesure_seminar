# -*- coding: utf-8 -*-
"""
Created on Sat Sep 20 19:45:11 2025

@author: gert
"""

"""
Simple test script for PSG9080 driver without argparse.

Edit the CONFIG section below to match your setup.
"""

from time import sleep
from psg9080_driver import PSG9080, OpenOptions, Waveform, Channel

# ------------------- CONFIG -------------------
PORT = "COM5"          # serial port
CHANNEL = Channel.CH1  # Channel.CH1 or Channel.CH2
FREQ_HZ = 100000        # frequency in Hz
AMPL_VPP = 1.0         # amplitude in Vpp
DUTY = None            # e.g. 50.0 for 50% duty (square/pulse)
PHASE = None           # e.g. 0.0 for 0 degrees
# -----------------------------------------------


def main():
    opts = OpenOptions(port=PORT, baudrate=115200, timeout=1.0)

    with PSG9080(opts) as psg:
        print("Querying initial states...")
        print("Outputs:", psg.get_output())
        print("Waveforms:", psg.get_waveform(Channel.CH1), psg.get_waveform(Channel.CH2))
        print("Frequencies:", psg.get_frequency(Channel.CH1), psg.get_frequency(Channel.CH2))
        print("Amplitudes:", psg.get_amplitude(Channel.CH1), psg.get_amplitude(Channel.CH2))

        print("Turning both outputs OFF...")
        psg.set_output(False, False)
        sleep(0.1)

        print(f"Configuring {CHANNEL.name} to {FREQ_HZ} Hz, {AMPL_VPP} Vpp...")
        psg.configure_basic(CHANNEL,
                            waveform=Waveform.SINE,
                            frequency_hz=FREQ_HZ,
                            amplitude_vpp=AMPL_VPP,
                            duty_percent=DUTY,
                            phase_deg=PHASE,
                            output_on=True)

        sleep(0.2)

        print("Reading back settings...")
        rb_f = psg.get_frequency(CHANNEL)
        rb_a = psg.get_amplitude(CHANNEL)
        print(f"Channel {CHANNEL.name} frequency: {rb_f} Hz")
        print(f"Channel {CHANNEL.name} amplitude: {rb_a} Vpp")

        print("Test complete, turning outputs OFF...")
        psg.set_output(False, False)


if __name__ == "__main__":
    main()
