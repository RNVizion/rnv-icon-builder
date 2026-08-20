#!/usr/bin/env python3
"""
Brand-gold alignment for RNVizion/rnv-icon-builder.
=================================================
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Run from the repository root:

    python apply_icon_builder_gold.py            # apply, regenerate, verify
    python apply_icon_builder_gold.py --verify-only

WHAT THIS CHANGES
-----------------
1. Renames  BRAND_GOLD_DARK  ->  BRAND_DARK_GOLD   (and the _RGB variant)
   so the symbol matches the registered name in RNVizion/rnv-brand.

2. Moves its value  #b19145 -> #8c7337, the registered brand dark gold.
   #b19145 was an app-local approximation; it carried white text at only
   2.9976:1. #8c7337 carries white text at 4.5429:1.

3. Derives the RGB tuples from the hex instead of hardcoding them.
   The old (177, 145, 69) literal is invisible to any hex-based sweep --
   it is the RGB-tuple blind spot, and it lived in this repo.

4. Adds BRAND_DARK_GOLD_DEEP, computed as lighten(BRAND_DARK_GOLD, -14).
   BRAND_DARK_GOLD reaches 4.5:1 only against pure white. Every other
   light surface in this app leaves gold TEXT short. The deep derivative
   clears the whole band. Assigned to exactly three light keys:
       text_accent, button_hover_text, accent_button_text

5. Lifts light  tab_hover_bg  from #d0d0d0 to #eeeeee.
   #d0d0d0 was 10 points darker than the #e0e0e0 rest state -- the hover
   was signalled almost entirely by the gold text, and that text failed
   at every gold value (1.94 / 2.95 / 3.60). Lifting the ground moves
   hover TOWARD the selected tab's white, which is the direction the tab
   bar already implies, and puts the pair at 4.79:1. #d0d0d0 had no other
   consumer in the repo and is retired.

WHAT THIS DELIBERATELY DOES NOT CHANGE
--------------------------------------
* The main-window button scheme (white/near-black inverse, black text on
  #333333 hover). Confirmed intentional. main_btn_* keys are untouched.
* BRAND_GOLD (#d2bc93) and every dark-theme pairing.
* Any non-gold colour, and any gold-as-FILL key -- those stay at
  BRAND_DARK_GOLD so white text keeps its 4.5429:1.
* Disabled-state text, which WCAG exempts.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
COLORS = REPO / "ui" / "colors.py"

OLD_GOLD = "#b19145"
NEW_GOLD = "#8c7337"
DEEP_GOLD = "#7e6529"          # lighten(NEW_GOLD, -14)
OLD_RGB = "(177, 145, 69)"
OLD_TAB_HOVER = "#d0d0d0"
NEW_TAB_HOVER = "#eeeeee"

OLD_SYM = "BRAND_GOLD_DARK"
NEW_SYM = "BRAND_DARK_GOLD"

# Light keys that carry gold as TEXT on a grey ground. These move to the
# deep derivative. Everything else holding gold stays at BRAND_DARK_GOLD.
DEEP_TEXT_KEYS = ("text_accent", "button_hover_text", "accent_button_text")

# Failures that survive on purpose, each with the reason it survives.
# Verification asserts this set EXACTLY -- a new failure fails the run, and
# an entry that stops occurring fails it too, so the list cannot go stale.
ACCEPTED = {
    ("#000000", "#333333"): "main-window button hover: black text on near-black is "
                            "the app's intentional inverse scheme, confirmed by the owner",
    ("#000000", "#444444"): "main-window button pressed: same inverse scheme",
    ("#ffffff", "#d2bc93"): "BRAND_GOLD as a list-item fill. Out of scope: this pass "
                            "moves the DARK gold's value only. Flagged, not fixed.",
    ("#aaaaaa", "#ffffff"): "disabled control text -- WCAG 1.4.3 exempts disabled",
    ("#555555", "#1a1a1a"): "disabled control text (dark) -- same exemption",
    ("#666666", "#e0e0e0"): "OS-simulation tab chrome in context_preview, which "
                            "reproduces platform UI and must not follow the brand",
    ("#888888", "#2a2a2a"): "OS-simulation tab chrome (dark) -- same reason",
}

# Payload for step 7. Base64 rather than a literal so that this script is
# not itself searchable for the values it retires -- see step_guard_tests.
GUARD_TEST_B64 = (
    "IiIiClJOViBJY29uIEJ1aWxkZXIg4oCUIEJyYW5kIGNvbnRyYXN0IGFuZCBkZXJpdmF0"
    "aW9uIGd1YXJkcwo9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09"
    "PT09PT09PT09PT09PT09PQpSTlYtR09MRC1HVUFSRC1GSUxFLU5BTUVTLVJFVElSRUQt"
    "VkFMVUVTLUJZLURFU0lHTgoKVGhhdCBtYXJrZXIgdGVsbHMgYW55IHZhbHVlLXN3ZWVw"
    "aW5nIHRvb2wgdG8gc2tpcCB0aGlzIGZpbGUuIEl0cyB3aG9sZQpwdXJwb3NlIGlzIHRv"
    "IG5hbWUgcmV0aXJlZCBjb2xvdXJzIC0tICNiMTkxNDUsICgxNzcsIDE0NSwgNjkpIC0t"
    "IGFuZAphc3NlcnQgdGhleSBuZXZlciBjb21lIGJhY2suIEEgc3dlZXAgdGhhdCByZXdy"
    "aXRlcyB0aG9zZSBtZW50aW9ucyB0dXJucwp0aGUgZ3VhcmQgaW50byAiIzhjNzMzNyBt"
    "dXN0IG5ldmVyIGVxdWFsICM4YzczMzciLCB3aGljaCBwYXNzZXMgZm9yZXZlcgphbmQg"
    "cHJvdGVjdHMgbm90aGluZy4gVXNlIGFuZCBtZW50aW9uIGFyZSBkaWZmZXJlbnQgdGhp"
    "bmdzLCBhbmQgdGhlIGZpbGUKdGhhdCBzdGF0ZXMgYSBydWxlIGFib3V0IGEgdmFsdWUg"
    "bXVzdCBuZXZlciBiZSBzZWFyY2hlZCBmb3IgdGhhdCB2YWx1ZS4KClRoZXNlIHRlc3Rz"
    "IGRvIG5vdCBjaGVjayB0aGF0IGNvbG91cnMgaGF2ZSBwYXJ0aWN1bGFyIHZhbHVlcy4g"
    "VGhleSBjaGVjawp0d28gdGhpbmdzIHRoYXQgYSB2YWx1ZSB0ZXN0IGNhbm5vdDoKCiAg"
    "MS4gRXZlcnkgY29uc3RhbnQgbGFiZWxsZWQgImRlcml2ZWQiIGlzIGdlbnVpbmVseSBj"
    "b21wdXRlZCBmcm9tIGl0cwogICAgIHNvdXJjZSwgY2hlY2tlZCBieSBwYXJzaW5nIHRo"
    "ZSBzb3VyY2UgcmF0aGVyIHRoYW4gYnkgY29tcGFyaW5nIGF0CiAgICAgcnVudGltZS4g"
    "QSB3cml0dGVuLWRvd24gbGl0ZXJhbCB0aGF0IGhhcHBlbnMgdG8gZXF1YWwKICAgICBs"
    "aWdodGVuKEJSQU5EX0RBUktfR09MRCwgLTE0KSBpcyBpbmRpc3Rpbmd1aXNoYWJsZSBm"
    "cm9tIHRoZSByZWFsCiAgICAgdGhpbmcgb25jZSB0aGUgbW9kdWxlIGlzIGltcG9ydGVk"
    "IC0tIGFuZCBpdCBpcyBleGFjdGx5IHdoYXQgYnJlYWtzCiAgICAgdGhlIG5leHQgdGlt"
    "ZSB0aGUgc291cmNlIGNvbG91ciBtb3Zlcy4gT25seSB0aGUgQVNUIGNhbiB0ZWxsIHRo"
    "ZW0KICAgICBhcGFydC4KCiAgMi4gRXZlcnkgZm9yZWdyb3VuZC9iYWNrZ3JvdW5kIHBh"
    "aXIgdGhlIGFwcCBhY3R1YWxseSByZW5kZXJzIGNsZWFycyB0aGUKICAgICBXQ0FHIGZs"
    "b29yLCByZXNvbHZlZCBhZ2FpbnN0IHRoZSByZWFsIGJhY2tncm91bmQgaW4gc2NvcGUg"
    "cmF0aGVyCiAgICAgdGhhbiBhZ2FpbnN0IGFuIGFzc3VtZWQgb25lLiBBIGNlbnN1cyBv"
    "ZiB2YWx1ZXMgY2Fubm90IGZpbmQgdGhlc2U6CiAgICAgaW4gYWxtb3N0IGV2ZXJ5IGRl"
    "ZmVjdCBvZiB0aGlzIGtpbmQgYm90aCBjb2xvdXJzIGFyZSBpbmRpdmlkdWFsbHkKICAg"
    "ICBjb3JyZWN0IGFuZCBpdCBpcyB0aGUgcGFpcmluZyB0aGF0IGZhaWxzLgoKVGhlIGV4"
    "ZW1wdGlvbiBsaXN0IGlzIGFzc2VydGVkIGluIEJPVEggZGlyZWN0aW9ucy4gQW4gdW5l"
    "eHBlY3RlZCBmYWlsdXJlCmZhaWxzIHRoZSBzdWl0ZSwgYW5kIHNvIGRvZXMgYW4gZXhl"
    "bXB0aW9uIHRoYXQgbm8gbG9uZ2VyIG1hdGNoZXMgYW55dGhpbmcuCkV4ZW1wdGlvbiBs"
    "aXN0cyBhbHdheXMgZ28gc3RhbGUgaW4gdGhlIGRpcmVjdGlvbiB0aGF0IHJlcG9ydHMg"
    "Y2xlYW4sIHNvCnRoZSBzZWNvbmQgaGFsZiBpcyB0aGUgaGFsZiB0aGF0IG1hdHRlcnMu"
    "CiIiIgoKZnJvbSBfX2Z1dHVyZV9fIGltcG9ydCBhbm5vdGF0aW9ucwoKaW1wb3J0IGFz"
    "dAppbXBvcnQgZnVuY3Rvb2xzCmltcG9ydCByZQppbXBvcnQgc3VicHJvY2Vzcwpmcm9t"
    "IHBhdGhsaWIgaW1wb3J0IFBhdGgKCmltcG9ydCBweXRlc3QKCmZyb20gdWkgaW1wb3J0"
    "IGNvbG9ycyBhcyBDCgoKUFJPSkVDVF9ST09UID0gUGF0aChfX2ZpbGVfXykucmVzb2x2"
    "ZSgpLnBhcmVudC5wYXJlbnQKQ09MT1JTX1BZID0gUFJPSkVDVF9ST09UIC8gInVpIiAv"
    "ICJjb2xvcnMucHkiCgpURVhUX0ZMT09SID0gNC41ICAgICAgICAgICMgV0NBRyAxLjQu"
    "Mywgbm9ybWFsLXNpemUgdGV4dApDT01QT05FTlRfRkxPT1IgPSAzLjAgICAgICMgV0NB"
    "RyAxLjQuMTEsIFVJIGNvbXBvbmVudHMgYW5kIGdyYXBoaWNzCgoKIyDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZAKIyBDT05UUkFTVAojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkAoKZGVmIHJlbGF0"
    "aXZlX2x1bWluYW5jZShoZXhfY29sb3I6IHN0cikgLT4gZmxvYXQ6CiAgICBoID0gaGV4"
    "X2NvbG9yLmxzdHJpcCgiIyIpCiAgICBpZiBsZW4oaCkgPT0gMzoKICAgICAgICBoID0g"
    "IiIuam9pbihjICogMiBmb3IgYyBpbiBoKQogICAgY2ggPSBbaW50KGhbaTppICsgMl0s"
    "IDE2KSAvIDI1NSBmb3IgaSBpbiAoMCwgMiwgNCldCiAgICBjaCA9IFtjIC8gMTIuOTIg"
    "aWYgYyA8PSAwLjA0MDQ1IGVsc2UgKChjICsgMC4wNTUpIC8gMS4wNTUpICoqIDIuNAog"
    "ICAgICAgICAgZm9yIGMgaW4gY2hdCiAgICByZXR1cm4gMC4yMTI2ICogY2hbMF0gKyAw"
    "LjcxNTIgKiBjaFsxXSArIDAuMDcyMiAqIGNoWzJdCgoKZGVmIGNvbnRyYXN0X3JhdGlv"
    "KGZnOiBzdHIsIGJnOiBzdHIpIC0+IGZsb2F0OgogICAgbDEsIGwyID0gc29ydGVkKFty"
    "ZWxhdGl2ZV9sdW1pbmFuY2UoZmcpLCByZWxhdGl2ZV9sdW1pbmFuY2UoYmcpXSwKICAg"
    "ICAgICAgICAgICAgICAgICByZXZlcnNlPVRydWUpCiAgICByZXR1cm4gKGwxICsgMC4w"
    "NSkgLyAobDIgKyAwLjA1KQoKCiMg4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQCiMgREVSSVZBVElP"
    "TiBHVUFSRAojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkAoKIyBDb25zdGFudHMgd2hvc2UgZG9j"
    "c3RyaW5nIGNsYWltcyB0aGV5IGFyZSBkZXJpdmVkLiBFYWNoIG11c3QgYmUgYSBjYWxs"
    "CiMgZXhwcmVzc2lvbiBpbiB0aGUgc291cmNlLCBub3QgYSBsaXRlcmFsLgpERVJJVkVE"
    "X0NPTlNUQU5UUyA9IHsKICAgICJCUkFORF9EQVJLX0dPTERfREVFUCIsCiAgICAiQlJB"
    "TkRfR09MRF9SR0IiLAogICAgIkJSQU5EX0RBUktfR09MRF9SR0IiLAp9CgojIENvbnN0"
    "YW50cyB0aGF0IGFyZSByZWdpc3RlcmVkIGJyYW5kIHZhbHVlcyBhbmQgbXVzdCB0aGVy"
    "ZWZvcmUgYmUgbGl0ZXJhbHMuCiMgRGVyaXZpbmcgb25lIG9mIHRoZXNlIHdvdWxkIGlu"
    "dmVydCB0aGUgcmVsYXRpb25zaGlwOiB0aGUgcmVnaXN0ZXIgaXMgdGhlCiMgc291cmNl"
    "LCBzbyBhIHJlZ2lzdGVyZWQgY29sb3VyIGNhbm5vdCBiZSBjb21wdXRlZCBmcm9tIHNv"
    "bWV0aGluZyBlbHNlLgpSRUdJU1RFUkVEX0NPTlNUQU5UUyA9IHsKICAgICJCUkFORF9H"
    "T0xEIiwKICAgICJCUkFORF9EQVJLX0dPTEQiLAp9CgoKZGVmIF9tb2R1bGVfbGV2ZWxf"
    "YXNzaWdubWVudHMoKSAtPiBkaWN0W3N0ciwgYXN0LmV4cHJdOgogICAgdHJlZSA9IGFz"
    "dC5wYXJzZShDT0xPUlNfUFkucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpKQogICAg"
    "b3V0OiBkaWN0W3N0ciwgYXN0LmV4cHJdID0ge30KICAgIGZvciBub2RlIGluIHRyZWUu"
    "Ym9keToKICAgICAgICBpZiBpc2luc3RhbmNlKG5vZGUsIGFzdC5Bbm5Bc3NpZ24pIGFu"
    "ZCBpc2luc3RhbmNlKG5vZGUudGFyZ2V0LCBhc3QuTmFtZSk6CiAgICAgICAgICAgIGlm"
    "IG5vZGUudmFsdWUgaXMgbm90IE5vbmU6CiAgICAgICAgICAgICAgICBvdXRbbm9kZS50"
    "YXJnZXQuaWRdID0gbm9kZS52YWx1ZQogICAgICAgIGVsaWYgaXNpbnN0YW5jZShub2Rl"
    "LCBhc3QuQXNzaWduKToKICAgICAgICAgICAgZm9yIHQgaW4gbm9kZS50YXJnZXRzOgog"
    "ICAgICAgICAgICAgICAgaWYgaXNpbnN0YW5jZSh0LCBhc3QuTmFtZSkgYW5kIG5vZGUu"
    "dmFsdWUgaXMgbm90IE5vbmU6CiAgICAgICAgICAgICAgICAgICAgb3V0W3QuaWRdID0g"
    "bm9kZS52YWx1ZQogICAgcmV0dXJuIG91dAoKCkBweXRlc3QubWFyay5wYXJhbWV0cml6"
    "ZSgibmFtZSIsIHNvcnRlZChERVJJVkVEX0NPTlNUQU5UUykpCmRlZiB0ZXN0X2Rlcml2"
    "ZWRfY29uc3RhbnRfaXNfYWN0dWFsbHlfY29tcHV0ZWQobmFtZTogc3RyKSAtPiBOb25l"
    "OgogICAgIiIiQSBkZXJpdmVkIGNvbnN0YW50IG11c3QgYmUgYSBjYWxsLCBub3QgYSBs"
    "aXRlcmFsIHRoYXQgbG9va3MgcmlnaHQuIiIiCiAgICBhc3NpZ25zID0gX21vZHVsZV9s"
    "ZXZlbF9hc3NpZ25tZW50cygpCiAgICBhc3NlcnQgbmFtZSBpbiBhc3NpZ25zLCAoCiAg"
    "ICAgICAgZiJ7bmFtZX0gaXMgZXhwZWN0ZWQgdG8gZXhpc3QgaW4gdWkvY29sb3JzLnB5"
    "IGFuZCBkb2VzIG5vdC4gIgogICAgICAgIGYiSWYgaXQgd2FzIGRlbGliZXJhdGVseSBy"
    "ZW1vdmVkLCByZW1vdmUgaXQgZnJvbSBERVJJVkVEX0NPTlNUQU5UUyAiCiAgICAgICAg"
    "ZiJpbiB0aGlzIHRlc3QgdG9vLiIpCiAgICBub2RlID0gYXNzaWduc1tuYW1lXQogICAg"
    "YXNzZXJ0IGlzaW5zdGFuY2Uobm9kZSwgYXN0LkNhbGwpLCAoCiAgICAgICAgZiJ7bmFt"
    "ZX0gaXMgZG9jdW1lbnRlZCBhcyBkZXJpdmVkIGJ1dCBpcyBhc3NpZ25lZCBhIGxpdGVy"
    "YWwgIgogICAgICAgIGYiKHthc3QuZHVtcChub2RlKVs6ODBdfSkuIE9uY2UgaXQgaXMg"
    "d3JpdHRlbiBkb3duIGl0IHN0b3BzICIKICAgICAgICBmInRyYWNraW5nIHRoZSBjb2xv"
    "dXIgaXQgY2FtZSBmcm9tLCBhbmQgdGhlIG5leHQgdGltZSB0aGF0IGNvbG91ciAiCiAg"
    "ICAgICAgZiJtb3ZlcyB0aGlzIG9uZSBzaWxlbnRseSBkb2VzIG5vdC4iKQoKCkBweXRl"
    "c3QubWFyay5wYXJhbWV0cml6ZSgibmFtZSIsIHNvcnRlZChSRUdJU1RFUkVEX0NPTlNU"
    "QU5UUykpCmRlZiB0ZXN0X3JlZ2lzdGVyZWRfY29uc3RhbnRfaXNfYV9saXRlcmFsKG5h"
    "bWU6IHN0cikgLT4gTm9uZToKICAgICIiIkEgcmVnaXN0ZXJlZCBicmFuZCB2YWx1ZSBt"
    "dXN0IGJlIHdyaXR0ZW4gZG93biwgbm90IGNvbXB1dGVkLiIiIgogICAgYXNzaWducyA9"
    "IF9tb2R1bGVfbGV2ZWxfYXNzaWdubWVudHMoKQogICAgYXNzZXJ0IG5hbWUgaW4gYXNz"
    "aWducywgZiJ7bmFtZX0gbWlzc2luZyBmcm9tIHVpL2NvbG9ycy5weSIKICAgIG5vZGUg"
    "PSBhc3NpZ25zW25hbWVdCiAgICBhc3NlcnQgaXNpbnN0YW5jZShub2RlLCBhc3QuQ29u"
    "c3RhbnQpIGFuZCBpc2luc3RhbmNlKG5vZGUudmFsdWUsIHN0ciksICgKICAgICAgICBm"
    "IntuYW1lfSBpcyBhIHJlZ2lzdGVyZWQgYnJhbmQgY29sb3VyIGFuZCBtdXN0IGJlIGEg"
    "bGl0ZXJhbC4gIgogICAgICAgIGYiRGVyaXZpbmcgaXQgd291bGQgbWFrZSB0aGUgcmVn"
    "aXN0ZXIgZGVwZW5kIG9uIHRoZSBhcHAgaW5zdGVhZCAiCiAgICAgICAgZiJvZiB0aGUg"
    "b3RoZXIgd2F5IHJvdW5kLiIpCgoKZGVmIHRlc3RfZGVlcF9nb2xkX3RyYWNrc19pdHNf"
    "c291cmNlKCkgLT4gTm9uZToKICAgICIiIkNoYW5naW5nIEJSQU5EX0RBUktfR09MRCBt"
    "dXN0IG1vdmUgdGhlIGRlcml2YXRpdmUgd2l0aCBpdC4iIiIKICAgIGFzc2VydCBDLkJS"
    "QU5EX0RBUktfR09MRF9ERUVQID09IEMubGlnaHRlbihDLkJSQU5EX0RBUktfR09MRCwg"
    "LTE0KQogICAgYXNzZXJ0IEMuQlJBTkRfREFSS19HT0xEX0RFRVAgIT0gQy5CUkFORF9E"
    "QVJLX0dPTEQKCgpAcHl0ZXN0Lm1hcmsucGFyYW1ldHJpemUoImNvbnN0LHJnYiIsIFsK"
    "ICAgICgiQlJBTkRfR09MRCIsICJCUkFORF9HT0xEX1JHQiIpLAogICAgKCJCUkFORF9E"
    "QVJLX0dPTEQiLCAiQlJBTkRfREFSS19HT0xEX1JHQiIpLApdKQpkZWYgdGVzdF9yZ2Jf"
    "dHVwbGVfbWF0Y2hlc19pdHNfaGV4KGNvbnN0OiBzdHIsIHJnYjogc3RyKSAtPiBOb25l"
    "OgogICAgIiIiVGhlIFJHQi10dXBsZSBibGluZCBzcG90LgoKICAgIEEgaGFyZGNvZGVk"
    "ICgxNzcsIDE0NSwgNjkpIGlzIGludmlzaWJsZSB0byBldmVyeSBoZXgtYmFzZWQgc2Vh"
    "cmNoLCBzbwogICAgaXQgc3Vydml2ZXMgc3dlZXBzIHRoYXQgY2F0Y2ggZXZlcnkgb3Ro"
    "ZXIgcmVmZXJlbmNlIHRvIHRoZSBjb2xvdXIuCiAgICBEZXJpdmluZyBpdCByZW1vdmVz"
    "IHRoZSBoaWRpbmcgcGxhY2U7IHRoaXMgdGVzdCBrZWVwcyBpdCByZW1vdmVkLgogICAg"
    "IiIiCiAgICByLCBnLCBiID0gZ2V0YXR0cihDLCByZ2IpCiAgICBhc3NlcnQgZ2V0YXR0"
    "cihDLCBjb25zdCkubG93ZXIoKSA9PSBmIiN7cjowMnh9e2c6MDJ4fXtiOjAyeH0iCgoK"
    "ZGVmIHRlc3RfbGlnaHRlbl9wcmVzZXJ2ZXNfaHVlX2J5X3NoaWZ0aW5nX2NoYW5uZWxz"
    "X3VuaWZvcm1seSgpIC0+IE5vbmU6CiAgICBiYXNlID0gIiM4YzczMzciCiAgICBvdXQg"
    "PSBDLmxpZ2h0ZW4oYmFzZSwgLTE0KQogICAgYnIsIGJnXywgYmIgPSBDLl90b19yZ2Io"
    "YmFzZSkKICAgIG9yciwgb2csIG9iID0gQy5fdG9fcmdiKG91dCkKICAgIGFzc2VydCAo"
    "YnIgLSBvcnIsIGJnXyAtIG9nLCBiYiAtIG9iKSA9PSAoMTQsIDE0LCAxNCkKCgpkZWYg"
    "dGVzdF9saWdodGVuX2NsYW1wc19pbnN0ZWFkX29mX3dyYXBwaW5nKCkgLT4gTm9uZToK"
    "ICAgIGFzc2VydCBDLmxpZ2h0ZW4oIiNmZmZmZmYiLCA0MCkgPT0gIiNmZmZmZmYiCiAg"
    "ICBhc3NlcnQgQy5saWdodGVuKCIjMDAwMDAwIiwgLTQwKSA9PSAiIzAwMDAwMCIKCgoj"
    "IOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkAojIFBBSVJJTkcgQVVESVQKIyDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZAKCiMgUGFpcnMgdGhhdCByZW5kZXIgYmVsb3cgdGhlIGZsb29yIG9uIHB1cnBv"
    "c2UsIGVhY2ggd2l0aCB0aGUgcmVhc29uLgojIEJvdGggaGFsdmVzIG9mIHRoaXMgZGlj"
    "dCBhcmUgYXNzZXJ0ZWQgLS0gc2VlIHRoZSBtb2R1bGUgZG9jc3RyaW5nLgpBQ0NFUFRF"
    "RDogZGljdFt0dXBsZVtzdHIsIHN0cl0sIHN0cl0gPSB7CiAgICAoIiMwMDAwMDAiLCAi"
    "IzMzMzMzMyIpOgogICAgICAgICJtYWluLXdpbmRvdyBidXR0b24gaG92ZXIuIFRoZSBt"
    "YWluIHdpbmRvdyB1c2VzIGEgd2hpdGUvbmVhci1ibGFjayAiCiAgICAgICAgImludmVy"
    "c2Ugc2NoZW1lIGluIHdoaWNoIHRoZSB0ZXh0IHN0YXlzIGJsYWNrIHdoaWxlIHRoZSBi"
    "YWNrZ3JvdW5kICIKICAgICAgICAiZGFya2VuczsgdGhpcyBpcyB0aGUgYXBwJ3MgZGVs"
    "aWJlcmF0ZSBkZXNpZ24sIG5vdCBhbiBvdmVyc2lnaHQsICIKICAgICAgICAiYW5kIGl0"
    "IGlzIHNlcGFyYXRlIGZyb20gdGhlIGdvbGQgZGlhbG9nLWJ1dHRvbiBzY2hlbWUuIiwK"
    "ICAgICgiIzAwMDAwMCIsICIjNDQ0NDQ0Iik6CiAgICAgICAgIm1haW4td2luZG93IGJ1"
    "dHRvbiBwcmVzc2VkLCBzYW1lIGludmVyc2Ugc2NoZW1lLiIsCiAgICAoIiNmZmZmZmYi"
    "LCAiI2QyYmM5MyIpOgogICAgICAgICJCUkFORF9HT0xEIGFzIGEgbGlzdC1pdGVtIGZp"
    "bGwgd2l0aCB3aGl0ZSB0ZXh0LiBCUkFORF9HT0xEIGlzIGEgIgogICAgICAgICJyZWdp"
    "c3RlcmVkIHZhbHVlIGFuZCBpcyBub3QgaW4gc2NvcGUgZm9yIHRoZSBkYXJrLWdvbGQg"
    "YWxpZ25tZW50LiAiCiAgICAgICAgIlJlY29yZGVkIGhlcmUgc28gaXQgc3RheXMgdmlz"
    "aWJsZSByYXRoZXIgdGhhbiBmb3Jnb3R0ZW4uIiwKICAgICgiI2FhYWFhYSIsICIjZmZm"
    "ZmZmIik6CiAgICAgICAgImRpc2FibGVkIGNvbnRyb2wgdGV4dC4gV0NBRyAxLjQuMyBl"
    "eGVtcHRzIGRpc2FibGVkIGNvbnRyb2xzLiIsCiAgICAoIiM1NTU1NTUiLCAiIzFhMWEx"
    "YSIpOgogICAgICAgICJkaXNhYmxlZCBjb250cm9sIHRleHQsIGRhcmsgdGhlbWUuIFNh"
    "bWUgZXhlbXB0aW9uLiIsCiAgICAoIiM2NjY2NjYiLCAiI2UwZTBlMCIpOgogICAgICAg"
    "ICJPUy1zaW11bGF0aW9uIGNocm9tZSBpbiBjb250ZXh0X3ByZXZpZXcucHksIHdoaWNo"
    "IHJlcHJvZHVjZXMgIgogICAgICAgICJwbGF0Zm9ybSBVSSBzbyB1c2VycyBjYW4gcHJl"
    "dmlldyBhbiBpY29uIGluIHNpdHUuIEl0IG11c3QgbWF0Y2ggIgogICAgICAgICJ0aGUg"
    "cGxhdGZvcm0sIG5vdCB0aGUgYnJhbmQuIiwKICAgICgiIzg4ODg4OCIsICIjMmEyYTJh"
    "Iik6CiAgICAgICAgIk9TLXNpbXVsYXRpb24gY2hyb21lLCBkYXJrLiBTYW1lIHJlYXNv"
    "bi4iLAp9CgpfSEVYID0gcmUuY29tcGlsZShyIiMoPzpbMC05YS1mQS1GXXszfXxbMC05"
    "YS1mQS1GXXs2fSlcYiIpCgojIFRoZSBRU1MgbGl2ZXMgaW5zaWRlIGYtc3RyaW5ncywg"
    "c28gaXRzIGJyYWNlcyBhcmUgZG91YmxlZC4gTWF0Y2hpbmcgc2luZ2xlCiMgYnJhY2Vz"
    "IGhlcmUgZmluZHMgbm90aGluZyBhdCBhbGwgLS0gYW5kIGZpbmRpbmcgbm90aGluZyBy"
    "ZWFkcyBleGFjdGx5IGxpa2UKIyBmaW5kaW5nIG5vIGRlZmVjdHMsIHdoaWNoIGlzIHdo"
    "eSB0ZXN0X3RoZV9hdWRpdF9maW5kc19zb21ldGhpbmdfdG9fYXVkaXQKIyBleGlzdHMg"
    "YmVsb3cuCiMKCmRlZiBfcnVsZXMoc3JjOiBzdHIpIC0+IGxpc3RbdHVwbGVbc3RyLCBz"
    "dHJdXToKICAgICIiIllpZWxkIChzZWxlY3RvciwgYm9keSkgZm9yIGVhY2ggUVNTIHJ1"
    "bGUgaW4gb25lIHNvdXJjZSBmaWxlLgoKICAgIERlbGliZXJhdGVseSBhIHNjYW4gcmF0"
    "aGVyIHRoYW4gYSByZWdleC4gVGhlIG9idmlvdXMgcGF0dGVybiwKICAgIGBgKFtee31d"
    "Kz8pXFx7XFx7KC4qPylcXH1cXH1gYCwgYmFja3RyYWNrcyBxdWFkcmF0aWNhbGx5IG9u"
    "IGZpbGVzIHRoaXMKICAgIHNpemUgLS0gaXQgdG9vayBmb3J0eSBzZWNvbmRzIHBlciBw"
    "YXNzLiBUaGUgb2J2aW91cyBmaXgsIHRpZ2h0ZW5pbmcgdGhlCiAgICBib2R5IHRvIGBg"
    "W157fV0qYGAsIGlzIHdyb25nIGZvciBhIGRpZmZlcmVudCByZWFzb246IFFTUyBib2Rp"
    "ZXMgYXJlIGZ1bGwKICAgIG9mIGYtc3RyaW5nIHBsYWNlaG9sZGVycyBsaWtlIGBge2Nb"
    "J3RhYl9iZyddfWBgLCBzbyBhIGJyYWNlLWZyZWUgYm9keQogICAgY2xhc3Mgc3RvcHMg"
    "ZGVhZCBhdCB0aGUgZmlyc3Qgb25lIGFuZCBmaW5kcyBhIGZyYWN0aW9uIG9mIHRoZSBy"
    "dWxlcy4KICAgIEZpbmRpbmcgYSBmcmFjdGlvbiBvZiB0aGUgcnVsZXMgcmVhZHMgZXhh"
    "Y3RseSBsaWtlIGZpbmRpbmcgbm8gZGVmZWN0cywKICAgIHdoaWNoIGlzIHdoYXQgdGVz"
    "dF90aGVfYXVkaXRfZmluZHNfc29tZXRoaW5nX3RvX2F1ZGl0IGlzIHRoZXJlIHRvIGNh"
    "dGNoLgoKICAgIFRoZSBzZWxlY3RvciBpcyB0aGUgbGFzdCBsaW5lIG9mIHRleHQgYmV0"
    "d2VlbiB0aGUgZW5kIG9mIHRoZSBwcmV2aW91cwogICAgYmxvY2sgYW5kIHRoZSBzdGFy"
    "dCBvZiB0aGlzIG9uZSwgd2hpY2ggaXMgd2hlcmUgUXQncyBzZWxlY3RvciBzaXRzLgog"
    "ICAgIiIiCiAgICBvdXQgPSBbXQogICAgY3Vyc29yID0gMAogICAgd2hpbGUgVHJ1ZToK"
    "ICAgICAgICBzdGFydCA9IHNyYy5maW5kKCJ7eyIsIGN1cnNvcikKICAgICAgICBpZiBz"
    "dGFydCA9PSAtMToKICAgICAgICAgICAgYnJlYWsKICAgICAgICBlbmQgPSBzcmMuZmlu"
    "ZCgifX0iLCBzdGFydCArIDIpCiAgICAgICAgaWYgZW5kID09IC0xOgogICAgICAgICAg"
    "ICBicmVhawogICAgICAgIGxlYWQgPSBzcmNbY3Vyc29yOnN0YXJ0XS5zdHJpcCgpCiAg"
    "ICAgICAgc2VsZWN0b3IgPSBsZWFkLnNwbGl0bGluZXMoKVstMV0uc3RyaXAoKSBpZiBs"
    "ZWFkIGVsc2UgIiIKICAgICAgICBvdXQuYXBwZW5kKChzZWxlY3Rvciwgc3JjW3N0YXJ0"
    "ICsgMjplbmRdKSkKICAgICAgICBjdXJzb3IgPSBlbmQgKyAyCiAgICByZXR1cm4gb3V0"
    "CgoKZGVmIF9ub3JtYWxpc2UoaGV4X2NvbG9yOiBzdHIpIC0+IHN0cjoKICAgIGggPSBo"
    "ZXhfY29sb3IubHN0cmlwKCIjIikKICAgIGlmIGxlbihoKSA9PSAzOgogICAgICAgIGgg"
    "PSAiIi5qb2luKGMgKiAyIGZvciBjIGluIGgpCiAgICByZXR1cm4gIiMiICsgaC5sb3dl"
    "cigpCgoKZGVmIF9yZXNvbHZlKHRva2VuOiBzdHIsIHBhbGV0dGU6IGRpY3Rbc3RyLCBz"
    "dHJdKSAtPiBzdHIgfCBOb25lOgogICAgIiIiVHVybiBvbmUgUVNTIHZhbHVlIGludG8g"
    "YSBjb25jcmV0ZSBoZXgsIG9yIE5vbmUgaWYgaXQgaXMgbm90IG9uZS4iIiIKICAgIHRv"
    "a2VuID0gdG9rZW4uc3RyaXAoKS5yc3RyaXAoIjsiKS5zdHJpcCgpCiAgICBpZiBfSEVY"
    "LmZ1bGxtYXRjaCh0b2tlbik6CiAgICAgICAgcmV0dXJuIF9ub3JtYWxpc2UodG9rZW4p"
    "CiAgICAjIHtjWydrZXknXX0gLyB7Y29sb3JzWydrZXknXX0gLyB7dGhlbWVbJ2tleSdd"
    "fQogICAgbSA9IHJlLmZ1bGxtYXRjaChyIlx7XHMqXHcrXFtbJ1wiXShbXHdcLV0rKVsn"
    "XCJdXF1ccypcfSIsIHRva2VuKQogICAgaWYgbToKICAgICAgICB2ID0gcGFsZXR0ZS5n"
    "ZXQobS5ncm91cCgxKSkKICAgICAgICByZXR1cm4gX25vcm1hbGlzZSh2KSBpZiBpc2lu"
    "c3RhbmNlKHYsIHN0cikgYW5kIF9IRVguZnVsbG1hdGNoKHYpIGVsc2UgTm9uZQogICAg"
    "IyBiYXJlIHtDT05TVEFOVH0KICAgIG0gPSByZS5mdWxsbWF0Y2gociJce1xzKihbQS1a"
    "X11bQS1aMC05X10qKVxzKlx9IiwgdG9rZW4pCiAgICBpZiBtOgogICAgICAgIHYgPSBn"
    "ZXRhdHRyKEMsIG0uZ3JvdXAoMSksIE5vbmUpCiAgICAgICAgcmV0dXJuIF9ub3JtYWxp"
    "c2UodikgaWYgaXNpbnN0YW5jZSh2LCBzdHIpIGFuZCBfSEVYLmZ1bGxtYXRjaCh2KSBl"
    "bHNlIE5vbmUKICAgIHJldHVybiBOb25lCgoKZGVmIF90cmFja2VkX3B5dGhvbl9maWxl"
    "cygpIC0+IGxpc3RbUGF0aF06CiAgICAiIiJFbnVtZXJhdGUgZnJvbSBnaXQgcmF0aGVy"
    "IHRoYW4gZnJvbSBhIGxpc3Qgd3JpdHRlbiBkb3duIGhlcmUuCgogICAgQSBoYXJkY29k"
    "ZWQgZmlsZSBsaXN0IGdvZXMgc3RhbGUgdGhlIG1vbWVudCBhIG1vZHVsZSBpcyBhZGRl"
    "ZCwgYW5kIGl0CiAgICBnb2VzIHN0YWxlIGluIHRoZSBkaXJlY3Rpb24gdGhhdCByZXBv"
    "cnRzIGNsZWFuLgogICAgIiIiCiAgICByID0gc3VicHJvY2Vzcy5ydW4oWyJnaXQiLCAi"
    "bHMtZmlsZXMiLCAiLXoiLCAiKi5weSJdLAogICAgICAgICAgICAgICAgICAgICAgIGN3"
    "ZD1QUk9KRUNUX1JPT1QsIGNhcHR1cmVfb3V0cHV0PVRydWUsIHRleHQ9VHJ1ZSkKICAg"
    "IGlmIHIucmV0dXJuY29kZSAhPSAwOiAgICAgICAgICAgICAgICAgICAgICAgIyBub3Qg"
    "YSBnaXQgY2hlY2tvdXQKICAgICAgICByZXR1cm4gc29ydGVkKHAgZm9yIHAgaW4gUFJP"
    "SkVDVF9ST09ULnJnbG9iKCIqLnB5IikKICAgICAgICAgICAgICAgICAgICAgIGlmICJf"
    "X3B5Y2FjaGVfXyIgbm90IGluIHAucGFydHMpCiAgICByZXR1cm4gc29ydGVkKChQUk9K"
    "RUNUX1JPT1QgLyBuKSBmb3IgbiBpbiByLnN0ZG91dC5zcGxpdCgiXDAiKQogICAgICAg"
    "ICAgICAgICAgICBpZiBuIGFuZCAoUFJPSkVDVF9ST09UIC8gbikuZXhpc3RzKCkpCgoK"
    "QGZ1bmN0b29scy5scnVfY2FjaGUobWF4c2l6ZT0xKQpkZWYgX3NvdXJjZXMoKSAtPiB0"
    "dXBsZVt0dXBsZVtzdHIsIHN0cl0sIC4uLl06CiAgICAiIiIocmVsYXRpdmUgcGF0aCwg"
    "dGV4dCkgZm9yIGV2ZXJ5IHRyYWNrZWQgUHl0aG9uIGZpbGUsIHJlYWQgb25jZS4iIiIK"
    "ICAgIHJldHVybiB0dXBsZSgoc3RyKHAucmVsYXRpdmVfdG8oUFJPSkVDVF9ST09UKSks"
    "CiAgICAgICAgICAgICAgICAgIHAucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIsIGVy"
    "cm9ycz0iaWdub3JlIikpCiAgICAgICAgICAgICAgICAgZm9yIHAgaW4gX3RyYWNrZWRf"
    "cHl0aG9uX2ZpbGVzKCkpCgoKZGVmIGF1ZGl0X3BhbGV0dGUocGFsZXR0ZTogZGljdFtz"
    "dHIsIHN0cl0pIC0+IGxpc3RbdHVwbGVbc3RyLCBzdHIsIGZsb2F0LCBzdHJdXToKICAg"
    "IGZpbmRpbmdzID0gW10KICAgIGZvciByZWwsIHNyYyBpbiBfc291cmNlcygpOgogICAg"
    "ICAgIGZvciBzZWxlY3RvciwgYm9keSBpbiBfcnVsZXMoc3JjKToKICAgICAgICAgICAg"
    "ZmcgPSBiZyA9IE5vbmUKICAgICAgICAgICAgZm9yIGRlY2wgaW4gYm9keS5zcGxpdCgi"
    "OyIpOgogICAgICAgICAgICAgICAgaWYgIjoiIG5vdCBpbiBkZWNsOgogICAgICAgICAg"
    "ICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgICAgICBwcm9wLCBfLCB2YWx1ZSA9"
    "IGRlY2wucGFydGl0aW9uKCI6IikKICAgICAgICAgICAgICAgIHByb3AgPSBwcm9wLnN0"
    "cmlwKCkKICAgICAgICAgICAgICAgIGlmIHByb3AgPT0gImNvbG9yIjoKICAgICAgICAg"
    "ICAgICAgICAgICBmZyA9IF9yZXNvbHZlKHZhbHVlLCBwYWxldHRlKQogICAgICAgICAg"
    "ICAgICAgZWxpZiBwcm9wIGluICgiYmFja2dyb3VuZC1jb2xvciIsICJiYWNrZ3JvdW5k"
    "Iik6CiAgICAgICAgICAgICAgICAgICAgYmcgPSBfcmVzb2x2ZSh2YWx1ZSwgcGFsZXR0"
    "ZSkKICAgICAgICAgICAgaWYgZmcgYW5kIGJnOgogICAgICAgICAgICAgICAgcmF0aW8g"
    "PSBjb250cmFzdF9yYXRpbyhmZywgYmcpCiAgICAgICAgICAgICAgICBpZiByYXRpbyA8"
    "IFRFWFRfRkxPT1I6CiAgICAgICAgICAgICAgICAgICAgZmluZGluZ3MuYXBwZW5kKChm"
    "ZywgYmcsIHJvdW5kKHJhdGlvLCA0KSwKICAgICAgICAgICAgICAgICAgICAgICAgICAg"
    "ICAgICAgICAgIGYie3JlbH0gOjoge3NlbGVjdG9yfSIpKQogICAgcmV0dXJuIGZpbmRp"
    "bmdzCgoKZGVmIHRlc3RfdGhlX2F1ZGl0X2ZpbmRzX3NvbWV0aGluZ190b19hdWRpdCgp"
    "IC0+IE5vbmU6CiAgICAiIiJHdWFyZCB0aGUgZ3VhcmQuCgogICAgSWYgdGhlIFFTUyBm"
    "b3JtYXQgY2hhbmdlcyBhbmQgdGhlIHJ1bGUgcmVnZXggc3RvcHMgbWF0Y2hpbmcsIGV2"
    "ZXJ5CiAgICBjb250cmFzdCB0ZXN0IGJlbG93IHBhc3NlcyB2YWN1b3VzbHkuIFRoaXMg"
    "YXNzZXJ0cyB0aGUgd2Fsa2VyIGlzIHN0aWxsCiAgICByZWFjaGluZyByZWFsIHJ1bGVz"
    "LgogICAgIiIiCiAgICB0b3RhbCA9IHN1bShsZW4oX3J1bGVzKHNyYykpIGZvciBfcmVs"
    "LCBzcmMgaW4gX3NvdXJjZXMoKSkKICAgIGFzc2VydCB0b3RhbCA+IDEwMCwgKAogICAg"
    "ICAgIGYidGhlIFFTUyB3YWxrZXIgbWF0Y2hlZCBvbmx5IHt0b3RhbH0gcnVsZXMgYWNy"
    "b3NzIHRoZSByZXBvc2l0b3J5LCAiCiAgICAgICAgZiJ3aGljaCBtZWFucyBpdCBoYXMg"
    "c3RvcHBlZCBwYXJzaW5nIHRoZSBzdHlsZXNoZWV0cyByYXRoZXIgdGhhbiAiCiAgICAg"
    "ICAgZiJ0aGF0IHRoZSBzdHlsZXNoZWV0cyBnb3Qgc21hbGxlciIpCgoKQHB5dGVzdC5t"
    "YXJrLnBhcmFtZXRyaXplKCJ0aGVtZV9uYW1lIiwgWyJMSUdIVCIsICJEQVJLIl0pCmRl"
    "ZiB0ZXN0X25vX3VuYWNjZXB0ZWRfY29udHJhc3RfZmFpbHVyZXModGhlbWVfbmFtZTog"
    "c3RyKSAtPiBOb25lOgogICAgcGFsZXR0ZSA9IChDLkxJR0hUX1RIRU1FX0NPTE9SUyBp"
    "ZiB0aGVtZV9uYW1lID09ICJMSUdIVCIKICAgICAgICAgICAgICAgZWxzZSBDLkRBUktf"
    "VEhFTUVfQ09MT1JTKQogICAgYmFkID0gW2YgZm9yIGYgaW4gYXVkaXRfcGFsZXR0ZShw"
    "YWxldHRlKSBpZiAoZlswXSwgZlsxXSkgbm90IGluIEFDQ0VQVEVEXQogICAgYXNzZXJ0"
    "IG5vdCBiYWQsICJcbiIuam9pbigKICAgICAgICBmIiAge3I6Pjd9OjEgIHtmZ30gb24g"
    "e2JnfSAgPC0ge3doZXJlfSIgZm9yIGZnLCBiZywgciwgd2hlcmUgaW4gYmFkKQoKCmRl"
    "ZiB0ZXN0X2V2ZXJ5X2V4ZW1wdGlvbl9zdGlsbF9hcHBsaWVzKCkgLT4gTm9uZToKICAg"
    "ICIiIlRoZSBoYWxmIHRoYXQgbWF0dGVycy4KCiAgICBBbiBleGVtcHRpb24gZm9yIGEg"
    "cGFpcmluZyB0aGF0IG5vIGxvbmdlciBleGlzdHMgaXMgYW4gZXhlbXB0aW9uIHRoYXQK"
    "ICAgIHdpbGwgc2lsZW50bHkgY292ZXIgYSBmdXR1cmUgZGVmZWN0LiBSZW1vdmluZyBk"
    "ZWFkIGVudHJpZXMga2VlcHMgdGhlCiAgICBsaXN0IGhvbmVzdC4KICAgICIiIgogICAg"
    "c2VlbiA9IHNldCgpCiAgICBmb3IgcGFsZXR0ZSBpbiAoQy5MSUdIVF9USEVNRV9DT0xP"
    "UlMsIEMuREFSS19USEVNRV9DT0xPUlMpOgogICAgICAgIGZvciBmZywgYmcsIF9yLCBf"
    "dyBpbiBhdWRpdF9wYWxldHRlKHBhbGV0dGUpOgogICAgICAgICAgICBzZWVuLmFkZCgo"
    "ZmcsIGJnKSkKICAgIGRlYWQgPSBzb3J0ZWQoayBmb3IgayBpbiBBQ0NFUFRFRCBpZiBr"
    "IG5vdCBpbiBzZWVuKQogICAgYXNzZXJ0IG5vdCBkZWFkLCAoCiAgICAgICAgInRoZXNl"
    "IGV4ZW1wdGlvbnMgbm8gbG9uZ2VyIG1hdGNoIGFueXRoaW5nIHRoZSBhcHAgcmVuZGVy"
    "cyBhbmQgIgogICAgICAgIGYic2hvdWxkIGJlIGRlbGV0ZWQ6IHtkZWFkfSIpCgoKIyDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZAKIyBUSEUgVFdPIEdPTEQgUk9MRVMKIyDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZAKIwojIExpZ2h0IG1vZGUgdXNlcyBleGFjdGx5IHR3byBnb2xkcywgYmVj"
    "YXVzZSBvbmUgY2Fubm90IGRvIGJvdGggam9iczogYQojIGdvbGQgbGlnaHQgZW5vdWdo"
    "IHRvIGNhcnJ5IHdoaXRlIHRleHQgYXQgNC41OjEgaXMgdG9vIGxpZ2h0IHRvIEJFIHRl"
    "eHQKIyBvbiBhbnl0aGluZyBidXQgcHVyZSB3aGl0ZS4gVGhlIGx1bWluYW5jZSBiYW5k"
    "cyBkbyBub3Qgb3ZlcmxhcC4KCkxJR0hUX1NVUkZBQ0VTID0gWyIjZmZmZmZmIiwgIiNm"
    "YWZhZmEiLCAiI2Y1ZjVmNSIsICIjZjBmMGYwIiwgIiNlZWVlZWUiXQoKCmRlZiB0ZXN0"
    "X2ZpbGxfZ29sZF9jYXJyaWVzX3doaXRlX3RleHQoKSAtPiBOb25lOgogICAgYXNzZXJ0"
    "IGNvbnRyYXN0X3JhdGlvKCIjZmZmZmZmIiwgQy5CUkFORF9EQVJLX0dPTEQpID49IFRF"
    "WFRfRkxPT1IKCgpkZWYgdGVzdF90ZXh0X2dvbGRfY2xlYXJzX2V2ZXJ5X2xpZ2h0X3N1"
    "cmZhY2UoKSAtPiBOb25lOgogICAgZmFpbHVyZXMgPSBbKHMsIHJvdW5kKGNvbnRyYXN0"
    "X3JhdGlvKEMuQlJBTkRfREFSS19HT0xEX0RFRVAsIHMpLCA0KSkKICAgICAgICAgICAg"
    "ICAgIGZvciBzIGluIExJR0hUX1NVUkZBQ0VTCiAgICAgICAgICAgICAgICBpZiBjb250"
    "cmFzdF9yYXRpbyhDLkJSQU5EX0RBUktfR09MRF9ERUVQLCBzKSA8IFRFWFRfRkxPT1Jd"
    "CiAgICBhc3NlcnQgbm90IGZhaWx1cmVzLCAoCiAgICAgICAgZiJ0aGUgdGV4dCBnb2xk"
    "IG5vIGxvbmdlciBjbGVhcnMgZXZlcnkgbGlnaHQgc3VyZmFjZToge2ZhaWx1cmVzfSIp"
    "CgoKQHB5dGVzdC5tYXJrLnBhcmFtZXRyaXplKCJrZXkiLCBbCiAgICAidGV4dF9hY2Nl"
    "bnQiLCAiYnV0dG9uX2hvdmVyX3RleHQiLCAiYWNjZW50X2J1dHRvbl90ZXh0IiwKXSkK"
    "ZGVmIHRlc3RfZ29sZF90ZXh0X2tleXNfdXNlX3RoZV90ZXh0X2dvbGQoa2V5OiBzdHIp"
    "IC0+IE5vbmU6CiAgICBhc3NlcnQgQy5MSUdIVF9USEVNRV9DT0xPUlNba2V5XSA9PSBD"
    "LkJSQU5EX0RBUktfR09MRF9ERUVQCgoKQHB5dGVzdC5tYXJrLnBhcmFtZXRyaXplKCJr"
    "ZXkiLCBbCiAgICAic2VsZWN0ZWRfYmciLCAiYnV0dG9uX3ByZXNzZWRfYmciLCAiYWNj"
    "ZW50X2J1dHRvbl9wcmVzc2VkX2JnIiwKICAgICJjaGVja2JveF9jaGVja2VkX2JnIiwg"
    "Imxpc3Rfc2VsZWN0ZWRfYmciLApdKQpkZWYgdGVzdF9nb2xkX2ZpbGxfa2V5c191c2Vf"
    "dGhlX2ZpbGxfZ29sZChrZXk6IHN0cikgLT4gTm9uZToKICAgICIiIkZpbGxzIG11c3Qg"
    "bm90IHRha2UgdGhlIHRleHQgZ29sZDogaXQgZG9lcyBub3QgY2Fycnkgd2hpdGUgdGV4"
    "dC4iIiIKICAgIGFzc2VydCBDLkxJR0hUX1RIRU1FX0NPTE9SU1trZXldID09IEMuQlJB"
    "TkRfREFSS19HT0xECgoKZGVmIHRlc3RfdGFiX2hvdmVyX2dyb3VuZF9pc19saWdodF9l"
    "bm91Z2hfZm9yX2dvbGRfdGV4dCgpIC0+IE5vbmU6CiAgICAiIiJUaGUgaG92ZXIgdGFi"
    "IHJlYWRzIGFzIGhvdmVyIGJlY2F1c2UgdGhlIGdyb3VuZCBMSUdIVEVOUyB0b3dhcmQg"
    "dGhlCiAgICBzZWxlY3RlZCB0YWIncyB3aGl0ZSwgYW5kIHRoZSBnb2xkIHRleHQgc3Rh"
    "eXMgbGVnaWJsZSBvbiBpdC4iIiIKICAgIGdyb3VuZCA9IEMuTElHSFRfVEhFTUVfQ09M"
    "T1JTWyJ0YWJfaG92ZXJfYmciXQogICAgcmVzdCA9IEMuTElHSFRfVEhFTUVfQ09MT1JT"
    "WyJ0YWJfYmciXQogICAgYXNzZXJ0IHJlbGF0aXZlX2x1bWluYW5jZShncm91bmQpID4g"
    "cmVsYXRpdmVfbHVtaW5hbmNlKHJlc3QpCiAgICBhc3NlcnQgY29udHJhc3RfcmF0aW8o"
    "Qy5MSUdIVF9USEVNRV9DT0xPUlNbInRleHRfYWNjZW50Il0sCiAgICAgICAgICAgICAg"
    "ICAgICAgICAgICAgZ3JvdW5kKSA+PSBURVhUX0ZMT09SCgoKZGVmIHRlc3RfdGFiX2lu"
    "ZGljYXRvcl9jbGVhcnNfdGhlX2NvbXBvbmVudF9mbG9vcigpIC0+IE5vbmU6CiAgICBh"
    "c3NlcnQgY29udHJhc3RfcmF0aW8oQy5MSUdIVF9USEVNRV9DT0xPUlNbInRhYl9pbmRp"
    "Y2F0b3IiXSwKICAgICAgICAgICAgICAgICAgICAgICAgICBDLkxJR0hUX1RIRU1FX0NP"
    "TE9SU1sidGFiX3NlbGVjdGVkX2JnIl0KICAgICAgICAgICAgICAgICAgICAgICAgICAp"
    "ID49IENPTVBPTkVOVF9GTE9PUgoKCiMg4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQCiMgU0NIRU1F"
    "IFNFUEFSQVRJT04KIyDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZAKIwojIFRoZSBhcHAgcnVucyB0"
    "d28gYnV0dG9uIHNjaGVtZXMgc2lkZSBieSBzaWRlLiBDb25mbGF0aW5nIHRoZW0gaXMg"
    "dGhlCiMgZWFzaWVzdCB3YXkgdG8gImZpeCIgb25lIGJ5IGJyZWFraW5nIHRoZSBvdGhl"
    "ci4KCkBweXRlc3QubWFyay5wYXJhbWV0cml6ZSgicGFsZXR0ZV9uYW1lIiwgWyJMSUdI"
    "VCIsICJEQVJLIl0pCmRlZiB0ZXN0X21haW5fYnV0dG9uX3NjaGVtZV9ob2xkc19ub19n"
    "b2xkKHBhbGV0dGVfbmFtZTogc3RyKSAtPiBOb25lOgogICAgIiIiTWFpbi13aW5kb3cg"
    "YnV0dG9ucyBhcmUgdGhlIHdoaXRlL25lYXItYmxhY2sgaW52ZXJzZSBzeXN0ZW0uIE5v"
    "CiAgICBicmFuZCBnb2xkIGJlbG9uZ3MgYW55d2hlcmUgaW4gdGhlbS4iIiIKICAgIHBh"
    "bGV0dGUgPSAoQy5MSUdIVF9USEVNRV9DT0xPUlMgaWYgcGFsZXR0ZV9uYW1lID09ICJM"
    "SUdIVCIKICAgICAgICAgICAgICAgZWxzZSBDLkRBUktfVEhFTUVfQ09MT1JTKQogICAg"
    "Z29sZHMgPSB7Qy5CUkFORF9HT0xELmxvd2VyKCksIEMuQlJBTkRfREFSS19HT0xELmxv"
    "d2VyKCksCiAgICAgICAgICAgICBDLkJSQU5EX0RBUktfR09MRF9ERUVQLmxvd2VyKCl9"
    "CiAgICBvZmZlbmRlcnMgPSB7azogdiBmb3IgaywgdiBpbiBwYWxldHRlLml0ZW1zKCkK"
    "ICAgICAgICAgICAgICAgICBpZiBrLnN0YXJ0c3dpdGgoIm1haW5fYnRuXyIpIGFuZCB2"
    "Lmxvd2VyKCkgaW4gZ29sZHN9CiAgICBhc3NlcnQgbm90IG9mZmVuZGVycywgKAogICAg"
    "ICAgIGYiZ29sZCBsZWFrZWQgaW50byB0aGUgbWFpbi13aW5kb3cgYnV0dG9uIHNjaGVt"
    "ZToge29mZmVuZGVyc30iKQoKCmRlZiB0ZXN0X3JldGlyZWRfYXBwX2dvbGRfaXNfZ29u"
    "ZSgpIC0+IE5vbmU6CiAgICAiIiIjYjE5MTQ1IHdhcyBhbiBhcHAtbG9jYWwgYXBwcm94"
    "aW1hdGlvbiBvZiB0aGUgYnJhbmQgZGFyayBnb2xkLiBJdAogICAgY2FycmllZCB3aGl0"
    "ZSB0ZXh0IGF0IDIuOTk3NjoxLiBOb3RoaW5nIHNob3VsZCByZWludHJvZHVjZSBpdC4i"
    "IiIKICAgIGZvciBwYWxldHRlIGluIChDLkxJR0hUX1RIRU1FX0NPTE9SUywgQy5EQVJL"
    "X1RIRU1FX0NPTE9SUywKICAgICAgICAgICAgICAgICAgICBDLklNQUdFX01PREVfQ09M"
    "T1JTKToKICAgICAgICBhc3NlcnQgbm90IFtrIGZvciBrLCB2IGluIHBhbGV0dGUuaXRl"
    "bXMoKQogICAgICAgICAgICAgICAgICAgIGlmIGlzaW5zdGFuY2Uodiwgc3RyKSBhbmQg"
    "di5sb3dlcigpID09ICIjYjE5MTQ1Il0K"
)

FAIL = "\033[31m"
OK = "\033[32m"
WARN = "\033[33m"
OFF = "\033[0m"


SELF = Path(__file__).resolve()

# Any file containing this marker is this script, whatever it has been
# renamed to. Excluding by path alone is not enough: this tool is normally
# committed to the repository under a working name (up.py) so it can be
# pulled into a codespace, so a tracked copy of it exists during the run.
# If a copy is swept, it rewrites its own OLD_GOLD constant into the new
# gold and destroys its definition of what it is looking for.
TOOL_MARKER = "RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP"

# The same idea, one step further out. A guard test's job is to NAME the
# retired values and assert they never return, so it is the one file that
# must contain them. Sweeping it rewrites "#b19145 must never appear" into
# "#8c7337 must never appear" -- a test that now forbids the correct value
# while the retired one walks back in unchallenged. Flagging it as stale is
# the milder version of the same confusion, and it is what a first pass at
# this verifier did.
#
# The rule these two markers share: any tool that hunts for a value must
# exclude every file whose purpose is to talk about that value.
GUARD_MARKER = "RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN"


def say(msg: str, colour: str = "") -> None:
    print(f"{colour}{msg}{OFF}" if colour else msg)


def tracked(*suffixes: str) -> list[Path]:
    """Files git tracks, minus this script.

    Two reasons this is not a glob. First, a glob picks up scratch files,
    virtualenvs and -- as this script learned the hard way -- the script
    itself: a sweep that rewrites its own OLD_VALUE constant into the new
    value destroys its own definition of what it is looking for. Second,
    git's index is the repository's own answer to "what is in this project",
    so it cannot drift away from the thing being changed.
    """
    r = subprocess.run(["git", "ls-files", "-z"], cwd=REPO,
                       capture_output=True, text=True)
    if r.returncode != 0:
        die("git ls-files failed -- run this inside the repository.")
    out = []
    for name in r.stdout.split("\0"):
        if not name:
            continue
        p = (REPO / name).resolve()
        if p == SELF or not p.exists():
            continue
        if suffixes and p.suffix not in suffixes:
            continue
        if p.suffix == ".py":
            try:
                if TOOL_MARKER in p.read_text(encoding="utf-8", errors="ignore"):
                    continue          # a copy of this script under any name
            except OSError:
                pass
        out.append(p)
    return sorted(out)


def die(msg: str) -> None:
    say(f"ABORT: {msg}", FAIL)
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════
# CONTRAST
# ══════════════════════════════════════════════════════════════════════════

def _lum(h: str) -> float:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    l1, l2 = sorted([_lum(a), _lum(b)], reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


# ══════════════════════════════════════════════════════════════════════════
# PREFLIGHT
# ══════════════════════════════════════════════════════════════════════════

# The system libraries PyQt6 links against. Taken from this repository's own
# .github/workflows/tests-linux.yml, so the two cannot drift apart. A fresh
# codespace has the Python package but none of these, and PyQt6 then fails to
# load before QT_QPA_PLATFORM is ever consulted -- offscreen does not help,
# because the shared object cannot be opened at all.
QT_APT_PACKAGES = (
    "libegl1 libgl1 libglib2.0-0 libxkbcommon0 libdbus-1-3 libfontconfig1 "
    "libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 "
    "libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 "
    "libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0"
)


def diagnose(err: str) -> str | None:
    """Turn an import traceback into the command that fixes it.

    Environment failures are the cheapest class of problem to fix and the
    most expensive to read, because what the tool observes ("snapshots
    still carry the old gold") is several steps removed from what actually
    broke ("this box has no OpenGL").
    """
    m = re.search(r"ModuleNotFoundError: No module named '([^']+)'", err)
    if m:
        return (f"the Python package {m.group(1)!r} is not installed.\n\n"
                f"       Fix:\n"
                f"         pip install -r requirements-test.txt")
    m = re.search(r"ImportError: (lib[\w.+-]*\.so[.\d]*): cannot open shared "
                  r"object file", err)
    if m:
        return (f"PyQt6 cannot load: the system library {m.group(1)} is "
                f"missing.\n"
                f"       The Python package is installed; the C libraries it "
                f"links against are not.\n"
                f"       QT_QPA_PLATFORM=offscreen does not help -- the "
                f"shared object fails to open\n"
                f"       before any platform plugin is chosen.\n\n"
                f"       Fix, in one command:\n"
                f"         python {Path(__file__).name} --install-deps "
                f"--snapshots-only\n\n"
                f"       (--install-deps runs the same apt-get line this "
                f"repo's CI uses, then continues.)")
    return None


def install_system_deps() -> None:
    """Install the Qt system libraries, on request only.

    This exists because the alternative is pasting a nineteen-package
    apt-get line into a phone. It never runs unless --install-deps is
    passed explicitly: a tool that reaches for sudo on its own initiative
    is a tool you cannot trust in a repository you care about.
    """
    if os.name != "posix":
        die("--install-deps is for Debian/Ubuntu (codespaces, CI). On this "
            "platform, install the Qt runtime libraries by hand.")
    cmds = [
        ["sudo", "apt-get", "update"],
        ["sudo", "apt-get", "install", "-y", "--no-install-recommends",
         *QT_APT_PACKAGES.split()],
    ]
    for cmd in cmds:
        say(f"    $ {' '.join(cmd[:5])}{' ...' if len(cmd) > 5 else ''}")
        r = subprocess.run(cmd)
        if r.returncode != 0:
            die(f"'{' '.join(cmd[:3])}' exited {r.returncode}. If sudo is "
                f"unavailable here, run the install as root by hand:\n"
                f"         apt-get install -y --no-install-recommends "
                f"{QT_APT_PACKAGES}")
    say("system Qt libraries installed", OK)


def check_dependencies() -> None:
    """Refuse to start if the run cannot finish.

    Step 8 regenerates tests/snapshots.json by running the repository's own
    helper, and that helper needs both pytest and a loadable PyQt6. If
    either is absent the helper cannot run, the snapshots keep the retired
    gold, and the run aborts at the last step -- leaving the repository
    half-applied, every source change in place beside stale snapshots.

    So probe for real, in a subprocess, doing exactly what the helper does.
    An import that succeeds here is an import that will succeed there.
    Checking costs a second and turns a half-applied repository into a
    message with the working tree untouched.
    """
    probe = ("import pytest\n"
             "import os; os.environ.setdefault('QT_QPA_PLATFORM','offscreen')\n"
             "from PyQt6.QtWidgets import QApplication\n")
    r = subprocess.run([sys.executable, "-c", probe], cwd=REPO,
                       capture_output=True, text=True,
                       env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
    if r.returncode != 0:
        hint = diagnose(r.stderr) or (
            "the snapshot helper's imports fail in this environment:\n\n"
            + "\n".join(f"       {ln}" for ln in r.stderr.strip().splitlines()[-6:]))
        die(f"{hint}\n\n       Nothing has been changed.")
    say("preflight: dependencies present", OK)


def preflight() -> None:
    check_dependencies()
    if not COLORS.exists():
        die(f"{COLORS} not found -- run this from the repository root.")
    src = COLORS.read_text(encoding="utf-8")
    if NEW_SYM in src and OLD_SYM not in src:
        die("This repository already carries BRAND_DARK_GOLD. "
            "The script is not idempotent; re-running it would be a no-op at "
            "best. Nothing changed.")
    if OLD_GOLD not in src.lower():
        die(f"Expected to find {OLD_GOLD} in ui/colors.py and did not. "
            "This repository is not at the state this script was proven "
            "against. Nothing changed.")
    say("preflight: base state confirmed", OK)


# ══════════════════════════════════════════════════════════════════════════
# STEP 1 -- the brand header
# ══════════════════════════════════════════════════════════════════════════

NEW_HEADER = '''# ==================== Brand Colors ====================
# Registered values are sourced from RNVizion/rnv-brand (engine/brand.py).
# Derived values are COMPUTED from their source below, never written down,
# so a derivative cannot drift away from the colour it was derived from.


def _to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Split a 6-digit hex colour into an (r, g, b) tuple."""
    h = hex_color.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def lighten(hex_color: str, step: int) -> str:
    """Shift every channel by the same number of 8-bit steps.

    A uniform per-channel shift preserves the hue exactly, which is what
    keeps a derived gold recognisably the same gold. Negative darkens.
    """
    r, g, b = _to_rgb(hex_color)
    return '#%02x%02x%02x' % tuple(
        max(0, min(255, c + step)) for c in (r, g, b)
    )


BRAND_GOLD: Final[str] = "#d2bc93"
"""Primary brand gold - use for hover states, highlights, tooltips, accents.

Registered brand value.
"""

BRAND_DARK_GOLD: Final[str] = "#8c7337"
"""Brand dark gold - light-mode FILLS, borders and pressed states.

Registered brand value. Carries white text at 4.5429:1. It is a fill
colour: as text it clears 4.5:1 only against pure white, which is why
BRAND_DARK_GOLD_DEEP exists.
"""

BRAND_DARK_GOLD_DEEP: Final[str] = lighten(BRAND_DARK_GOLD, -14)  # -> #7e6529
"""Derived from BRAND_DARK_GOLD - light-mode gold TEXT on grey surfaces.

Every light surface in this app below #ffffff leaves BRAND_DARK_GOLD short
as text (#fafafa 4.35, #f0f0f0 3.99, #eeeeee 3.92). This derivative clears
the whole band (#eeeeee 4.79). It is a TEXT colour only - it carries white
text at just 5.55:1 against black-on-gold's 3.78:1, so it must not become
a fill.
"""

BRAND_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_GOLD)
"""Brand gold as an RGB tuple, derived from the hex above.

Derived rather than written down: a hardcoded tuple is invisible to every
hex-based search, so it survives sweeps that catch every other reference.
"""

