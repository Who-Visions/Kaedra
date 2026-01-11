# Razer Chroma SDK REST API - Comprehensive Documentation Summary

## Overview

The Razer Chroma SDK REST API allows third-party applications to interact with Razer Synapse and control RGB lighting across all supported devices (Keyboard, Mouse, Headset, Mousepad, Keypad, ChromaLink).

## Connection Basics

- **Base URL**: `http://localhost:54235/razer/chromasdk`
- **Discovery**: `POST` to the base URL with application info to obtain a session `uri` and `sessionid`.
- **Heartbeat**: `PUT` to `[session_uri]/heartbeat` every 1 second.
- **Timeout**: The SDK closes sessions if no activity is detected for **15 seconds**.

## Endpoint Reference & Matrix Sizes

| Device Type | Endpoint | Size / Layout |
| :--- | :--- | :--- |
| **Keyboard** | `/keyboard` | 6 Rows x 22 Columns (Standard) / 8x24 (Extended) |
| **Mouse** | `/mouse` | 9 Rows x 7 Columns |
| **Mousepad** | `/mousepad` | 15 LEDs (Standard) / 20 LEDs (Extended) |
| **Headset** | `/headset` | 5 LEDs |
| **Keypad** | `/keypad` | 4 Rows x 5 Columns |
| **ChromaLink** | `/chromalink` | 5 LEDs |
| **HeadsetStand** | `/headsetstand` | (Often mapped to 5 LEDs) |

## Result Codes (RZRESULT)

Successful calls return `{ "result": 0 }`. If a call fails, the `result` field contains an error code.

### Common SDK Errors

| Code | Constant | Meaning |
| :--- | :--- | :--- |
| **0** | `RZRESULT_SUCCESS` | Operation successful. |
| **5** | `RZRESULT_ACCESS_DENIED` | Permission issue (Synapse may be blocking). |
| **50** | `RZRESULT_NOT_SUPPORTED` | Device or effect type not supported. |
| **87** | `RZRESULT_INVALID_PARAMETER` | Incorrect payload structure (e.g., wrong array size). |
| **1062** | `RZRESULT_SERVICE_NOT_ACTIVE` | Chroma SDK service is stopped or crashing. |
| **1167** | `RZRESULT_DEVICE_NOT_CONNECTED` | Device is not found or unplugged. |
| **1247** | `RZRESULT_ALREADY_INITIALIZED` | Application already has an active session. |

### The "Result 126" Mystery

The value `126` is **not** defined in the Razer SDK headers (`RzErrors.h`). Following the SDK's fallback logic to Windows System Error Codes:

- **Code 126**: `ERROR_MOD_NOT_FOUND` ("The specified module could not be found").
- **Analysis**: This typically means the REST server (Synapse) cannot locate the internal logic DLL (e.g., `RzChromaSDK64.dll`) or a device-specific module required to process the request.

## Best Practices

1. **BGR Format**: All colors must be in `0x00BBGGRR` format.
2. **Active Driving**: Continuous updates (10Hz-30Hz) are better for responsive lighting than one-shot updates.
3. **Session Management**: Always `DELETE` the session URI when closing the application to allow other apps to take control.

## Scour Answers for Kaedra Debugging

- **Laptop Stand (PID 3853)** is defined as a `mousemat` (accessory category) in `Devices.xml`.
- **Mapping**: Based on the docs, `mousemat` maps to the `/mousepad` endpoint.
- **Error 126 solution**: If `/mousepad` returns 126, it implies the module for handling mousemats is missing or failing to load in Synapse 4.
- **Workaround**: Since the stand also appears to respond to `/chromalink` (which has 5 LEDs), the "Universal Drive" approach (driving all accessory endpoints) is the safest path forward.
