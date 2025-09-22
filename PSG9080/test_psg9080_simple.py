# -*- coding: utf-8 -*-
"""
Created on Sat Sep 20 19:52:32 2025

@author: Gert Lauritsen
"""

"""
Simple PSG9080 test (no argparse).

Edit CONFIG below, then run:  python test_psg9080_simple.py
"""

import time
from psg9080_driver import PSG9080, OpenOptions, Waveform, Channel

# ------------------- CONFIG -------------------
PORT = "COM5"            # e.g., "COM5" or "/dev/ttyUSB0"
CHANNEL = Channel.CH1    # Channel.CH1 or Channel.CH2
FREQ_HZ = 1000        # target frequency in Hz
AMPL_VPP = 1.0           # amplitude in Vpp
DUTY = None              # e.g., 50.0 for 50% duty (square/pulse)
PHASE = None             # e.g., 0.0 for 0 degrees
# ------------------------------------------------


def verify_with_retry(psg: PSG9080, ch: Channel, want_hz: float, want_vpp: float, tries: int = 3):
    """Read back frequency/amplitude with a short retry window."""
    last_f = None
    last_a = None
    for i in range(tries):
        time.sleep(0.05 if i == 0 else 0.15)  # tiny settle, then slightly longer
        last_f = psg.get_frequency(ch)
        last_a = psg.get_amplitude(ch)
        ok_f = abs(last_f - want_hz) <= max(1.0, 0.01 * want_hz)  # within 1% or 1 Hz
        ok_a = abs(last_a - want_vpp) <= max(0.01, 0.05 * want_vpp)  # within 5% or 10 mV
        if ok_f and ok_a:
            break
    return last_f, last_a


def main():
    # Show which driver file you’re importing (avoid stale copy)
    import psg9080_driver as drv
    print("Driver path:", getattr(drv, "__file__", "<unknown>"))

    opts = OpenOptions(port=PORT, baudrate=115200, timeout=1.0)
    with PSG9080(opts) as psg:
        print("Querying initial states...")
        print("Outputs:", psg.get_output())
        print("Waveforms:", psg.get_waveform(Channel.CH1), psg.get_waveform(Channel.CH2))
        print("Frequencies:", psg.get_frequency(Channel.CH1), psg.get_frequency(Channel.CH2))
        print("Amplitudes:", psg.get_amplitude(Channel.CH1), psg.get_amplitude(Channel.CH2))

        print("Turning both outputs OFF...")
        psg.set_output(False, False)
        time.sleep(0.1)

        # Configure order & tiny settle between steps (some firmware needs breaths)
        print(f"Configuring {CHANNEL.name} to {FREQ_HZ} Hz, {AMPL_VPP} Vpp...")
        psg.set_waveform(CHANNEL, Waveform.SINE)
        time.sleep(0.03)

        psg.set_frequency(CHANNEL, FREQ_HZ)
        time.sleep(0.05)

        psg.set_amplitude(CHANNEL, AMPL_VPP)
        time.sleep(0.03)

        if DUTY is not None:
            psg.set_duty(CHANNEL, DUTY)
            time.sleep(0.02)

        if PHASE is not None:
            psg.set_phase(CHANNEL, PHASE)
            time.sleep(0.02)

        # Enable only selected channel
        if CHANNEL == Channel.CH1:
            psg.set_output(True, False)
        else:
            psg.set_output(False, True)

        # Verify with a small retry (the CLI script effectively gives this time “for free”)
        rb_f, rb_a = verify_with_retry(psg, CHANNEL, FREQ_HZ, AMPL_VPP)
        print(f"Readback: {CHANNEL.name} frequency: {rb_f} Hz, amplitude: {rb_a} Vpp")


        HOLD_SECONDS = 10  # keep output on this long
        print(f"Holding output ON for {HOLD_SECONDS} seconds...")
        time.sleep(HOLD_SECONDS)

        print("Test complete, turning outputs OFF...")
        psg.set_output(False, False)


if __name__ == "__main__":
    main()
