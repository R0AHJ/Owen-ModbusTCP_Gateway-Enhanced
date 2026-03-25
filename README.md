# Industrial Gateway Templates

## OVEN RS-485 -> Modbus TCP

Gateway for OVEN devices such as `TRM138`.

The gateway communicates with field devices only through the OVEN protocol on
`RS-485` and publishes data to clients through `Modbus TCP`.

## What Is Implemented

- OVEN frame encode/decode
- parameter hash and CRC calculation
- polling over one or multiple `RS-485` buses
- `Modbus TCP` publication
- service status and telemetry registers
- `rEAd` value publication with `time mark`
- `TRM138` parameter decoding for `C.SP`, `HYSt`, `AL.t`
- logical unit state mask in `HR48`

## Runtime Model

- service registers are published in `SlaveID 1`
- device `SlaveID` equals the device base OVEN address
- `TRM138` is read only through the OVEN protocol
- `time mark` is published but does not affect channel status

## Service Registers

- `HR1` gateway status
- `HR2` last error code
- `HR3` success counter
- `HR4` timeout counter
- `HR5` protocol error counter
- `HR6` poll cycle counter
- `HR10..HR13` per-line status

Gateway status codes:

- `1` ok
- `2` degraded
- `3` offline
- `4` protocol error

Last error codes:

- `0` none
- `1` timeout
- `2` bad flag
- `3` hash mismatch
- `4` decode error
- `5` io error

## TRM138 Device Map

For each device:

- values: `HR16..HR31`
- time marks: `HR32..HR39`
- channel statuses: `HR40..HR47`
- LU mask: `HR48`

Channel status codes:

- `0` disabled / no data / empty payload
- `1` ok
- `2` temporary communication error
- `3` protocol error
- `4` failed, reduced polling

`HR48` contains one bitmask:

- `bit0..bit7 -> LU1..LU8`

## TRM138 Parameters

Supported OVEN parameters:

- `rEAd` -> `float32`
- `C.SP` -> `stored_dot`
- `HYSt` -> `uint16`
- `AL.t` -> `uint16`

Important:

- `C.SP`, `HYSt`, `AL.t` are read by channel address, like `rEAd`
- `C.SP` uses OVEN `stored_dot` encoding
- both `2`-byte and `3`-byte `stored_dot` payloads are supported

Examples confirmed on hardware:

- `00 4b` -> `75.0`
- `13 e8` -> `100.0`
- `2b c2` -> `30.1`
- `20 24 ea` -> `94.5`

## Logical Unit Mask

The gateway calculates `HR48` from:

- measured channel value `rEAd`
- setpoint `C.SP`
- hysteresis `HYSt`
- output characteristic `AL.t`

Supported `AL.t` modes:

- `1` direct hysteresis
- `2` reverse hysteresis
- `3` inside band
- `4` outside band

## Config Notes

Health section:

- `fault_after_failures`
- `recovery_poll_interval_cycles`

Legacy `stale_after_cycles` is ignored if present in an old config.

Ready examples:

- [owen_config.single_trm138.com6.json](/D:/Python_Project/owen_config.single_trm138.com6.json)
- [owen_config.example.json](/D:/Python_Project/owen_config.example.json)
- [owen_config.com6.two_trm138.addr48_96.json](/D:/Python_Project/owen_config.com6.two_trm138.addr48_96.json)
- [owen_config.linux.json](/D:/Python_Project/owen_config.linux.json)
- [owen_config.windows.json](/D:/Python_Project/owen_config.windows.json)

Project navigation:

- [PROJECT_FILES.md](/D:/Python_Project/PROJECT_FILES.md)

## Install

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

## Run

```bash
python -m owen_gateway --config owen_config.json
```

Probe:

```bash
python -m owen_gateway.probe --config owen_probe.com6.json --log-level INFO
```

Tests:

```bash
python -m unittest discover -s tests
```
