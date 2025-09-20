#!/usr/bin/env python3
"""
PSG9080 driver smoke test & demo

Usage examples:
  python test_psg9080.py --port COM5 --ch 1 --freq 10e3 --ampl 1.0
  python test_psg9080.py --port /dev/ttyUSB0 --identify-only

This script performs a conservative configuration on one channel, reads back
key parameters, and (optionally) runs short sweep and modulation demos.
It always turns outputs off on exit.
"""
import argparse
import sys
import time
from typing import Optional

from psg9080_driver import PSG9080, OpenOptions, Waveform, Channel


def parse_args() -> argparse.Namespace:
    wf_names = [w.name.lower() for w in Waveform]
    p = argparse.ArgumentParser(description="PSG9080 smoke test & demo")
    p.add_argument("--port", required=True, help="Serial port (e.g., COM5 or /dev/ttyUSB0)")
    p.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    p.add_argument("--ch", type=int, default=1, choices=[1, 2], help="Channel to exercise (1 or 2)")
    p.add_argument("--freq", type=float, default=1000.0, help="Frequency in Hz (default: 1000)")
    p.add_argument("--ampl", type=float, default=1.0, help="Amplitude Vpp (default: 1.0)")
    p.add_argument("--duty", type=float, default=None, help="Duty cycle in percent (square/pulse)")
    p.add_argument("--phase", type=float, default=None, help="Phase in degrees")
    p.add_argument("--waveform", type=str, default="sine", help=f"Waveform name or code (options: {', '.join(wf_names)} or integer code)")
    p.add_argument("--duration", type=float, default=2.0, help="Time to leave output on (s)")
    p.add_argument("--run-sweep", action="store_true", help="Run a brief sweep demo after basic test")
    p.add_argument("--run-am", action="store_true", help="Run a brief AM modulation demo after basic test")
    p.add_argument("--identify-only", action="store_true", help="Only query device state, do not change config")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args()


def resolve_waveform(s: str) -> int:
    # Accept numeric or name
    try:
        return int(s)
    except ValueError:
        name = s.strip().upper()
        try:
            return int(getattr(Waveform, name))
        except Exception:
            valid = ", ".join(w.name.lower() for w in Waveform)
            raise SystemExit(f"Unknown waveform '{s}'. Valid: {valid} or numeric code")


def log(msg: str, verbose: bool = True) -> None:
    if verbose:
        print(msg)


def identify(psg: PSG9080, verbose: bool = True) -> None:
    # Try reading a few things that do not alter state meaningfully
    try:
        out = psg.get_output()
        log(f"Output states CH1,CH2: {out}", verbose)
        w1 = psg.get_waveform(1)
        w2 = psg.get_waveform(2)
        log(f"Waveforms: CH1={w1}, CH2={w2}", verbose)
        f1 = psg.get_frequency(1)
        f2 = psg.get_frequency(2)
        log(f"Frequencies: CH1={f1:.6f} Hz, CH2={f2:.6f} Hz", verbose)
        a1 = psg.get_amplitude(1)
        a2 = psg.get_amplitude(2)
        log(f"Amplitudes: CH1={a1:.3f} Vpp, CH2={a2:.3f} Vpp", verbose)
    except Exception as e:
        print(f"Identify step failed: {e}")


def basic_test(psg: PSG9080, ch: Channel, freq: float, ampl: float,
               duty: Optional[float], phase: Optional[float], waveform_code: int,
               duration: float, verbose: bool) -> None:
    log("Turning both outputs OFF...", verbose)
    psg.set_output(False, False)

    log(f"Configuring CH{ch} basic parameters...", verbose)
    psg.configure_basic(ch, waveform=waveform_code, frequency_hz=freq,
                        amplitude_vpp=ampl, duty_percent=duty, phase_deg=phase,
                        output_on=False)

    # Readback checks (tolerant)
    rb_f = psg.get_frequency(ch)
    rb_a = psg.get_amplitude(ch)
    log(f"Readback: freq={rb_f:.6f} Hz, ampl={rb_a:.3f} Vpp", verbose)

    if abs(rb_f - freq) / max(freq, 1.0) > 0.01:
        log("WARNING: Frequency readback deviates >1% from requested.", verbose)
    if abs(rb_a - ampl) / max(ampl, 1e-6) > 0.05:
        log("WARNING: Amplitude readback deviates >5% from requested.", verbose)

    if duty is not None:
        rb_d = psg.get_duty(ch)
        log(f"Readback: duty={rb_d:.2f}%", verbose)

    if phase is not None:
        rb_p = psg.get_phase(ch)
        log(f"Readback: phase={rb_p:.2f}°", verbose)

    # Enable just the selected channel
    log(f"Enabling CH{ch} output for {duration} s...", verbose)
    if ch == Channel.CH1:
        psg.set_output(True, False)
    else:
        psg.set_output(False, True)

    time.sleep(max(0.1, duration))

    log("Disabling outputs...", verbose)
    psg.set_output(False, False)


def sweep_demo(psg: PSG9080, ch: Channel, f_start: float, f_end: float, verbose: bool) -> None:
    log("Starting sweep demo (1 s)...", verbose)
    # Keep it simple: set start/end via helper and toggle sweep switch
    psg.set_sweep(ch, sweep_time_ms=1000, direction=2, mode_log=False)
    psg.set_sweep_start_freq(f_start)
    psg.set_sweep_end_freq(f_end)
    psg.set_sweep_vco_switches(sweep_on=True, vco_on=False)
    if ch == Channel.CH1:
        psg.set_output(True, False)
    else:
        psg.set_output(False, True)
    time.sleep(1.2)
    psg.set_sweep_vco_switches(sweep_on=False, vco_on=False)
    psg.set_output(False, False)


def am_demo(psg: PSG9080, ch: Channel, depth: float = 50.0, verbose: bool = True) -> None:
    log("Starting AM demo (2 s)...", verbose)
    # Mod type AM on selected channel, internal source, 1 kHz mod
    if ch == Channel.CH1:
        psg.set_mod_types(ch1=0, ch2=0)  # AM on CH1; CH2 unchanged
        psg.set_mod_source_internal(True, True)
        psg.set_ch1_mod_freq(1000.0)
        psg.set_ch1_am_depth(depth)
        psg.set_output(True, False)
    else:
        psg.set_mod_types(ch1=0, ch2=0)  # AM on CH2 as well
        psg.set_mod_source_internal(True, True)
        psg.set_ch2_mod_freq(1000.0)
        psg.set_ch2_am_depth(depth)
        psg.set_output(False, True)
    time.sleep(2.0)
    psg.set_output(False, False)


def main() -> int:
    args = parse_args()
    ch = Channel.CH1 if args.ch == 1 else Channel.CH2
    waveform_code = resolve_waveform(args.waveform)

    opts = OpenOptions(port=args.port, baudrate=args.baud, timeout=0.8)
    with PSG9080(opts) as psg:
        # Initial quick probe
        identify(psg, verbose=args.verbose)

        if args.identify_only:
            return 0

        try:
            basic_test(psg, ch, args.freq, args.ampl, args.duty, args.phase,
                       waveform_code, args.duration, args.verbose)

            if args.run_sweep:
                sweep_demo(psg, ch, f_start=max(1.0, args.freq / 10.0), f_end=args.freq * 10.0, verbose=args.verbose)

            if args.run_am:
                am_demo(psg, ch, depth=50.0, verbose=args.verbose)

        finally:
            # Always make sure outputs are off
            try:
                psg.set_output(False, False)
            except Exception:
                pass

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
