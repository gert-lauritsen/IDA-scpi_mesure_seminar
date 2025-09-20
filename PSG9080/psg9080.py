# -*- coding: utf-8 -*-
"""
Created on Sat Sep 20 18:57:41 2025

@author: gert

PSG9080 Python driver

Implements the serial command protocol for the PSG9080 function/arbitrary waveform generator.

Protocol summary (per vendor PDF):
- Baud: 115200, 8N1
- Commands: ASCII lines beginning with ':' and ending with CRLF ("\r\n").
- Operator: 'w' (write) or 'r' (read)
- Function codes: integers selecting a feature; data fields separated by commas; numeric formats vary by command.

This driver wraps each documented command with a clear method.

Notes on numeric encodings:
- Frequency uses (value, unit_code), where the ID field is an integer with 3 implied decimals.
  Example: 25.786 Hz -> (25786, unit_code=0). See set_frequency().
- Amplitude (Vpp) is given in millivolts as an integer n; e.g., 1.000 Vpp -> n=1000.
- Duty cycle is in hundredths of a percent (e.g., 50% -> 5000).
- Phase is in hundredths of a degree (e.g., 180.00° -> 18000) per examples (the PDF shows 35999 -> 359.99°).
- Some features (offset, certain calibrations) use device-specific integer scales; helper methods expose the raw values
  with optional convenience converters when the mapping is clear from the documentation.

Tested conceptually without hardware; exceptions and parsing are robust for integration.


License: MIT
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import re
import time
from typing import Optional, Tuple, Union, List

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover
    serial = None  # Allows importing this module without pyserial installed


class PSG9080Error(Exception):
    pass


class Channel(IntEnum):
    CH1 = 1
    CH2 = 2


class Waveform(IntEnum):
    SINE = 0
    SQUARE = 1
    PULSE = 2
    TRIANGLE = 3
    SLOPE = 4
    CMOS = 5
    DC = 6
    PARTIAL_SINE = 7
    HALF_WAVE = 8
    FULL_WAVE = 9
    POS_LADDER = 10
    NEG_LADDER = 11
    POS_TRAPEZOID = 12
    NEG_TRAPEZOID = 13
    NOISE = 14
    EXP_RISE = 15
    EXP_FALL = 16
    LOG_RISE = 17
    LOG_FALL = 18
    SINKER_PULSE = 19
    MULTI_AUDIO = 20
    LORENZ = 21
    # Arbitrary waves: 101..199 correspond to Arb 01..99


class ModType(IntEnum):
    AM = 0
    FM = 1
    PM = 2
    ASK = 3
    FSK = 4
    PSK = 5
    PULSE = 6
    BURST = 7


class BuiltInModWave(IntEnum):
    SINE = 0
    SQUARE = 1
    TRIANGLE = 2
    RISING_SAW = 3
    FALLING_SAW = 4
    ARB101 = 5
    ARB102 = 6
    ARB103 = 7
    ARB104 = 8
    ARB105 = 9


@dataclass
class OpenOptions:
    port: str
    baudrate: int = 115200
    timeout: float = 0.5


_RESP_RE = re.compile(rb"^:(r\d{2})=(.*)\r\n$")


class PSG9080:
    def __init__(self, opts: OpenOptions):
        self.opts = opts
        self._ser = None  # type: Optional[serial.Serial]

    # ------------------------------ connection ------------------------------
    def open(self) -> None:
        if serial is None:
            raise PSG9080Error(
                "pyserial is not available; install with `pip install pyserial`."
            )
        if self._ser and self._ser.is_open:
            return
        self._ser = serial.Serial(
            self.opts.port,
            self.opts.baudrate,
            timeout=self.opts.timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )
        # Give device a moment after opening
        time.sleep(0.05)

    def close(self) -> None:
        if self._ser:
            try:
                self._ser.close()
            finally:
                self._ser = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    # ------------------------------ utilities ------------------------------
    def _send(self, line: str) -> None:
        if not self._ser or not self._ser.is_open:
            raise PSG9080Error("Serial port not open. Call open().")
        data = (":" + line + "\r\n").encode("ascii")
        self._ser.write(data)

    def _query(self, line: str) -> str:
        if not self._ser or not self._ser.is_open:
            raise PSG9080Error("Serial port not open. Call open().")
        self._send(line)
        raw = self._ser.readline()  # read until \n or timeout
        if not raw:
            raise PSG9080Error("No response from device.")
        m = _RESP_RE.match(raw)
        if not m:
            raise PSG9080Error(f"Malformed response: {raw!r}")
        # Return payload (right side of '=') as text without CRLF
        return m.group(2).decode("ascii")

    # --------------------------- encoding helpers ---------------------------
    @staticmethod
    def _freq_to_fields(hz: float) -> Tuple[int, int]:
        """Return (scaled_value, unit_code) using the spec's 3 implied decimals.
        unit_code: 0=Hz, 1=kHz, 2=MHz, 3=mHz, 4=μHz.
        We choose the most compact unit so that scaled_value fits 1..2_147_483_647.
        """
        if hz < 0:
            raise ValueError("Frequency must be non-negative")
        # Try units from Hz up to MHz/mHz/uHz picking value with 3 implied decimals
        units = [
            (0, 1.0),  # Hz
            (1, 1e3),  # kHz
            (2, 1e6),  # MHz
            (3, 1e-3),  # mHz
            (4, 1e-6),  # uHz
        ]
        # Prefer Hz/kHz/MHz for typical ranges
        best = (int(round(hz * 1000)), 0)
        for code, scale in units:
            scaled = int(round((hz / scale) * 1000))
            if 0 <= scaled <= 2_147_483_647:
                best = (scaled, code)
                # Prefer not to use sub-Hz units unless necessary
                if code in (0, 1, 2):
                    break
        return best

    @staticmethod
    def _fields_to_freq(value_str: str, unit_code: int) -> float:
        # Value has 3 implied decimals
        val = int(value_str)
        base = val / 1000.0
        if unit_code == 0:
            return base
        if unit_code == 1:
            return base * 1e3
        if unit_code == 2:
            return base * 1e6
        if unit_code == 3:
            return base * 1e-3
        if unit_code == 4:
            return base * 1e-6
        raise PSG9080Error(f"Unknown unit code {unit_code}")

    @staticmethod
    def _ensure_channel(ch: Union[int, Channel]) -> Channel:
        if isinstance(ch, Channel):
            return ch
        if ch in (1, 2):
            return Channel(ch)
        raise ValueError("Channel must be 1 or 2")

    # ------------------------------ core API -------------------------------
    # w10: Channel output enable
    def set_output(self, ch1_on: bool, ch2_on: bool) -> None:
        self._send(f"w10={1 if ch1_on else 0},{1 if ch2_on else 0}.")

    # r10: read output status -> "1,1" (1=on, 0=off)
    def get_output(self) -> Tuple[bool, bool]:
        payload = self._query("r10=0.")
        a, b = payload.strip(".").split(",")
        return (a == "1", b == "1")

    # w11/w12: waveform
    def set_waveform(self, ch: Union[int, Channel], wf: Union[int, Waveform]) -> None:
        ch = self._ensure_channel(ch)
        code = int(wf)
        if ch == Channel.CH1:
            self._send(f"w11={code}.")
        else:
            self._send(f"w12={code}.")

    def get_waveform(self, ch: Union[int, Channel]) -> int:
        ch = self._ensure_channel(ch)
        payload = self._query("r11=0." if ch == Channel.CH1 else "r12=0.")
        return int(payload.strip("."))

    # w13/w14: frequency
    def set_frequency(self, ch: Union[int, Channel], hz: float) -> None:
        ch = self._ensure_channel(ch)
        val, unit = self._freq_to_fields(hz)
        cmd = "w13" if ch == Channel.CH1 else "w14"
        self._send(f"{cmd}={val},{unit}.")

    def get_frequency(self, ch: Union[int, Channel]) -> float:
        ch = self._ensure_channel(ch)
        payload = self._query("r13=0." if ch == Channel.CH1 else "r14=0.")
        value_str, unit_str = payload.strip(".").split(",")
        return self._fields_to_freq(value_str, int(unit_str))

    # w15/w16: amplitude (Vpp) in mV steps
    def set_amplitude(self, ch: Union[int, Channel], vpp: float) -> None:
        ch = self._ensure_channel(ch)
        n = int(round(vpp * 1000))
        cmd = "w15" if ch == Channel.CH1 else "w16"
        self._send(f"{cmd}={n}.")

    def get_amplitude(self, ch: Union[int, Channel]) -> float:
        ch = self._ensure_channel(ch)
        payload = self._query("r15=0." if ch == Channel.CH1 else "r16=0.")
        n = int(payload.strip("."))
        return n / 1000.0

    # w17/w18: offset (raw encoding per manual). Expose raw + convenience volts<->code where feasible.
    def set_offset_raw(self, ch: Union[int, Channel], code: int) -> None:
        cmd = "w17" if self._ensure_channel(ch) == Channel.CH1 else "w18"
        self._send(f"{cmd}={code}.")

    def get_offset_raw(self, ch: Union[int, Channel]) -> int:
        payload = self._query("r17=0." if self._ensure_channel(ch) == Channel.CH1 else "r18=0.")
        return int(payload.strip("."))

    # w19/w20: duty cycle (hundredths of a percent)
    def set_duty(self, ch: Union[int, Channel], percent: float) -> None:
        n = int(round(percent * 100))
        cmd = "w19" if self._ensure_channel(ch) == Channel.CH1 else "w20"
        self._send(f"{cmd}={n}.")

    def get_duty(self, ch: Union[int, Channel]) -> float:
        payload = self._query("r19=0." if self._ensure_channel(ch) == Channel.CH1 else "r20=0.")
        n = int(payload.strip("."))
        return n / 100.0

    # w21/w22: phase (hundredths of a degree)
    def set_phase(self, ch: Union[int, Channel], degrees: float) -> None:
        n = int(round(degrees * 100))
        cmd = "w21" if self._ensure_channel(ch) == Channel.CH1 else "w22"
        self._send(f"{cmd}={n}.")

    def get_phase(self, ch: Union[int, Channel]) -> float:
        payload = self._query("r21=0." if self._ensure_channel(ch) == Channel.CH1 else "r22=0.")
        n = int(payload.strip("."))
        return n / 100.0

    # w24: UI interface select (raw)
    def set_interface(self, *fields: int) -> None:
        if not fields:
            raise ValueError("At least one field required")
        self._send("w24=" + ",".join(str(x) for x in fields) + ".")

    def get_interface(self) -> Tuple[int, int, int, int]:
        payload = self._query("r24=0.")
        a, b, c, d = payload.strip(".").split(",")
        return (int(a), int(b), int(c), int(d))

    # w25: sync settings (waveform, freq, ampl, offset, duty, external)
    def set_sync(self, waveform: bool, freq: bool, ampl: bool, offset: bool, duty: bool, ext_sig: bool) -> None:
        vals = [int(b) for b in (waveform, freq, ampl, offset, duty, ext_sig)]
        self._send(f"w25={','.join(map(str, vals))}.")

    def get_sync(self) -> Tuple[bool, bool, bool, bool, bool, bool]:
        payload = self._query("r25=0.")
        s = payload.strip(".")
        # Could be concatenated like "110000"; normalize to 6 chars
        if "," in s:
            parts = s.split(",")
        else:
            parts = list(s)
        parts = [int(x) for x in parts]
        while len(parts) < 6:
            parts.append(0)
        return tuple(bool(x) for x in parts[:6])  # type: ignore

    # w26: save/load/clear (raw)
    def memory(self, slot: int, op: str) -> None:
        """op: 'load' -> 111, 'save' -> 222, 'clear_slot' -> 333, 'clear_all' -> 444"""
        ops = {"load": 111, "save": 222, "clear_slot": 333, "clear_all": 444}
        code = ops.get(op)
        if code is None:
            raise ValueError("op must be one of: " + ", ".join(ops))
        self._send(f"w26={slot},{code}.")

    # w27..w33: sound, brightness, language, preset counts, load mode, fine tune
    def set_key_sound(self, on: bool) -> None:
        self._send(f"w27={1 if on else 0}.")

    def set_brightness(self, percent: int) -> None:
        self._send(f"w28={int(percent)}.")

    def set_language(self, chinese: bool) -> None:
        self._send(f"w29={1 if chinese else 0}.")

    def set_preset_wave_count(self, n: int) -> None:
        self._send(f"w30={int(n)}.")

    def set_preset_arb_count(self, n: int) -> None:
        self._send(f"w31={int(n)}.")

    def set_wave_load_mode(self, fast: bool) -> None:
        self._send(f"w32={1 if fast else 0}.")

    def set_fine_tune(self, n: int) -> None:
        self._send(f"w33={int(n)}.")

    # w40..w52: modulation settings
    def set_mod_types(self, ch1: ModType, ch2: ModType) -> None:
        self._send(f"w40={int(ch1)},{int(ch2)}.")

    def set_mod_builtin_wave(self, ch1: BuiltInModWave, ch2: BuiltInModWave) -> None:
        self._send(f"w41={int(ch1)},{int(ch2)}.")

    def set_mod_source_internal(self, ch1_internal: bool, ch2_internal: bool) -> None:
        self._send(f"w42={0 if ch1_internal else 1},{0 if ch2_internal else 1}.")

    def set_ch1_mod_freq(self, hz: float) -> None:
        val = int(round(hz * 1000))
        self._send(f"w43={val}.")

    def set_ch2_mod_freq(self, hz: float) -> None:
        val = int(round(hz * 1000))
        self._send(f"w44={val}.")

    def set_ch1_am_depth(self, percent: float) -> None:
        self._send(f"w45={int(round(percent * 10))}.")  # 80.0% -> 800

    def set_ch2_am_depth(self, percent: float) -> None:
        self._send(f"w46={int(round(percent * 10))}.")

    def set_ch1_fm_dev(self, hz: float) -> None:
        self._send(f"w47={int(round(hz * 10))}.")  # 0.1 Hz min step per doc

    def set_ch2_fm_dev(self, hz: float) -> None:
        self._send(f"w48={int(round(hz * 10))}.")

    def set_ch1_fsk_freq(self, hz: float) -> None:
        self._send(f"w49={int(round(hz * 10))}.")

    def set_ch2_fsk_freq(self, hz: float) -> None:
        self._send(f"w50={int(round(hz * 10))}.")

    def set_ch1_pm_dev(self, degrees: float) -> None:
        self._send(f"w51={int(round(degrees * 10))}.")  # 0.1° steps

    def set_ch2_pm_dev(self, degrees: float) -> None:
        self._send(f"w52={int(round(degrees * 10))}.")

    # w53..w56: pulse width/period in microseconds with 3 implied decimals (per examples)
    def set_pulse_width(self, ch: Union[int, Channel], microseconds: float) -> None:
        n = int(round(microseconds * 1000))
        cmd = "w53" if self._ensure_channel(ch) == Channel.CH1 else "w54"
        self._send(f"{cmd}={n}.")

    def set_pulse_period(self, ch: Union[int, Channel], microseconds: float) -> None:
        n = int(round(microseconds * 100))  # examples show 0.01 us resolution
        cmd = "w55" if self._ensure_channel(ch) == Channel.CH1 else "w56"
        self._send(f"{cmd}={n}.")

    # w57: pulse inversion
    def set_pulse_invert(self, ch1_invert: bool, ch2_invert: bool) -> None:
        self._send(f"w57={1 if ch1_invert else 0},{1 if ch2_invert else 0}.")

    # w58: burst idle mode (0 zero, 1 pos max, 2 neg max)
    def set_burst_idle(self, ch1_mode: int, ch2_mode: int) -> None:
        self._send(f"w58={int(ch1_mode)},{int(ch2_mode)}.")

    # w59: polarity (0 positive, 1 negative)
    def set_polarity(self, ch1_negative: bool, ch2_negative: bool) -> None:
        self._send(f"w59={1 if ch1_negative else 0},{1 if ch2_negative else 0}.")

    # w60: trigger source (0 key,1 internal,2 ext AC,3 ext DC)
    def set_trigger_source(self, ch1: int, ch2: int) -> None:
        self._send(f"w60={int(ch1)},{int(ch2)}.")

    # w61: burst pulse number
    def set_burst_count(self, ch1: int, ch2: int) -> None:
        self._send(f"w61={int(ch1)},{int(ch2)}.")

    # w62/w63: measurement config & switches
    def set_measurement(self, coupling_ac: bool, gate_time_ms: int, low_freq_mode: bool) -> None:
        n1 = 0 if coupling_ac else 1
        n2 = int(gate_time_ms)
        n3 = 1 if low_freq_mode else 0
        self._send(f"w62={n1},{n2},{n3}.")

    def set_measurement_switches(self, measure_on: bool, counter_on: bool) -> None:
        self._send(f"w63={1 if measure_on else 0},{1 if counter_on else 0}.")

    # w64..w71, w72..w73: sweep / VCO and calibration
    def set_sweep(self, channel: Channel, sweep_time_ms: int, direction: int, mode_log: bool) -> None:
        n1 = 0 if channel == Channel.CH1 else 1
        n2 = int(sweep_time_ms)
        n3 = int(direction)  # 0 inc, 1 dec, 2 back/forth
        n4 = 1 if mode_log else 0
        self._send(f"w64={n1},{n2},{n3},{n4}.")

    def set_sweep_vco_switches(self, sweep_on: bool, vco_on: bool) -> None:
        self._send(f"w65={1 if sweep_on else 0},{1 if vco_on else 0}.")

    def set_sweep_start_freq(self, hz: float) -> None:
        val, unit = self._freq_to_fields(hz)
        self._send(f"w66={val}.")  # manual shows single value; device uses implied 3 dec

    def set_sweep_end_freq(self, hz: float) -> None:
        val, unit = self._freq_to_fields(hz)
        self._send(f"w67={val}.")

    def set_sweep_start_ampl(self, vpp: float) -> None:
        self._send(f"w68={int(round(vpp * 1000))}.")

    def set_sweep_end_ampl(self, vpp: float) -> None:
        self._send(f"w69={int(round(vpp * 1000))}.")

    def set_sweep_start_duty(self, percent: float) -> None:
        self._send(f"w70={int(round(percent * 100))}.")

    def set_sweep_end_duty(self, percent: float) -> None:
        self._send(f"w71={int(round(percent * 100))}.")

    def set_min_voltage_cal(self, code: int) -> None:
        self._send(f"w72={int(code)}.")

    def set_max_voltage_cal(self, code: int) -> None:
        self._send(f"w73={int(code)}.")

    # w74: trigger on/off per channel
    def trigger(self, ch1: bool, ch2: bool) -> None:
        self._send(f"w74={1 if ch1 else 0},{1 if ch2 else 0}.")

    # ------------------------------- reads ---------------------------------
    # Expose frequently used r-commands; more can be added similarly if needed.
    def get_am_depth(self, ch: Union[int, Channel]) -> float:
        payload = self._query("r45=0." if self._ensure_channel(ch) == Channel.CH1 else "r46=0.")
        return int(payload.strip(".")) / 10.0

    def get_fm_dev(self, ch: Union[int, Channel]) -> float:
        payload = self._query("r47=0." if self._ensure_channel(ch) == Channel.CH1 else "r48=0.")
        return int(payload.strip(".")) / 10.0

    def get_pm_dev(self, ch: Union[int, Channel]) -> float:
        payload = self._query("r51=0." if self._ensure_channel(ch) == Channel.CH1 else "r52=0.")
        return int(payload.strip(".")) / 10.0

    def get_pulse_width_us(self, ch: Union[int, Channel]) -> float:
        payload = self._query("r53=0." if self._ensure_channel(ch) == Channel.CH1 else "r54=0.")
        return int(payload.strip(".")) / 1000.0

    def get_pulse_period_us(self, ch: Union[int, Channel]) -> float:
        payload = self._query("r55=0." if self._ensure_channel(ch) == Channel.CH1 else "r56=0.")
        return int(payload.strip(".")) / 100.0

    def get_burst_count(self, ch: Union[int, Channel]) -> int:
        payload = self._query("r61=0.")
        a, b = payload.strip(".").split(",")
        return int(a) if self._ensure_channel(ch) == Channel.CH1 else int(b)

    def get_measurement_frequency_hz(self, high_band: bool = True) -> float:
        payload = self._query("r81=0." if high_band else "r82=0.")
        return int(payload.strip(".")) / (1.0 if high_band else 1000.0)

    # ---------------------------- convenience ------------------------------
    def configure_basic(self, ch: Union[int, Channel], *, waveform: Union[int, Waveform] = Waveform.SINE,
                        frequency_hz: float = 1000.0, amplitude_vpp: float = 1.0, offset_raw: Optional[int] = None,
                        duty_percent: Optional[float] = None, phase_deg: Optional[float] = None,
                        output_on: bool = True) -> None:
        """Quickly configure a channel with common parameters and toggle outputs.
        For DC waveform, amplitude_vpp adjusts the DC level range per device behavior.
        """
        ch = self._ensure_channel(ch)
        self.set_waveform(ch, int(waveform))
        self.set_frequency(ch, frequency_hz)
        self.set_amplitude(ch, amplitude_vpp)
        if offset_raw is not None:
            self.set_offset_raw(ch, offset_raw)
        if duty_percent is not None:
            self.set_duty(ch, duty_percent)
        if phase_deg is not None:
            self.set_phase(ch, phase_deg)
        if ch == Channel.CH1:
            st = self.get_output()[1]
            self.set_output(output_on, st)
        else:
            st = self.get_output()[0]
            self.set_output(st, output_on)


# Example usage:
# with PSG9080(OpenOptions(port="/dev/ttyUSB0")) as psg:
#     psg.set_output(False, False)
#     psg.configure_basic(1, waveform=Waveform.SINE, frequency_hz=10000, amplitude_vpp=1.0)
#     psg.set_output(True, False)
#     print("CH1 freq:", psg.get_frequency(1))
