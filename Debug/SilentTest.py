# -*- coding: utf-8 -*-
"""
Created on Sat Sep 20 16:55:25 2025

@author: gert
"""

import time
import numpy as np
import pyvisa
from pyvisa import constants as pv, errors as pv_errors

# ==== USER CONFIG ====
CHANNEL              = "C1"        # C1..C4
TIMEBASE_S_PER_DIV   = 1e-6        # 1 µs/div
SAMPLE_RATE          = 500e6       # 500 MSa/s
TRIG_LEVEL_V         = 0.5
TRIG_SOURCE          = "C1"
POINTS_TO_READ       = None        # None -> instrument default
CSV_PATH             = "sds824_capture.csv"
NPY_PATH             = "sds824_capture.npy"

# ==== HELPERS ====
def read_block(session):
    raw = session.read_raw()
    h = raw.find(b'#')
    if h < 0:
        raise RuntimeError("No SCPI block header found")
    ndigits = int(raw[h+1:h+2])
    nbytes = int(raw[h+2:h+2+ndigits])
    start = h + 2 + ndigits
    return raw[start:start+nbytes]

def parse_preamble_block(pre_bin):
    def f32(off): return np.frombuffer(pre_bin[off:off+4], dtype='<f4')[0]
    def s16(off): return np.frombuffer(pre_bin[off:off+2], dtype='<i2')[0]
    def f64(off): return np.frombuffer(pre_bin[off:off+8], dtype='<f8')[0]
    return dict(
        vdiv=f32(156),
        voffset=f32(160),
        code_per_div=f32(164),
        adc_bits=s16(172),
        dt=f32(176),
        delay=f64(180),
    )

def to_volts(code_bytes, vdiv, code_per_div, voffset, adc_bits, is_word=True):
    if is_word:
        data = np.frombuffer(code_bytes, dtype='>i2').astype(np.int32)
        shift = 16 - int(adc_bits)
        data = (data >> shift).astype(np.int32)
        full = 1 << int(adc_bits)
        center = full // 2
        data[data >= center] -= full
        code_signed = data.astype(np.float64)
    else:
        data = np.frombuffer(code_bytes, dtype=np.uint8).astype(np.int16)
        center = 128
        data[data >= center] -= 256
        code_signed = data.astype(np.float64)
    return code_signed * (vdiv / code_per_div) - voffset

def polite_flush(scope):
    try:
        scope.timeout = 100
        try:
            _ = scope.read_raw()
        except Exception:
            pass
        try:
            scope.flush(pv.BufferOperation.discard_read_buffer)
            scope.flush(pv.BufferOperation.discard_write_buffer)
        except Exception:
            pass
    finally:
        time.sleep(0.05)

# ==== MAIN ====
def main():
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    if not resources:
        raise RuntimeError("No VISA instruments found.")
    addr = resources[0]
    print(f"Using VISA resource: {addr}")

    scope = None
    try:
        scope = rm.open_resource(addr, timeout=20000, chunk_size=1024*1024)
        scope.write_termination = '\n'
        scope.read_termination  = None  # binary reads

        idn = scope.query("*IDN?").strip()
        print("IDN:", idn)

        # 1) Timebase + Fixed Sample Rate + Trigger
        scope.write(":ACQuire:MMANagement FSRate")
        scope.write(f":ACQuire:SRATe {SAMPLE_RATE:.9E}")
        print("SRATE set ->", scope.query(":ACQuire:SRATe?").strip())

        scope.write(f":TIMebase:SCALe {TIMEBASE_S_PER_DIV:.9E}")
        print("TIMEBASE set ->", scope.query(":TIMebase:SCALe?").strip())

        scope.write(":TRIGger:MODE NORMal")
        scope.write(f":TRIGger:EDGE:SOURce {TRIG_SOURCE}")
        scope.write(":TRIGger:EDGE:SLOPe POSitive")
        scope.write(f":TRIGger:LEVel {TRIG_LEVEL_V:.6f}")
        scope.write(":TRIGger:RUN")

        status = ""
        for _ in range(200):
            status = scope.query(":TRIGger:STATus?").strip()
            if status in ("Trig'd", "Stop"):
                break
            time.sleep(0.05)
        print("TRIG status:", status)

        # 2) Replace UI with SCPI: source + format
        scope.write(f":WAVeform:SOURce {CHANNEL}")
        scope.write(":WAVeform:WIDTh WORD")
        if POINTS_TO_READ is not None:
            scope.write(f":WAVeform:POINt {int(POINTS_TO_READ)}")

        # 3) PREamble + DATA (binary blocks)
        scope.write(":WAVeform:PREamble?")
        pre_bin = read_block(scope)
        meta = parse_preamble_block(pre_bin)

        scope.write(":WAVeform:DATA?")
        raw_bin = read_block(scope)

        # Convert and save
        volt = to_volts(
            raw_bin,
            meta["vdiv"], meta["code_per_div"], meta["voffset"],
            meta["adc_bits"], is_word=True
        )
        n = len(volt)
        dt = float(meta["dt"])
        delay = float(meta["delay"])
        grid = 10.0
        t0 = -delay - (TIMEBASE_S_PER_DIV * grid / 2.0)
        t = t0 + np.arange(n, dtype=np.float64) * dt

        np.save(NPY_PATH, np.vstack((t, volt)))
        with open(CSV_PATH, "w", encoding="utf-8") as f:
            f.write("# Siglent SDS824 capture\n")
            f.write(f"# idn={idn}\n")
            f.write(f"# points={n}\n")
            f.write(f"# dt={dt:.12e} s\n")
            f.write("# x_unit=s, y_unit=V\n")
            f.write("# columns: time_s, voltage_V\n")
            for ti, vi in zip(t, volt):
                f.write(f"{ti:.12e},{vi:.12e}\n")

        print(f"Saved {n} points")
        print("CSV:", CSV_PATH)
        print("NPY:", NPY_PATH)

        # 4) Drain, switch off events, then close — and neutralize destructor
        polite_flush(scope)
        try:
            # Some backends choke here; guard it
            scope.disable_event(pv.EventType.service_request, pv.EventMechanism.queue)
        except Exception:
            pass
        try:
            scope.close()
        except pv_errors.VisaIOError as e:
            print(f"Scope close warning (suppressed): {e}")
        except Exception as e:
            print(f"Scope close warning (suppressed): {e}")
        # Make PyVISA destructor a no-op for this instance
        try:
            scope.close = lambda *a, **k: None
        except Exception:
            pass

    finally:
        # Close RM (optional), also guarded + neutralize destructor call
        try:
            rm.close()
        except Exception as e:
            print(f"ResourceManager close warning (suppressed): {e}")

if __name__ == "__main__":
    main()