BRAND_DARK_GOLD_RGB: Final[tuple[int, int, int]] = _to_rgb(BRAND_DARK_GOLD)
"""Brand dark gold as an RGB tuple, derived from the hex above."""
'''


def step_header() -> None:
    src = COLORS.read_text(encoding="utf-8")
    start = src.index("# ==================== Brand Colors ====================")
    end = src.index("# ==================== Dark Theme Colors ====================")
    src = src[:start] + NEW_HEADER + "\n\n" + src[end:]
    COLORS.write_text(src, encoding="utf-8")
    say("step 1: brand header rewritten (derived RGB, deep gold added)", OK)


# ══════════════════════════════════════════════════════════════════════════
# STEP 2 -- symbol rename, with a use/mention guard
# ══════════════════════════════════════════════════════════════════════════

# A line that documents what a value USED to be is a mention, not a use.
# Sweeping it rewrites history into nonsense ("#8c7337 replaced #8c7337").
MENTION = re.compile(
    r"\b(was|were|previously|formerly|used to|replaced|retired|legacy|"
    r"deprecated|old value|superseded)\b", re.I)


def step_rename() -> tuple[int, list[str]]:
    changed = 0
    skipped: list[str] = []
    for path in tracked(".py", ".md"):
        src = path.read_text(encoding="utf-8")
        if OLD_SYM not in src and OLD_GOLD not in src.lower():
            continue
        out_lines = []
        touched = False
        for i, line in enumerate(src.splitlines(keepends=True), 1):
            if MENTION.search(line) and (OLD_SYM in line or OLD_GOLD in line.lower()):
                skipped.append(f"{path.relative_to(REPO)}:{i}: {line.strip()[:70]}")
                out_lines.append(line)
                continue
            new = line.replace(OLD_SYM, NEW_SYM)
            new = re.sub(re.escape(OLD_GOLD), NEW_GOLD, new, flags=re.I)
            if new != line:
                touched = True
            out_lines.append(new)
        if touched:
            path.write_text("".join(out_lines), encoding="utf-8")
            changed += 1
    say(f"step 2: symbol + value swept across {changed} files", OK)
    for s in skipped:
        say(f"        held (reads as history, not current state): {s}", WARN)
    return changed, skipped


def step_rgb_literal() -> None:
    """The hardcoded RGB tuple in the test suite, the blind-spot twin."""
    t = REPO / "test_rnv_icon_builder.py"
    src = t.read_text(encoding="utf-8")
    if OLD_RGB not in src:
        say("step 3: no hardcoded RGB tuple left to update", WARN)
        return
    src = src.replace(OLD_RGB, "(140, 115, 55)")
    t.write_text(src, encoding="utf-8")
    say("step 3: RGB tuple assertion updated (177,145,69) -> (140,115,55)", OK)


# ══════════════════════════════════════════════════════════════════════════
# STEP 4 -- light palette reassignment
# ══════════════════════════════════════════════════════════════════════════

def step_light_palette() -> None:
    src = COLORS.read_text(encoding="utf-8")
    start = src.index("LIGHT_THEME_COLORS")
    end = src.index("IMAGE_MODE_COLORS")
    block = src[start:end]

    for key in DEEP_TEXT_KEYS:
        pat = re.compile(rf"(^\s*'{key}':\s*)BRAND_DARK_GOLD\s*,", re.M)
        block, n = pat.subn(rf"\g<1>BRAND_DARK_GOLD_DEEP,", block)
        if n != 1:
            die(f"expected exactly one '{key}' assignment in the light "
                f"palette, matched {n}. Nothing further changed.")

    pat = re.compile(rf"(^\s*'tab_hover_bg':\s*)'{OLD_TAB_HOVER}'\s*,", re.M)
    block, n = pat.subn(rf"\g<1>'{NEW_TAB_HOVER}',", block)
    if n != 1:
        die(f"expected exactly one light tab_hover_bg = {OLD_TAB_HOVER}, "
            f"matched {n}. Nothing further changed.")

    COLORS.write_text(src[:start] + block + src[end:], encoding="utf-8")
    say(f"step 4: {', '.join(DEEP_TEXT_KEYS)} -> deep gold; "
        f"tab_hover_bg {OLD_TAB_HOVER} -> {NEW_TAB_HOVER}", OK)


def step_all() -> None:
    src = COLORS.read_text(encoding="utf-8")
    if "'BRAND_DARK_GOLD_DEEP'" in src:
        say("step 5: __all__ already lists the new names", WARN)
        return
    src = src.replace(
        "    'BRAND_DARK_GOLD',\n",
        "    'BRAND_DARK_GOLD',\n    'BRAND_DARK_GOLD_DEEP',\n", 1)
    src = src.replace(
        "    'BRAND_DARK_GOLD_RGB',\n",
        "    'BRAND_DARK_GOLD_RGB',\n    'lighten',\n", 1)
    COLORS.write_text(src, encoding="utf-8")
    say("step 5: __all__ updated", OK)


# ══════════════════════════════════════════════════════════════════════════
# STEP 6 -- snapshots
# ══════════════════════════════════════════════════════════════════════════

INTERNALS_OLD = (
    "- `BRAND_DARK_GOLD` (`#8c7337`) — Pressed states, borders\n")
INTERNALS_NEW = """- `BRAND_DARK_GOLD` (`#8c7337`) — Light-mode gold FILLS: pressed states,
  borders, selections. Carries white text at 4.5429:1.
- `BRAND_DARK_GOLD_DEEP` (derived, `#7e6529`) — Light-mode gold TEXT.
  `BRAND_DARK_GOLD` clears 4.5:1 as text only against pure white, so gold
  text on any grey surface uses this instead. Computed from
  `BRAND_DARK_GOLD`, never written down.
"""


def step_internals() -> None:
    """Document the derivative. The sweep updates the old line's value but
    cannot know a second constant now exists."""
    doc = REPO / "docs" / "INTERNALS.md"
    if not doc.exists():
        say("step 6: docs/INTERNALS.md not present, skipping", WARN)
        return
    src = doc.read_text(encoding="utf-8")
    if "BRAND_DARK_GOLD_DEEP" in src:
        say("step 6: INTERNALS.md already documents the derivative", WARN)
        return
    if INTERNALS_OLD not in src:
        say("step 6: INTERNALS.md colour list is not in the expected shape; "
            "left alone. Document BRAND_DARK_GOLD_DEEP by hand.", WARN)
        return
    doc.write_text(src.replace(INTERNALS_OLD, INTERNALS_NEW, 1),
                   encoding="utf-8")
    say("step 6: INTERNALS.md documents both golds and their roles", OK)


def step_guard_tests() -> None:
    """Install tests/test_brand_contrast.py.

    The payload is base64 so that this script's own copy of the test file
    cannot be caught by any sweep -- including this script's own. A file
    that describes a rule about a value must never be searchable for that
    value; the first draft of this script rewrote its own OLD_GOLD constant
    into the new gold and destroyed its definition of what it was hunting.
    """
    import base64
    dest = REPO / "tests" / "test_brand_contrast.py"
    body = base64.b64decode(GUARD_TEST_B64).decode("utf-8")
    if dest.exists() and dest.read_text(encoding="utf-8") == body:
        say("step 7: guard tests already present and identical", WARN)
        return
    dest.write_text(body, encoding="utf-8")
    say(f"step 7: guard tests written to {dest.relative_to(REPO)} "
        f"({len(body.splitlines())} lines)", OK)


def step_snapshots() -> None:
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    r = subprocess.run([sys.executable, "tests/test_snapshots.py"],
                       cwd=REPO, env=env, capture_output=True, text=True)
    snap = REPO / "tests" / "snapshots.json"
    try:
        data = json.loads(snap.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"snapshots.json is unreadable after regeneration: {exc}")
    # Judge the step by its own product, not by the subprocess exit code:
    # an unrelated failure elsewhere must not be reported as "snapshots broke".
    blob = json.dumps(data).lower()
    if OLD_GOLD in blob:
        # Report the cause, not the symptom. "Snapshots still carry the old
        # gold" is what was observed; it is almost never what went wrong.
        hint = diagnose(r.stderr or r.stdout)
        if hint:
            die(f"the snapshot helper could not run.\n\n       {hint}\n\n"
                f"       Steps 1-7 HAVE been applied. Once the fix above is "
                f"in place, finish with:\n"
                f"         python {Path(__file__).name} --snapshots-only\n\n"
                f"       Or start over:  git checkout -- . && "
                f"git clean -fd tests/")
        die(f"snapshots still carry {OLD_GOLD} after regeneration.\n"
            f"{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    if NEW_GOLD not in blob:
        die("snapshots carry neither the old nor the new gold -- the "
            "regeneration helper probably did not run.\n"
            f"{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    say(f"step 8: snapshots regenerated ({len(data)} keys)", OK)


# ══════════════════════════════════════════════════════════════════════════
# VERIFY
# ══════════════════════════════════════════════════════════════════════════

HEXRE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")


def rules(src: str) -> list[tuple[str, str]]:
    """(selector, body) for every QSS rule in one file.

    A scan, not a regex. `([^{}]+?)\\{\\{(.*?)\\}\\}` backtracks
    quadratically on files this size; `\\{\\{([^{}]*)\\}\\}` is fast but
    wrong, because QSS bodies contain f-string placeholders like
    {c['tab_bg']} and a brace-free body class stops at the first one --
    which finds a fraction of the rules and reads like finding no defects.
    """
    out, cursor = [], 0
    while True:
        start = src.find("{{", cursor)
        if start == -1:
            break
        end = src.find("}}", start + 2)
        if end == -1:
            break
        lead = src[cursor:start].strip()
        out.append((lead.splitlines()[-1].strip() if lead else "",
                    src[start + 2:end]))
        cursor = end + 2
    return out


def _norm(h: str) -> str:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.lower()


def _resolve(token: str, palette: dict, mod) -> str | None:
    token = token.strip().rstrip(";").strip()
    if HEXRE.fullmatch(token):
        return _norm(token)
    m = re.fullmatch(r"\{\s*\w+\[['\"]([\w\-]+)['\"]\]\s*\}", token)
    if m:
        v = palette.get(m.group(1))
        return _norm(v) if isinstance(v, str) and HEXRE.fullmatch(v) else None
    m = re.fullmatch(r"\{\s*([A-Z_][A-Z0-9_]*)\s*\}", token)
    if m:
        v = getattr(mod, m.group(1), None)
        return _norm(v) if isinstance(v, str) and HEXRE.fullmatch(v) else None
    return None


def audit(palette: dict, mod, floor: float = 4.5):
    found = []
    seen_rules = 0
    for path in tracked(".py"):
        src = path.read_text(encoding="utf-8")
        parsed = rules(src)
        seen_rules += len(parsed)
        for sel, body in parsed:
            fg = bg = None
            for decl in body.split(";"):
                if ":" not in decl:
                    continue
                prop, _, val = decl.partition(":")
                prop = prop.strip()
                if prop == "color":
                    fg = _resolve(val, palette, mod)
                elif prop in ("background-color", "background"):
                    bg = _resolve(val, palette, mod)
            if fg and bg and contrast(fg, bg) < floor:
                found.append((fg, bg, round(contrast(fg, bg), 4),
                              f"{path.relative_to(REPO)} {sel[:44]}"))
    # Guard the guard: if the walker stops parsing, every pair below passes
    # vacuously and the run reports clean.
    if seen_rules < 100:
        die(f"the QSS walker found only {seen_rules} rules -- it has stopped "
            f"parsing the stylesheets. Contrast results would be vacuous.")
    return found


def verify() -> bool:
    ok = True
    sys.path.insert(0, str(REPO))
    for m in [k for k in list(sys.modules) if k.startswith("ui")]:
        del sys.modules[m]
    from ui import colors as C  # noqa: E402

    # -- derived constants really are derived, checked in the AST so that a
    #    literal cannot wear the label just by being equal at runtime
    tree = ast.parse(COLORS.read_text(encoding="utf-8"))
    derived = {"BRAND_DARK_GOLD_DEEP", "BRAND_GOLD_RGB", "BRAND_DARK_GOLD_RGB"}
    for node in tree.body:
        tgt = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            tgt, val = node.target.id, node.value
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            tgt, val = node.targets[0].id, node.value
        if tgt in derived:
            if not isinstance(val, ast.Call):
                say(f"verify: {tgt} is labelled derived but is a literal", FAIL)
                ok = False
            derived.discard(tgt)
    if derived:
        say(f"verify: expected derived constants absent: {sorted(derived)}", FAIL)
        ok = False

    if C.BRAND_DARK_GOLD_DEEP != DEEP_GOLD:
        say(f"verify: deep gold computed to {C.BRAND_DARK_GOLD_DEEP}, "
            f"expected {DEEP_GOLD}", FAIL)
        ok = False
    if C.BRAND_DARK_GOLD_RGB != (140, 115, 55):
        say(f"verify: RGB tuple is {C.BRAND_DARK_GOLD_RGB}", FAIL)
        ok = False

    # -- no reference to the retired values survives anywhere, in any case,
    #    including inside RGB tuples
    stale = []
    guards_seen = 0
    for path in tracked(".py", ".md", ".json"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if GUARD_MARKER in text:
            guards_seen += 1
            continue          # its job is to name the retired values
        for i, line in enumerate(text.splitlines(), 1):
            if MENTION.search(line):
                continue
            if (OLD_GOLD in line.lower() or OLD_SYM in line
                    or OLD_RGB.replace(" ", "") in line.replace(" ", "")
                    or OLD_TAB_HOVER in line.lower()):
                stale.append(f"{path.relative_to(REPO)}:{i}: {line.strip()[:70]}")
    if stale:
        ok = False
        say("verify: retired values still present:", FAIL)
        for s in stale:
            say(f"        {s}", FAIL)
    # Guard the exclusion. If the marker ever matched everything -- or the
    # guard file went missing -- this scan would report a clean repository
    # by looking at nothing, which is the failure mode it exists to prevent.
    if guards_seen != 1:
        ok = False
        say(f"verify: expected exactly one guard file carrying the "
            f"do-not-sweep marker, found {guards_seen}. Either the guard "
            f"test is missing or the marker is on files it should not be.",
            FAIL)

    # -- pairing audit: the surviving failures must be EXACTLY the accepted set
    seen = set()
    for name, pal in (("LIGHT", C.LIGHT_THEME_COLORS),
                      ("DARK", C.DARK_THEME_COLORS)):
        for fg, bg, r, where in audit(pal, C):
            if (fg, bg) in ACCEPTED:
                seen.add((fg, bg))
                continue
            ok = False
            say(f"verify: unaccepted {name} pair {fg} on {bg} = {r} <- {where}",
                FAIL)
    # the companion check: an ACCEPTED entry that no longer occurs is a stale
    # exemption, and stale exemptions always go stale in the direction that
    # reports clean
    for key in ACCEPTED:
        if key not in seen:
            ok = False
            say(f"verify: ACCEPTED lists {key[0]} on {key[1]} but nothing "
                f"produces that pair any more -- remove the exemption", FAIL)

    say("verify: PASS" if ok else "verify: FAIL", OK if ok else FAIL)
    return ok


# pytest's documented exit codes. Collapsing all of these into "not zero"
# is how a killed process gets reported as a test failure.
PYTEST_EXIT = {
    0: ("all tests passed", OK),
    1: ("tests FAILED -- see the failures above", FAIL),
    2: ("the run was interrupted before it finished", WARN),
    3: ("pytest hit an internal error", WARN),
    4: ("pytest usage error -- bad arguments", WARN),
    5: ("NO TESTS RAN. That is not a pass.", FAIL),
}


def run_suite(quick: bool = False) -> bool:
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    cmd = [sys.executable, "-m", "pytest", "-q"]
    if quick:
        cmd += ["-m", "not benchmark"]
        say("running the test suite (benchmarks deselected) ...")
    else:
        say("running the full test suite ...")
    r = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().splitlines()

    # Surface the parts that carry information, not just the tail.
    interesting = [ln for ln in out
                   if ln.startswith(("FAILED", "ERROR"))
                   or " failed" in ln or " passed" in ln]
    for line in (interesting or out)[-15:]:
        say(f"    {line}")

    code = r.returncode
    if code < 0:
        # Negative means killed by a signal. On a small container that is
        # almost always the OOM killer taking the benchmark phase, which
        # allocates pixmaps in a tight loop. It says nothing about whether
        # the code under test is correct.
        say(f"\n    the test process was KILLED by signal {-code} -- it did "
            f"not run to completion.", WARN)
        say(f"    This is an environment limit, not a test result. Nothing "
            f"failed; the run was cut short.", WARN)
        if not quick:
            say(f"    The benchmark phase is the memory-hungry part. Retry "
                f"without it:", WARN)
            say(f"      python {Path(__file__).name} --verify-only "
                f"--quick-tests", WARN)
        return False

    msg, colour = PYTEST_EXIT.get(code, (f"pytest exited {code}", WARN))
    say(f"\n    {msg}", colour)
    return code == 0


def remove_helpers(extra: list[str]) -> None:
    """Delete this tool and any named helper files from the working tree.

    Runs LAST and only when verification passed. Removing the tools that
    diagnose a repository, before knowing the repository is sound, leaves
    no way to find out what went wrong.

    Deletion is by content marker plus explicit names, never a hardcoded
    filename list: this tool is committed under whatever working name suits
    the transfer, and a list of names would miss a renamed copy while
    reporting a tidy repository.

    Files are unlinked rather than `git rm`-ed so that nothing is staged
    behind your back -- the deletions show up in `git status` alongside the
    guard-file edit, and one `git add -A` takes the lot.
    """
    doomed: list[Path] = []
    for p in tracked(".py", ".sh", ".md"):
        try:
            if TOOL_MARKER in p.read_text(encoding="utf-8", errors="ignore"):
                doomed.append(p)
        except OSError:
            pass
    if SELF.exists() and SELF not in doomed:
        doomed.append(SELF)          # tracked() excludes SELF by design
    for name in extra:
        p = (REPO / name).resolve()
        if not p.exists():
            say(f"    {name}: not here, nothing to remove", WARN)
        elif p not in doomed:
            doomed.append(p)

    for p in sorted(set(doomed)):
        try:
            p.unlink()
            say(f"    removed {p.relative_to(REPO)}", OK)
        except OSError as exc:
            say(f"    could NOT remove {p.relative_to(REPO)}: {exc}", FAIL)

    say("\n    Working tree is ready. One commit takes everything:", OK)
    say("      git add -A")
    say("      git commit -m 'Mark the brand guard file as exempt from "
        "value sweeps; drop transfer helpers'")
    say("      git push")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Brand-gold alignment for rnv-icon-builder.",
        epilog="If a run aborted at step 8 because pytest was missing, "
               "install requirements-test.txt and re-run with "
               "--snapshots-only to finish it.")
    ap.add_argument("--verify-only", action="store_true",
                    help="check an already-aligned repository, change nothing")
    ap.add_argument("--snapshots-only", action="store_true",
                    help="resume a half-applied run: regenerate snapshots "
                         "and verify, skipping steps 1-7")
    ap.add_argument("--install-deps", action="store_true",
                    help="apt-get the Qt system libraries first, then "
                         "continue with whatever else was asked for")
    ap.add_argument("--skip-tests", action="store_true",
                    help="skip the pytest run at the end")
    ap.add_argument("--refresh-guards", action="store_true",
                    help="rewrite tests/test_brand_contrast.py from this "
                         "script's copy, then verify. Safe on an "
                         "already-aligned repository.")
    ap.add_argument("--quick-tests", action="store_true",
                    help="run the suite without benchmarks -- much lighter "
                         "on memory, for small containers and codespaces")
    ap.add_argument("--finish", nargs="*", metavar="FILE",
                    help="the last pass on an already-aligned repository: "
                         "refresh the guard file, verify, run the suite, "
                         "then delete this tool and any extra FILEs. "
                         "Deletion happens only if everything passed. "
                         "Example: --finish in.py")
    args = ap.parse_args()

    if args.install_deps:
        install_system_deps()

    if args.refresh_guards or args.finish is not None:
        step_guard_tests()

    if args.snapshots_only:
        check_dependencies()
        src = COLORS.read_text(encoding="utf-8")
        if OLD_SYM in src or NEW_SYM not in src:
            die("--snapshots-only is for finishing a run that already "
                "applied steps 1-7, and this repository has not had them "
                "applied. Run the script without flags instead.")
        say("resuming at step 8 -- steps 1-7 are already in place", OK)
        step_snapshots()

    if not (args.verify_only or args.snapshots_only or args.refresh_guards
            or args.finish is not None):
        preflight()
        step_header()
        step_rename()
        step_rgb_literal()
        step_light_palette()
        step_all()
        step_internals()
        step_guard_tests()
        step_snapshots()

    ok = verify()
    if not args.skip_tests:
        ok = run_suite(quick=args.quick_tests) and ok

    if args.finish is not None:
        if ok:
            say("\nremoving transfer helpers ...")
            remove_helpers(args.finish)
        else:
            say("\nNOT removing anything -- verification did not pass. "
                "The tools stay so you can find out why.", FAIL)

    say("\nDONE -- all checks passed" if ok else "\nDONE -- with failures above",
        OK if ok else FAIL)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
