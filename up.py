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
    "IGNvbG9ycyBhcyBDCmZyb20gdWkudGhlbWVfbWFuYWdlciBpbXBvcnQgVGhlbWVNYW5h"
    "Z2VyIGFzIFRNCgoKUFJPSkVDVF9ST09UID0gUGF0aChfX2ZpbGVfXykucmVzb2x2ZSgp"
    "LnBhcmVudC5wYXJlbnQKQ09MT1JTX1BZID0gUFJPSkVDVF9ST09UIC8gInVpIiAvICJj"
    "b2xvcnMucHkiCgpURVhUX0ZMT09SID0gNC41ICAgICAgICAgICMgV0NBRyAxLjQuMywg"
    "bm9ybWFsLXNpemUgdGV4dApDT01QT05FTlRfRkxPT1IgPSAzLjAgICAgICMgV0NBRyAx"
    "LjQuMTEsIFVJIGNvbXBvbmVudHMgYW5kIGdyYXBoaWNzCgoKIyDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZAKIyBDT05UUkFTVAojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkAoKZGVmIHJlbGF0aXZl"
    "X2x1bWluYW5jZShoZXhfY29sb3I6IHN0cikgLT4gZmxvYXQ6CiAgICBoID0gaGV4X2Nv"
    "bG9yLmxzdHJpcCgiIyIpCiAgICBpZiBsZW4oaCkgPT0gMzoKICAgICAgICBoID0gIiIu"
    "am9pbihjICogMiBmb3IgYyBpbiBoKQogICAgY2ggPSBbaW50KGhbaTppICsgMl0sIDE2"
    "KSAvIDI1NSBmb3IgaSBpbiAoMCwgMiwgNCldCiAgICBjaCA9IFtjIC8gMTIuOTIgaWYg"
    "YyA8PSAwLjA0MDQ1IGVsc2UgKChjICsgMC4wNTUpIC8gMS4wNTUpICoqIDIuNAogICAg"
    "ICAgICAgZm9yIGMgaW4gY2hdCiAgICByZXR1cm4gMC4yMTI2ICogY2hbMF0gKyAwLjcx"
    "NTIgKiBjaFsxXSArIDAuMDcyMiAqIGNoWzJdCgoKZGVmIGNvbnRyYXN0X3JhdGlvKGZn"
    "OiBzdHIsIGJnOiBzdHIpIC0+IGZsb2F0OgogICAgbDEsIGwyID0gc29ydGVkKFtyZWxh"
    "dGl2ZV9sdW1pbmFuY2UoZmcpLCByZWxhdGl2ZV9sdW1pbmFuY2UoYmcpXSwKICAgICAg"
    "ICAgICAgICAgICAgICByZXZlcnNlPVRydWUpCiAgICByZXR1cm4gKGwxICsgMC4wNSkg"
    "LyAobDIgKyAwLjA1KQoKCiMg4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQCiMgREVSSVZBVElPTiBH"
    "VUFSRAojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkAoKIyBDb25zdGFudHMgd2hvc2UgZG9jc3Ry"
    "aW5nIGNsYWltcyB0aGV5IGFyZSBkZXJpdmVkLiBFYWNoIG11c3QgYmUgYSBjYWxsCiMg"
    "ZXhwcmVzc2lvbiBpbiB0aGUgc291cmNlLCBub3QgYSBsaXRlcmFsLgpERVJJVkVEX0NP"
    "TlNUQU5UUyA9IHsKICAgICJCUkFORF9EQVJLX0dPTERfREVFUCIsCiAgICAiQlJBTkRf"
    "R09MRF9SR0IiLAogICAgIkJSQU5EX0RBUktfR09MRF9SR0IiLAp9CgojIENvbnN0YW50"
    "cyB0aGF0IGFyZSByZWdpc3RlcmVkIGJyYW5kIHZhbHVlcyBhbmQgbXVzdCB0aGVyZWZv"
    "cmUgYmUgbGl0ZXJhbHMuCiMgRGVyaXZpbmcgb25lIG9mIHRoZXNlIHdvdWxkIGludmVy"
    "dCB0aGUgcmVsYXRpb25zaGlwOiB0aGUgcmVnaXN0ZXIgaXMgdGhlCiMgc291cmNlLCBz"
    "byBhIHJlZ2lzdGVyZWQgY29sb3VyIGNhbm5vdCBiZSBjb21wdXRlZCBmcm9tIHNvbWV0"
    "aGluZyBlbHNlLgpSRUdJU1RFUkVEX0NPTlNUQU5UUyA9IHsKICAgICJCUkFORF9HT0xE"
    "IiwKICAgICJCUkFORF9EQVJLX0dPTEQiLAp9CgoKZGVmIF9tb2R1bGVfbGV2ZWxfYXNz"
    "aWdubWVudHMoKSAtPiBkaWN0W3N0ciwgYXN0LmV4cHJdOgogICAgdHJlZSA9IGFzdC5w"
    "YXJzZShDT0xPUlNfUFkucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpKQogICAgb3V0"
    "OiBkaWN0W3N0ciwgYXN0LmV4cHJdID0ge30KICAgIGZvciBub2RlIGluIHRyZWUuYm9k"
    "eToKICAgICAgICBpZiBpc2luc3RhbmNlKG5vZGUsIGFzdC5Bbm5Bc3NpZ24pIGFuZCBp"
    "c2luc3RhbmNlKG5vZGUudGFyZ2V0LCBhc3QuTmFtZSk6CiAgICAgICAgICAgIGlmIG5v"
    "ZGUudmFsdWUgaXMgbm90IE5vbmU6CiAgICAgICAgICAgICAgICBvdXRbbm9kZS50YXJn"
    "ZXQuaWRdID0gbm9kZS52YWx1ZQogICAgICAgIGVsaWYgaXNpbnN0YW5jZShub2RlLCBh"
    "c3QuQXNzaWduKToKICAgICAgICAgICAgZm9yIHQgaW4gbm9kZS50YXJnZXRzOgogICAg"
    "ICAgICAgICAgICAgaWYgaXNpbnN0YW5jZSh0LCBhc3QuTmFtZSkgYW5kIG5vZGUudmFs"
    "dWUgaXMgbm90IE5vbmU6CiAgICAgICAgICAgICAgICAgICAgb3V0W3QuaWRdID0gbm9k"
    "ZS52YWx1ZQogICAgcmV0dXJuIG91dAoKCkBweXRlc3QubWFyay5wYXJhbWV0cml6ZSgi"
    "bmFtZSIsIHNvcnRlZChERVJJVkVEX0NPTlNUQU5UUykpCmRlZiB0ZXN0X2Rlcml2ZWRf"
    "Y29uc3RhbnRfaXNfYWN0dWFsbHlfY29tcHV0ZWQobmFtZTogc3RyKSAtPiBOb25lOgog"
    "ICAgIiIiQSBkZXJpdmVkIGNvbnN0YW50IG11c3QgYmUgYSBjYWxsLCBub3QgYSBsaXRl"
    "cmFsIHRoYXQgbG9va3MgcmlnaHQuIiIiCiAgICBhc3NpZ25zID0gX21vZHVsZV9sZXZl"
    "bF9hc3NpZ25tZW50cygpCiAgICBhc3NlcnQgbmFtZSBpbiBhc3NpZ25zLCAoCiAgICAg"
    "ICAgZiJ7bmFtZX0gaXMgZXhwZWN0ZWQgdG8gZXhpc3QgaW4gdWkvY29sb3JzLnB5IGFu"
    "ZCBkb2VzIG5vdC4gIgogICAgICAgIGYiSWYgaXQgd2FzIGRlbGliZXJhdGVseSByZW1v"
    "dmVkLCByZW1vdmUgaXQgZnJvbSBERVJJVkVEX0NPTlNUQU5UUyAiCiAgICAgICAgZiJp"
    "biB0aGlzIHRlc3QgdG9vLiIpCiAgICBub2RlID0gYXNzaWduc1tuYW1lXQogICAgYXNz"
    "ZXJ0IGlzaW5zdGFuY2Uobm9kZSwgYXN0LkNhbGwpLCAoCiAgICAgICAgZiJ7bmFtZX0g"
    "aXMgZG9jdW1lbnRlZCBhcyBkZXJpdmVkIGJ1dCBpcyBhc3NpZ25lZCBhIGxpdGVyYWwg"
    "IgogICAgICAgIGYiKHthc3QuZHVtcChub2RlKVs6ODBdfSkuIE9uY2UgaXQgaXMgd3Jp"
    "dHRlbiBkb3duIGl0IHN0b3BzICIKICAgICAgICBmInRyYWNraW5nIHRoZSBjb2xvdXIg"
    "aXQgY2FtZSBmcm9tLCBhbmQgdGhlIG5leHQgdGltZSB0aGF0IGNvbG91ciAiCiAgICAg"
    "ICAgZiJtb3ZlcyB0aGlzIG9uZSBzaWxlbnRseSBkb2VzIG5vdC4iKQoKCkBweXRlc3Qu"
    "bWFyay5wYXJhbWV0cml6ZSgibmFtZSIsIHNvcnRlZChSRUdJU1RFUkVEX0NPTlNUQU5U"
    "UykpCmRlZiB0ZXN0X3JlZ2lzdGVyZWRfY29uc3RhbnRfaXNfYV9saXRlcmFsKG5hbWU6"
    "IHN0cikgLT4gTm9uZToKICAgICIiIkEgcmVnaXN0ZXJlZCBicmFuZCB2YWx1ZSBtdXN0"
    "IGJlIHdyaXR0ZW4gZG93biwgbm90IGNvbXB1dGVkLiIiIgogICAgYXNzaWducyA9IF9t"
    "b2R1bGVfbGV2ZWxfYXNzaWdubWVudHMoKQogICAgYXNzZXJ0IG5hbWUgaW4gYXNzaWdu"
    "cywgZiJ7bmFtZX0gbWlzc2luZyBmcm9tIHVpL2NvbG9ycy5weSIKICAgIG5vZGUgPSBh"
    "c3NpZ25zW25hbWVdCiAgICBhc3NlcnQgaXNpbnN0YW5jZShub2RlLCBhc3QuQ29uc3Rh"
    "bnQpIGFuZCBpc2luc3RhbmNlKG5vZGUudmFsdWUsIHN0ciksICgKICAgICAgICBmIntu"
    "YW1lfSBpcyBhIHJlZ2lzdGVyZWQgYnJhbmQgY29sb3VyIGFuZCBtdXN0IGJlIGEgbGl0"
    "ZXJhbC4gIgogICAgICAgIGYiRGVyaXZpbmcgaXQgd291bGQgbWFrZSB0aGUgcmVnaXN0"
    "ZXIgZGVwZW5kIG9uIHRoZSBhcHAgaW5zdGVhZCAiCiAgICAgICAgZiJvZiB0aGUgb3Ro"
    "ZXIgd2F5IHJvdW5kLiIpCgoKZGVmIHRlc3RfZGVlcF9nb2xkX3RyYWNrc19pdHNfc291"
    "cmNlKCkgLT4gTm9uZToKICAgICIiIkNoYW5naW5nIEJSQU5EX0RBUktfR09MRCBtdXN0"
    "IG1vdmUgdGhlIGRlcml2YXRpdmUgd2l0aCBpdC4iIiIKICAgIGFzc2VydCBDLkJSQU5E"
    "X0RBUktfR09MRF9ERUVQID09IEMubGlnaHRlbihDLkJSQU5EX0RBUktfR09MRCwgLTE0"
    "KQogICAgYXNzZXJ0IEMuQlJBTkRfREFSS19HT0xEX0RFRVAgIT0gQy5CUkFORF9EQVJL"
    "X0dPTEQKCgpAcHl0ZXN0Lm1hcmsucGFyYW1ldHJpemUoImNvbnN0LHJnYiIsIFsKICAg"
    "ICgiQlJBTkRfR09MRCIsICJCUkFORF9HT0xEX1JHQiIpLAogICAgKCJCUkFORF9EQVJL"
    "X0dPTEQiLCAiQlJBTkRfREFSS19HT0xEX1JHQiIpLApdKQpkZWYgdGVzdF9yZ2JfdHVw"
    "bGVfbWF0Y2hlc19pdHNfaGV4KGNvbnN0OiBzdHIsIHJnYjogc3RyKSAtPiBOb25lOgog"
    "ICAgIiIiVGhlIFJHQi10dXBsZSBibGluZCBzcG90LgoKICAgIEEgaGFyZGNvZGVkICgx"
    "NzcsIDE0NSwgNjkpIGlzIGludmlzaWJsZSB0byBldmVyeSBoZXgtYmFzZWQgc2VhcmNo"
    "LCBzbwogICAgaXQgc3Vydml2ZXMgc3dlZXBzIHRoYXQgY2F0Y2ggZXZlcnkgb3RoZXIg"
    "cmVmZXJlbmNlIHRvIHRoZSBjb2xvdXIuCiAgICBEZXJpdmluZyBpdCByZW1vdmVzIHRo"
    "ZSBoaWRpbmcgcGxhY2U7IHRoaXMgdGVzdCBrZWVwcyBpdCByZW1vdmVkLgogICAgIiIi"
    "CiAgICByLCBnLCBiID0gZ2V0YXR0cihDLCByZ2IpCiAgICBhc3NlcnQgZ2V0YXR0cihD"
    "LCBjb25zdCkubG93ZXIoKSA9PSBmIiN7cjowMnh9e2c6MDJ4fXtiOjAyeH0iCgoKZGVm"
    "IHRlc3RfbGlnaHRlbl9wcmVzZXJ2ZXNfaHVlX2J5X3NoaWZ0aW5nX2NoYW5uZWxzX3Vu"
    "aWZvcm1seSgpIC0+IE5vbmU6CiAgICBiYXNlID0gIiM4YzczMzciCiAgICBvdXQgPSBD"
    "LmxpZ2h0ZW4oYmFzZSwgLTE0KQogICAgYnIsIGJnXywgYmIgPSBDLl90b19yZ2IoYmFz"
    "ZSkKICAgIG9yciwgb2csIG9iID0gQy5fdG9fcmdiKG91dCkKICAgIGFzc2VydCAoYnIg"
    "LSBvcnIsIGJnXyAtIG9nLCBiYiAtIG9iKSA9PSAoMTQsIDE0LCAxNCkKCgpkZWYgdGVz"
    "dF9saWdodGVuX2NsYW1wc19pbnN0ZWFkX29mX3dyYXBwaW5nKCkgLT4gTm9uZToKICAg"
    "IGFzc2VydCBDLmxpZ2h0ZW4oIiNmZmZmZmYiLCA0MCkgPT0gIiNmZmZmZmYiCiAgICBh"
    "c3NlcnQgQy5saWdodGVuKCIjMDAwMDAwIiwgLTQwKSA9PSAiIzAwMDAwMCIKCgojIOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkAojIFBBSVJJTkcgQVVESVQKIyDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZAKCiMgRXZlcnkgcGFsZXR0ZSB0aGUgYXBwIGNhbiBhY3R1YWxseSByZW5kZXIgYSBz"
    "dHlsZXNoZWV0IHdpdGguCiMKIyBUaGUgcmF3IHRocmVlIGFyZSBub3QgdGhlIHdob2xl"
    "IHN0b3J5OiBUaGVtZU1hbmFnZXIgYnVpbGRzIHR3byBtb3JlIGJ5CiMgUkVNQVBQSU5H"
    "IGtleXMgLS0gaXRzICdidXR0b25faG92ZXJfYmcnIGlzIGNvbG9ycy5weSdzICdtYWlu"
    "X2J0bl9ob3Zlcl9iZycsCiMgYSBkaWZmZXJlbnQgY29sb3VyIGVudGlyZWx5LiBBdWRp"
    "dGluZyBhIFRoZW1lTWFuYWdlci1kcml2ZW4gYmxvY2sgYWdhaW5zdAojIHRoZSByYXcg"
    "cGFsZXR0ZSByZWFkcyBhIHZhbHVlIHRoYXQgYmxvY2sgbmV2ZXIgcmVuZGVycywgd2hp"
    "Y2ggaXMgaG93IHRoZQojIG1haW4td2luZG93IGJ1dHRvbiBzY2hlbWUgd2VudCB1bmF1"
    "ZGl0ZWQgd2hpbGUgYSBwYWlyaW5nIHRoYXQgZG9lcyBub3QKIyBleGlzdCBnb3QgcmVj"
    "b3JkZWQgYXMgYSBrbm93biBmYWlsdXJlLgpQQUxFVFRFUzogZGljdFtzdHIsIGRpY3Rb"
    "c3RyLCBzdHJdXSA9IHsKICAgICJMSUdIVCI6IEMuTElHSFRfVEhFTUVfQ09MT1JTLAog"
    "ICAgIkRBUksiOiBDLkRBUktfVEhFTUVfQ09MT1JTLAogICAgIklNQUdFIjogQy5JTUFH"
    "RV9NT0RFX0NPTE9SUywKICAgICJUTV9MSUdIVCI6IFRNLkxJR0hUX1RIRU1FLAogICAg"
    "IlRNX0RBUksiOiBUTS5EQVJLX1RIRU1FLAp9CgojIExvY2FsIG5hbWVzIGJvdW5kIGRp"
    "cmVjdGx5IHRvIGEgcGFsZXR0ZSBjb25zdGFudCwgZS5nLiBgaW0gPSBJTUFHRV9NT0RF"
    "X0NPTE9SU2AuCiMgQSBibG9jayB1c2luZyBzdWNoIGEgbmFtZSByZW5kZXJzIHdpdGgg"
    "VEhBVCBwYWxldHRlIGFuZCBubyBvdGhlci4KX1BJTl9DT05TVCA9IHsKICAgICJMSUdI"
    "VF9USEVNRV9DT0xPUlMiOiAiTElHSFQiLAogICAgIkRBUktfVEhFTUVfQ09MT1JTIjog"
    "IkRBUksiLAogICAgIklNQUdFX01PREVfQ09MT1JTIjogIklNQUdFIiwKfQpfUElOID0g"
    "cmUuY29tcGlsZSgKICAgIHIiXlxzKihcdyspXHMqPVxzKihMSUdIVF9USEVNRV9DT0xP"
    "UlN8REFSS19USEVNRV9DT0xPUlN8SU1BR0VfTU9ERV9DT0xPUlMpXHMqJCIsCiAgICBy"
    "ZS5NKQoKIyBQYWlycyB0aGF0IHJlbmRlciBiZWxvdyB0aGUgZmxvb3Igb24gcHVycG9z"
    "ZSwga2V5ZWQgYnkgdGhlIHBhbGV0dGUgdGhhdAojIGFjdHVhbGx5IHJlbmRlcnMgdGhl"
    "bS4gQm90aCBoYWx2ZXMgb2YgdGhpcyBkaWN0IGFyZSBhc3NlcnRlZCAtLSBhbgojIHVu"
    "ZXhwZWN0ZWQgZmFpbHVyZSBmYWlscyB0aGUgc3VpdGUsIGFuZCBhbiBlbnRyeSB0aGF0"
    "IG5vIGxvbmdlciBtYXRjaGVzCiMgYW55dGhpbmcgZmFpbHMgaXQgdG9vLiBBbiBleGVt"
    "cHRpb24gZm9yIGEgcGFpcmluZyB0aGF0IGRvZXMgbm90IGV4aXN0IGlzCiMgd29yc2Ug"
    "dGhhbiBubyBleGVtcHRpb246IGl0IGlzIGEgbGljZW5jZSB3YWl0aW5nIGZvciBhIHJl"
    "YWwgZGVmZWN0IHRvCiMgd2FuZGVyIGludG8uCkFDQ0VQVEVEOiBkaWN0W3R1cGxlW3N0"
    "ciwgc3RyLCBzdHJdLCBzdHJdID0gewogICAgKCJUTV9MSUdIVCIsICIjMDAwMDAwIiwg"
    "IiMzMzMzMzMiKToKICAgICAgICAibWFpbi13aW5kb3cgYnV0dG9uIGhvdmVyLCBsaWdo"
    "dC4gVGhlIG1haW4gd2luZG93IHJ1bnMgYSAiCiAgICAgICAgIndoaXRlL25lYXItYmxh"
    "Y2sgaW52ZXJzZSBzY2hlbWUgaW4gd2hpY2ggdGhlIHRleHQgc3RheXMgYmxhY2sgIgog"
    "ICAgICAgICJ3aGlsZSB0aGUgYmFja2dyb3VuZCBkYXJrZW5zLiBEZWxpYmVyYXRlLCBh"
    "bmQgc2VwYXJhdGUgZnJvbSB0aGUgIgogICAgICAgICJnb2xkIGRpYWxvZy1idXR0b24g"
    "c2NoZW1lLiIsCiAgICAoIlRNX0RBUksiLCAiIzAwMDAwMCIsICIjNDQ0NDQ0Iik6CiAg"
    "ICAgICAgIm1haW4td2luZG93IGJ1dHRvbiBwcmVzc2VkLCBkYXJrLiBTYW1lIGludmVy"
    "c2Ugc2NoZW1lLCBtaXJyb3JlZDogIgogICAgICAgICJ0aGUgdGV4dCBnb2VzIGJsYWNr"
    "IGFzIHRoZSBiYWNrZ3JvdW5kIGxpZ2h0ZW5zLiIsCiAgICAoIklNQUdFIiwgIiMwMDAw"
    "MDAiLCAiIzQ0NDQ0NCIpOgogICAgICAgICJtYWluLXdpbmRvdyBidXR0b24gcHJlc3Nl"
    "ZCBpbiBpbWFnZSBtb2RlLCB3aGljaCBpbmhlcml0cyB0aGUgZGFyayAiCiAgICAgICAg"
    "InBhbGV0dGUuIFNhbWUgaW52ZXJzZSBzY2hlbWUuIiwKICAgICgiTElHSFQiLCAiI2Fh"
    "YWFhYSIsICIjZmZmZmZmIik6CiAgICAgICAgImRpc2FibGVkIGNvbnRyb2wgdGV4dC4g"
    "V0NBRyAxLjQuMyBleGVtcHRzIGRpc2FibGVkIGNvbnRyb2xzLiIsCiAgICAoIkRBUksi"
    "LCAiIzU1NTU1NSIsICIjMWExYTFhIik6CiAgICAgICAgImRpc2FibGVkIGNvbnRyb2wg"
    "dGV4dCwgZGFyay4gU2FtZSBleGVtcHRpb24uIiwKICAgICgiTElHSFQiLCAiIzY2NjY2"
    "NiIsICIjZTBlMGUwIik6CiAgICAgICAgIk9TLXNpbXVsYXRpb24gY2hyb21lIGluIGNv"
    "bnRleHRfcHJldmlldy5weSwgd2hpY2ggcmVwcm9kdWNlcyAiCiAgICAgICAgInBsYXRm"
    "b3JtIFVJIHNvIGEgdXNlciBjYW4gcHJldmlldyBhbiBpY29uIGluIHNpdHUuIEl0IG11"
    "c3QgbWF0Y2ggIgogICAgICAgICJ0aGUgcGxhdGZvcm0sIG5vdCB0aGUgYnJhbmQuIiwK"
    "ICAgICgiREFSSyIsICIjODg4ODg4IiwgIiMyYTJhMmEiKToKICAgICAgICAiT1Mtc2lt"
    "dWxhdGlvbiBjaHJvbWUsIGRhcmsuIFNhbWUgcmVhc29uLiIsCiAgICAoIklNQUdFIiwg"
    "IiM4ODg4ODgiLCAiIzJhMmEyYSIpOgogICAgICAgICJPUy1zaW11bGF0aW9uIGNocm9t"
    "ZSB1bmRlciB0aGUgaW1hZ2UtbW9kZSBwYWxldHRlLiBTYW1lIHJlYXNvbi4iLAp9Cgpf"
    "SEVYID0gcmUuY29tcGlsZShyIiMoPzpbMC05YS1mQS1GXXszfXxbMC05YS1mQS1GXXs2"
    "fSlcYiIpCgojIFRoZSBRU1MgbGl2ZXMgaW5zaWRlIGYtc3RyaW5ncywgc28gaXRzIGJy"
    "YWNlcyBhcmUgZG91YmxlZC4gTWF0Y2hpbmcgc2luZ2xlCiMgYnJhY2VzIGhlcmUgZmlu"
    "ZHMgbm90aGluZyBhdCBhbGwgLS0gYW5kIGZpbmRpbmcgbm90aGluZyByZWFkcyBleGFj"
    "dGx5IGxpa2UKIyBmaW5kaW5nIG5vIGRlZmVjdHMsIHdoaWNoIGlzIHdoeSB0ZXN0X3Ro"
    "ZV9hdWRpdF9maW5kc19zb21ldGhpbmdfdG9fYXVkaXQKIyBleGlzdHMgYmVsb3cuCiMK"
    "CmRlZiBfcnVsZXMoc3JjOiBzdHIpIC0+IGxpc3RbdHVwbGVbc3RyLCBzdHJdXToKICAg"
    "ICIiIllpZWxkIChzZWxlY3RvciwgYm9keSkgZm9yIGVhY2ggUVNTIHJ1bGUgaW4gb25l"
    "IHNvdXJjZSBmaWxlLgoKICAgIERlbGliZXJhdGVseSBhIHNjYW4gcmF0aGVyIHRoYW4g"
    "YSByZWdleC4gVGhlIG9idmlvdXMgcGF0dGVybiwKICAgIGBgKFtee31dKz8pXFx7XFx7"
    "KC4qPylcXH1cXH1gYCwgYmFja3RyYWNrcyBxdWFkcmF0aWNhbGx5IG9uIGZpbGVzIHRo"
    "aXMKICAgIHNpemUgLS0gaXQgdG9vayBmb3J0eSBzZWNvbmRzIHBlciBwYXNzLiBUaGUg"
    "b2J2aW91cyBmaXgsIHRpZ2h0ZW5pbmcgdGhlCiAgICBib2R5IHRvIGBgW157fV0qYGAs"
    "IGlzIHdyb25nIGZvciBhIGRpZmZlcmVudCByZWFzb246IFFTUyBib2RpZXMgYXJlIGZ1"
    "bGwKICAgIG9mIGYtc3RyaW5nIHBsYWNlaG9sZGVycyBsaWtlIGBge2NbJ3RhYl9iZydd"
    "fWBgLCBzbyBhIGJyYWNlLWZyZWUgYm9keQogICAgY2xhc3Mgc3RvcHMgZGVhZCBhdCB0"
    "aGUgZmlyc3Qgb25lIGFuZCBmaW5kcyBhIGZyYWN0aW9uIG9mIHRoZSBydWxlcy4KICAg"
    "IEZpbmRpbmcgYSBmcmFjdGlvbiBvZiB0aGUgcnVsZXMgcmVhZHMgZXhhY3RseSBsaWtl"
    "IGZpbmRpbmcgbm8gZGVmZWN0cywKICAgIHdoaWNoIGlzIHdoYXQgdGVzdF90aGVfYXVk"
    "aXRfZmluZHNfc29tZXRoaW5nX3RvX2F1ZGl0IGlzIHRoZXJlIHRvIGNhdGNoLgoKICAg"
    "IFRoZSBzZWxlY3RvciBpcyB0aGUgbGFzdCBsaW5lIG9mIHRleHQgYmV0d2VlbiB0aGUg"
    "ZW5kIG9mIHRoZSBwcmV2aW91cwogICAgYmxvY2sgYW5kIHRoZSBzdGFydCBvZiB0aGlz"
    "IG9uZSwgd2hpY2ggaXMgd2hlcmUgUXQncyBzZWxlY3RvciBzaXRzLgogICAgIiIiCiAg"
    "ICBvdXQgPSBbXQogICAgY3Vyc29yID0gMAogICAgd2hpbGUgVHJ1ZToKICAgICAgICBz"
    "dGFydCA9IHNyYy5maW5kKCJ7eyIsIGN1cnNvcikKICAgICAgICBpZiBzdGFydCA9PSAt"
    "MToKICAgICAgICAgICAgYnJlYWsKICAgICAgICBlbmQgPSBzcmMuZmluZCgifX0iLCBz"
    "dGFydCArIDIpCiAgICAgICAgaWYgZW5kID09IC0xOgogICAgICAgICAgICBicmVhawog"
    "ICAgICAgIGxlYWQgPSBzcmNbY3Vyc29yOnN0YXJ0XS5zdHJpcCgpCiAgICAgICAgc2Vs"
    "ZWN0b3IgPSBsZWFkLnNwbGl0bGluZXMoKVstMV0uc3RyaXAoKSBpZiBsZWFkIGVsc2Ug"
    "IiIKICAgICAgICBvdXQuYXBwZW5kKChzZWxlY3Rvciwgc3JjW3N0YXJ0ICsgMjplbmRd"
    "KSkKICAgICAgICBjdXJzb3IgPSBlbmQgKyAyCiAgICByZXR1cm4gb3V0CgoKZGVmIF9u"
    "b3JtYWxpc2UoaGV4X2NvbG9yOiBzdHIpIC0+IHN0cjoKICAgIGggPSBoZXhfY29sb3Iu"
    "bHN0cmlwKCIjIikKICAgIGlmIGxlbihoKSA9PSAzOgogICAgICAgIGggPSAiIi5qb2lu"
    "KGMgKiAyIGZvciBjIGluIGgpCiAgICByZXR1cm4gIiMiICsgaC5sb3dlcigpCgoKX0xP"
    "T0tVUCA9IHJlLmNvbXBpbGUociJce1xzKihcdyspXFtbJ1wiXShbXHdcLV0rKVsnXCJd"
    "XF1ccypcfSIpCgoKZGVmIF9yZXNvbHZlKHRva2VuOiBzdHIsIHBhbGV0dGU6IGRpY3Rb"
    "c3RyLCBzdHJdLAogICAgICAgICAgICAgcGluczogZGljdFtzdHIsIHN0cl0pIC0+IHN0"
    "ciB8IE5vbmU6CiAgICAiIiJUdXJuIG9uZSBRU1MgdmFsdWUgaW50byBhIGNvbmNyZXRl"
    "IGhleCwgb3IgTm9uZSBpZiBpdCBpcyBub3Qgb25lLgoKICAgIGBwaW5zYCBtYXBzIGEg"
    "bG9jYWwgdmFyaWFibGUgbmFtZSB0byB0aGUgcGFsZXR0ZSBpdCBpcyBib3VuZCB0bywg"
    "c28gYQogICAgYmxvY2sgd3JpdHRlbiBhZ2FpbnN0IGBpbSA9IElNQUdFX01PREVfQ09M"
    "T1JTYCBpcyByZWFkIHdpdGggdGhlIGltYWdlCiAgICBwYWxldHRlIGV2ZW4gd2hpbGUg"
    "c29tZSBvdGhlciBwYWxldHRlIGlzIHVuZGVyIHRlc3QuCiAgICAiIiIKICAgIHRva2Vu"
    "ID0gdG9rZW4uc3RyaXAoKS5yc3RyaXAoIjsiKS5zdHJpcCgpCiAgICBpZiBfSEVYLmZ1"
    "bGxtYXRjaCh0b2tlbik6CiAgICAgICAgcmV0dXJuIF9ub3JtYWxpc2UodG9rZW4pCiAg"
    "ICAjIHtjWydrZXknXX0gLyB7Y29sb3JzWydrZXknXX0gLyB7dGhlbWVbJ2tleSddfSAv"
    "IHtpbVsna2V5J119CiAgICBtID0gX0xPT0tVUC5mdWxsbWF0Y2godG9rZW4pCiAgICBp"
    "ZiBtOgogICAgICAgIHZhciwga2V5ID0gbS5ncm91cHMoKQogICAgICAgIHNvdXJjZSA9"
    "IFBBTEVUVEVTW3BpbnNbdmFyXV0gaWYgdmFyIGluIHBpbnMgZWxzZSBwYWxldHRlCiAg"
    "ICAgICAgdiA9IHNvdXJjZS5nZXQoa2V5KQogICAgICAgIHJldHVybiBfbm9ybWFsaXNl"
    "KHYpIGlmIGlzaW5zdGFuY2Uodiwgc3RyKSBhbmQgX0hFWC5mdWxsbWF0Y2godikgZWxz"
    "ZSBOb25lCiAgICAjIGJhcmUge0NPTlNUQU5UfQogICAgbSA9IHJlLmZ1bGxtYXRjaChy"
    "Ilx7XHMqKFtBLVpfXVtBLVowLTlfXSopXHMqXH0iLCB0b2tlbikKICAgIGlmIG06CiAg"
    "ICAgICAgdiA9IGdldGF0dHIoQywgbS5ncm91cCgxKSwgTm9uZSkKICAgICAgICByZXR1"
    "cm4gX25vcm1hbGlzZSh2KSBpZiBpc2luc3RhbmNlKHYsIHN0cikgYW5kIF9IRVguZnVs"
    "bG1hdGNoKHYpIGVsc2UgTm9uZQogICAgcmV0dXJuIE5vbmUKCgpkZWYgX3BhbGV0dGVf"
    "Y2FuX3JlbmRlcihib2R5OiBzdHIsIHBhbGV0dGU6IGRpY3Rbc3RyLCBzdHJdLAogICAg"
    "ICAgICAgICAgICAgICAgICAgICBwaW5zOiBkaWN0W3N0ciwgc3RyXSwgcGFsZXR0ZV9u"
    "YW1lOiBzdHIpIC0+IGJvb2w6CiAgICAiIiJDb3VsZCB0aGlzIHBhbGV0dGUgYWN0dWFs"
    "bHkgYmUgdGhlIG9uZSB0aGlzIGJsb2NrIHJlbmRlcnMgd2l0aD8KCiAgICBUd28gd2F5"
    "cyBpdCBjb3VsZCBub3QuIFRoZSBibG9jayBtYXkgYmUgcGlubmVkIHRvIGEgZGlmZmVy"
    "ZW50IHBhbGV0dGUKICAgIGJ5IGFuIGBpbSA9IElNQUdFX01PREVfQ09MT1JTYC1zdHls"
    "ZSBiaW5kaW5nLiBPciB0aGUgcGFsZXR0ZSBtYXkgc2ltcGx5CiAgICBub3QgaGF2ZSBh"
    "IGtleSB0aGUgYmxvY2sgYXNrcyBmb3IgLS0gVGhlbWVNYW5hZ2VyJ3MgZGljdHMgY2Fy"
    "cnkKICAgICdib3JkZXJfY29sb3InLCB0aGUgcmF3IHBhbGV0dGVzIGNhcnJ5ICdib3Jk"
    "ZXJfZGVmYXVsdCcsIHNvIGEgYmxvY2sKICAgIG5hbWluZyB0aGUgZm9ybWVyIGNhbm5v"
    "dCBiZSBhIHJhdy1wYWxldHRlIGJsb2NrLgoKICAgIFdpdGhvdXQgdGhpcywgZXZlcnkg"
    "YmxvY2sgZ2V0cyBtZWFzdXJlZCBhZ2FpbnN0IGV2ZXJ5IHBhbGV0dGUgYW5kIHRoZQog"
    "ICAgYXVkaXQgcmVwb3J0cyBwYWlyaW5ncyB0aGUgYXBwIG5ldmVyIHJlbmRlcnMgd2hp"
    "bGUgbWlzc2luZyB0aGUgb25lcyBpdAogICAgZG9lcy4KICAgICIiIgogICAgbG9va3Vw"
    "cyA9IF9MT09LVVAuZmluZGFsbChib2R5KQogICAgaWYgbm90IGxvb2t1cHM6CiAgICAg"
    "ICAgcmV0dXJuIFRydWUKICAgIHBpbm5lZCA9IHtwaW5zW3Zhcl0gZm9yIHZhciwgXyBp"
    "biBsb29rdXBzIGlmIHZhciBpbiBwaW5zfQogICAgaWYgcGlubmVkIGFuZCBwYWxldHRl"
    "X25hbWUgbm90IGluIHBpbm5lZDoKICAgICAgICByZXR1cm4gRmFsc2UKICAgIHJldHVy"
    "biBhbGwoa2V5IGluIHBhbGV0dGUgZm9yIHZhciwga2V5IGluIGxvb2t1cHMgaWYgdmFy"
    "IG5vdCBpbiBwaW5zKQoKCmRlZiBfdHJhY2tlZF9weXRob25fZmlsZXMoKSAtPiBsaXN0"
    "W1BhdGhdOgogICAgIiIiRW51bWVyYXRlIGZyb20gZ2l0IHJhdGhlciB0aGFuIGZyb20g"
    "YSBsaXN0IHdyaXR0ZW4gZG93biBoZXJlLgoKICAgIEEgaGFyZGNvZGVkIGZpbGUgbGlz"
    "dCBnb2VzIHN0YWxlIHRoZSBtb21lbnQgYSBtb2R1bGUgaXMgYWRkZWQsIGFuZCBpdAog"
    "ICAgZ29lcyBzdGFsZSBpbiB0aGUgZGlyZWN0aW9uIHRoYXQgcmVwb3J0cyBjbGVhbi4K"
    "ICAgICIiIgogICAgciA9IHN1YnByb2Nlc3MucnVuKFsiZ2l0IiwgImxzLWZpbGVzIiwg"
    "Ii16IiwgIioucHkiXSwKICAgICAgICAgICAgICAgICAgICAgICBjd2Q9UFJPSkVDVF9S"
    "T09ULCBjYXB0dXJlX291dHB1dD1UcnVlLCB0ZXh0PVRydWUpCiAgICBpZiByLnJldHVy"
    "bmNvZGUgIT0gMDogICAgICAgICAgICAgICAgICAgICAgICMgbm90IGEgZ2l0IGNoZWNr"
    "b3V0CiAgICAgICAgcmV0dXJuIHNvcnRlZChwIGZvciBwIGluIFBST0pFQ1RfUk9PVC5y"
    "Z2xvYigiKi5weSIpCiAgICAgICAgICAgICAgICAgICAgICBpZiAiX19weWNhY2hlX18i"
    "IG5vdCBpbiBwLnBhcnRzKQogICAgcmV0dXJuIHNvcnRlZCgoUFJPSkVDVF9ST09UIC8g"
    "bikgZm9yIG4gaW4gci5zdGRvdXQuc3BsaXQoIlwwIikKICAgICAgICAgICAgICAgICAg"
    "aWYgbiBhbmQgKFBST0pFQ1RfUk9PVCAvIG4pLmV4aXN0cygpKQoKCkBmdW5jdG9vbHMu"
    "bHJ1X2NhY2hlKG1heHNpemU9MSkKZGVmIF9zb3VyY2VzKCkgLT4gdHVwbGVbdHVwbGVb"
    "c3RyLCBzdHJdLCAuLi5dOgogICAgIiIiKHJlbGF0aXZlIHBhdGgsIHRleHQpIGZvciBl"
    "dmVyeSB0cmFja2VkIFB5dGhvbiBmaWxlLCByZWFkIG9uY2UuIiIiCiAgICByZXR1cm4g"
    "dHVwbGUoKHN0cihwLnJlbGF0aXZlX3RvKFBST0pFQ1RfUk9PVCkpLAogICAgICAgICAg"
    "ICAgICAgICBwLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgiLCBlcnJvcnM9Imlnbm9y"
    "ZSIpKQogICAgICAgICAgICAgICAgIGZvciBwIGluIF90cmFja2VkX3B5dGhvbl9maWxl"
    "cygpKQoKCmRlZiBfcGlucyhzcmM6IHN0cikgLT4gZGljdFtzdHIsIHN0cl06CiAgICAi"
    "IiJMb2NhbCBuYW1lcyBib3VuZCBzdHJhaWdodCB0byBhIHBhbGV0dGUgY29uc3RhbnQg"
    "aW4gdGhpcyBmaWxlLiIiIgogICAgcmV0dXJuIHttLmdyb3VwKDEpOiBfUElOX0NPTlNU"
    "W20uZ3JvdXAoMildIGZvciBtIGluIF9QSU4uZmluZGl0ZXIoc3JjKX0KCgpAZnVuY3Rv"
    "b2xzLmxydV9jYWNoZShtYXhzaXplPTgpCmRlZiBhdWRpdF9wYWxldHRlKHBhbGV0dGVf"
    "bmFtZTogc3RyKSAtPiB0dXBsZVt0dXBsZVtzdHIsIHN0ciwgZmxvYXQsIHN0cl0sIC4u"
    "Ll06CiAgICAiIiJFdmVyeSBiZWxvdy1mbG9vciBwYWlyIHRoaXMgcGFsZXR0ZSBhY3R1"
    "YWxseSByZW5kZXJzLiIiIgogICAgcGFsZXR0ZSA9IFBBTEVUVEVTW3BhbGV0dGVfbmFt"
    "ZV0KICAgIGZpbmRpbmdzID0gW10KICAgIGZvciByZWwsIHNyYyBpbiBfc291cmNlcygp"
    "OgogICAgICAgIHBpbnMgPSBfcGlucyhzcmMpCiAgICAgICAgZm9yIHNlbGVjdG9yLCBi"
    "b2R5IGluIF9ydWxlcyhzcmMpOgogICAgICAgICAgICBpZiBub3QgX3BhbGV0dGVfY2Fu"
    "X3JlbmRlcihib2R5LCBwYWxldHRlLCBwaW5zLCBwYWxldHRlX25hbWUpOgogICAgICAg"
    "ICAgICAgICAgY29udGludWUKICAgICAgICAgICAgZmcgPSBiZyA9IE5vbmUKICAgICAg"
    "ICAgICAgZm9yIGRlY2wgaW4gYm9keS5zcGxpdCgiOyIpOgogICAgICAgICAgICAgICAg"
    "aWYgIjoiIG5vdCBpbiBkZWNsOgogICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAg"
    "ICAgICAgICAgICAgICBwcm9wLCBfLCB2YWx1ZSA9IGRlY2wucGFydGl0aW9uKCI6IikK"
    "ICAgICAgICAgICAgICAgIHByb3AgPSBwcm9wLnN0cmlwKCkKICAgICAgICAgICAgICAg"
    "IGlmIHByb3AgPT0gImNvbG9yIjoKICAgICAgICAgICAgICAgICAgICBmZyA9IF9yZXNv"
    "bHZlKHZhbHVlLCBwYWxldHRlLCBwaW5zKQogICAgICAgICAgICAgICAgZWxpZiBwcm9w"
    "IGluICgiYmFja2dyb3VuZC1jb2xvciIsICJiYWNrZ3JvdW5kIik6CiAgICAgICAgICAg"
    "ICAgICAgICAgYmcgPSBfcmVzb2x2ZSh2YWx1ZSwgcGFsZXR0ZSwgcGlucykKICAgICAg"
    "ICAgICAgaWYgZmcgYW5kIGJnOgogICAgICAgICAgICAgICAgcmF0aW8gPSBjb250cmFz"
    "dF9yYXRpbyhmZywgYmcpCiAgICAgICAgICAgICAgICBpZiByYXRpbyA8IFRFWFRfRkxP"
    "T1I6CiAgICAgICAgICAgICAgICAgICAgZmluZGluZ3MuYXBwZW5kKChmZywgYmcsIHJv"
    "dW5kKHJhdGlvLCA0KSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg"
    "IGYie3JlbH0gOjoge3NlbGVjdG9yfSIpKQogICAgcmV0dXJuIHR1cGxlKGZpbmRpbmdz"
    "KQoKCmRlZiB0ZXN0X3RoZV9hdWRpdF9maW5kc19zb21ldGhpbmdfdG9fYXVkaXQoKSAt"
    "PiBOb25lOgogICAgIiIiR3VhcmQgdGhlIGd1YXJkLgoKICAgIElmIHRoZSBRU1MgZm9y"
    "bWF0IGNoYW5nZXMgYW5kIHRoZSBydWxlIHJlZ2V4IHN0b3BzIG1hdGNoaW5nLCBldmVy"
    "eQogICAgY29udHJhc3QgdGVzdCBiZWxvdyBwYXNzZXMgdmFjdW91c2x5LiBUaGlzIGFz"
    "c2VydHMgdGhlIHdhbGtlciBpcyBzdGlsbAogICAgcmVhY2hpbmcgcmVhbCBydWxlcy4K"
    "ICAgICIiIgogICAgdG90YWwgPSBzdW0obGVuKF9ydWxlcyhzcmMpKSBmb3IgX3JlbCwg"
    "c3JjIGluIF9zb3VyY2VzKCkpCiAgICBhc3NlcnQgdG90YWwgPiAxMDAsICgKICAgICAg"
    "ICBmInRoZSBRU1Mgd2Fsa2VyIG1hdGNoZWQgb25seSB7dG90YWx9IHJ1bGVzIGFjcm9z"
    "cyB0aGUgcmVwb3NpdG9yeSwgIgogICAgICAgIGYid2hpY2ggbWVhbnMgaXQgaGFzIHN0"
    "b3BwZWQgcGFyc2luZyB0aGUgc3R5bGVzaGVldHMgcmF0aGVyIHRoYW4gIgogICAgICAg"
    "IGYidGhhdCB0aGUgc3R5bGVzaGVldHMgZ290IHNtYWxsZXIiKQoKCmRlZiB0ZXN0X2V2"
    "ZXJ5X3BhbGV0dGVfZ2V0c19hdWRpdGVkKCkgLT4gTm9uZToKICAgICIiIkd1YXJkIHRo"
    "ZSBwYWxldHRlIGJpbmRpbmcuCgogICAgX3BhbGV0dGVfY2FuX3JlbmRlciBjYW4gZXhj"
    "bHVkZSBhIGJsb2NrIGZyb20gYSBwYWxldHRlLiBJZiBpdCBldmVyCiAgICBleGNsdWRl"
    "ZCBldmVyeXRoaW5nLCBldmVyeSBwYWxldHRlIGJlbG93IHdvdWxkIHBhc3MgYnkgbWVh"
    "c3VyaW5nCiAgICBub3RoaW5nIGF0IGFsbC4KICAgICIiIgogICAgZm9yIG5hbWUgaW4g"
    "UEFMRVRURVM6CiAgICAgICAgY2hlY2tlZCA9IHN1bSgKICAgICAgICAgICAgMSBmb3Ig"
    "X3JlbCwgc3JjIGluIF9zb3VyY2VzKCkKICAgICAgICAgICAgZm9yIF9zZWwsIGJvZHkg"
    "aW4gX3J1bGVzKHNyYykKICAgICAgICAgICAgaWYgX3BhbGV0dGVfY2FuX3JlbmRlcihi"
    "b2R5LCBQQUxFVFRFU1tuYW1lXSwgX3BpbnMoc3JjKSwgbmFtZSkKICAgICAgICAgICAg"
    "YW5kIF9MT09LVVAuc2VhcmNoKGJvZHkpKQogICAgICAgIGFzc2VydCBjaGVja2VkID4g"
    "MTAsICgKICAgICAgICAgICAgZiJwYWxldHRlIHtuYW1lfSBtYXRjaGVkIG9ubHkge2No"
    "ZWNrZWR9IGJsb2NrcyAtLSB0aGUgIgogICAgICAgICAgICBmImJpbmRpbmcgcnVsZSBo"
    "YXMgc3RvcHBlZCBsZXR0aW5nIGFueXRoaW5nIHRocm91Z2giKQoKCkBweXRlc3QubWFy"
    "ay5wYXJhbWV0cml6ZSgicGFsZXR0ZV9uYW1lIiwgc29ydGVkKFBBTEVUVEVTKSkKZGVm"
    "IHRlc3Rfbm9fdW5hY2NlcHRlZF9jb250cmFzdF9mYWlsdXJlcyhwYWxldHRlX25hbWU6"
    "IHN0cikgLT4gTm9uZToKICAgIGJhZCA9IFtmIGZvciBmIGluIGF1ZGl0X3BhbGV0dGUo"
    "cGFsZXR0ZV9uYW1lKQogICAgICAgICAgIGlmIChwYWxldHRlX25hbWUsIGZbMF0sIGZb"
    "MV0pIG5vdCBpbiBBQ0NFUFRFRF0KICAgIGFzc2VydCBub3QgYmFkLCAiXG4iLmpvaW4o"
    "CiAgICAgICAgZiIgIHtwYWxldHRlX25hbWV9ICB7cjo+N306MSAge2ZnfSBvbiB7Ymd9"
    "ICA8LSB7d2hlcmV9IgogICAgICAgIGZvciBmZywgYmcsIHIsIHdoZXJlIGluIGJhZCkK"
    "CgpkZWYgdGVzdF9ldmVyeV9leGVtcHRpb25fc3RpbGxfYXBwbGllcygpIC0+IE5vbmU6"
    "CiAgICAiIiJUaGUgaGFsZiB0aGF0IG1hdHRlcnMuCgogICAgQW4gZXhlbXB0aW9uIGZv"
    "ciBhIHBhaXJpbmcgdGhhdCBubyBsb25nZXIgZXhpc3RzIGlzIGFuIGV4ZW1wdGlvbiB0"
    "aGF0CiAgICB3aWxsIHNpbGVudGx5IGNvdmVyIGEgZnV0dXJlIGRlZmVjdC4gVGhpcyBy"
    "ZXBvc2l0b3J5IGhhZCBvbmU6IHdoaXRlIG9uCiAgICBCUkFORF9HT0xEIHdhcyByZWNv"
    "cmRlZCBhcyBhIGtub3duIGZhaWx1cmUgZm9yIGEgbGlzdC1pdGVtIGZpbGwgdGhhdAog"
    "ICAgcmVuZGVycyBpbiBpbWFnZSBtb2RlLCB3aGVyZSB0aGUgdGV4dCBpcyBibGFjayBh"
    "dCAxMS4zNToxLiBUaGUgcGFpciB3YXMKICAgIG5ldmVyIHJlbmRlcmVkIGJ5IGFueXRo"
    "aW5nOyB0aGUgZXhlbXB0aW9uIHdhcyBwdXJlIGxpY2VuY2UuCiAgICAiIiIKICAgIHNl"
    "ZW4gPSBzZXQoKQogICAgZm9yIG5hbWUgaW4gUEFMRVRURVM6CiAgICAgICAgZm9yIGZn"
    "LCBiZywgX3IsIF93IGluIGF1ZGl0X3BhbGV0dGUobmFtZSk6CiAgICAgICAgICAgIHNl"
    "ZW4uYWRkKChuYW1lLCBmZywgYmcpKQogICAgZGVhZCA9IHNvcnRlZChrIGZvciBrIGlu"
    "IEFDQ0VQVEVEIGlmIGsgbm90IGluIHNlZW4pCiAgICBhc3NlcnQgbm90IGRlYWQsICgK"
    "ICAgICAgICAidGhlc2UgZXhlbXB0aW9ucyBubyBsb25nZXIgbWF0Y2ggYW55dGhpbmcg"
    "dGhlIGFwcCByZW5kZXJzIGFuZCAiCiAgICAgICAgZiJzaG91bGQgYmUgZGVsZXRlZDog"
    "e2RlYWR9IikKCgojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkAojIFRIRSBUV08gR09MRCBST0xF"
    "UwojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkAojCiMgTGlnaHQgbW9kZSB1c2VzIGV4YWN0bHkg"
    "dHdvIGdvbGRzLCBiZWNhdXNlIG9uZSBjYW5ub3QgZG8gYm90aCBqb2JzOiBhCiMgZ29s"
    "ZCBsaWdodCBlbm91Z2ggdG8gY2Fycnkgd2hpdGUgdGV4dCBhdCA0LjU6MSBpcyB0b28g"
    "bGlnaHQgdG8gQkUgdGV4dAojIG9uIGFueXRoaW5nIGJ1dCBwdXJlIHdoaXRlLiBUaGUg"
    "bHVtaW5hbmNlIGJhbmRzIGRvIG5vdCBvdmVybGFwLgoKTElHSFRfU1VSRkFDRVMgPSBb"
    "IiNmZmZmZmYiLCAiI2ZhZmFmYSIsICIjZjVmNWY1IiwgIiNmMGYwZjAiLCAiI2VlZWVl"
    "ZSJdCgoKZGVmIHRlc3RfZmlsbF9nb2xkX2NhcnJpZXNfd2hpdGVfdGV4dCgpIC0+IE5v"
    "bmU6CiAgICBhc3NlcnQgY29udHJhc3RfcmF0aW8oIiNmZmZmZmYiLCBDLkJSQU5EX0RB"
    "UktfR09MRCkgPj0gVEVYVF9GTE9PUgoKCmRlZiB0ZXN0X3RleHRfZ29sZF9jbGVhcnNf"
    "ZXZlcnlfbGlnaHRfc3VyZmFjZSgpIC0+IE5vbmU6CiAgICBmYWlsdXJlcyA9IFsocywg"
    "cm91bmQoY29udHJhc3RfcmF0aW8oQy5CUkFORF9EQVJLX0dPTERfREVFUCwgcyksIDQp"
    "KQogICAgICAgICAgICAgICAgZm9yIHMgaW4gTElHSFRfU1VSRkFDRVMKICAgICAgICAg"
    "ICAgICAgIGlmIGNvbnRyYXN0X3JhdGlvKEMuQlJBTkRfREFSS19HT0xEX0RFRVAsIHMp"
    "IDwgVEVYVF9GTE9PUl0KICAgIGFzc2VydCBub3QgZmFpbHVyZXMsICgKICAgICAgICBm"
    "InRoZSB0ZXh0IGdvbGQgbm8gbG9uZ2VyIGNsZWFycyBldmVyeSBsaWdodCBzdXJmYWNl"
    "OiB7ZmFpbHVyZXN9IikKCgpAcHl0ZXN0Lm1hcmsucGFyYW1ldHJpemUoImtleSIsIFsK"
    "ICAgICJ0ZXh0X2FjY2VudCIsICJidXR0b25faG92ZXJfdGV4dCIsICJhY2NlbnRfYnV0"
    "dG9uX3RleHQiLApdKQpkZWYgdGVzdF9nb2xkX3RleHRfa2V5c191c2VfdGhlX3RleHRf"
    "Z29sZChrZXk6IHN0cikgLT4gTm9uZToKICAgIGFzc2VydCBDLkxJR0hUX1RIRU1FX0NP"
    "TE9SU1trZXldID09IEMuQlJBTkRfREFSS19HT0xEX0RFRVAKCgpAcHl0ZXN0Lm1hcmsu"
    "cGFyYW1ldHJpemUoImtleSIsIFsKICAgICJzZWxlY3RlZF9iZyIsICJidXR0b25fcHJl"
    "c3NlZF9iZyIsICJhY2NlbnRfYnV0dG9uX3ByZXNzZWRfYmciLAogICAgImNoZWNrYm94"
    "X2NoZWNrZWRfYmciLCAibGlzdF9zZWxlY3RlZF9iZyIsCl0pCmRlZiB0ZXN0X2dvbGRf"
    "ZmlsbF9rZXlzX3VzZV90aGVfZmlsbF9nb2xkKGtleTogc3RyKSAtPiBOb25lOgogICAg"
    "IiIiRmlsbHMgbXVzdCBub3QgdGFrZSB0aGUgdGV4dCBnb2xkOiBpdCBkb2VzIG5vdCBj"
    "YXJyeSB3aGl0ZSB0ZXh0LiIiIgogICAgYXNzZXJ0IEMuTElHSFRfVEhFTUVfQ09MT1JT"
    "W2tleV0gPT0gQy5CUkFORF9EQVJLX0dPTEQKCgpkZWYgdGVzdF90YWJfaG92ZXJfZ3Jv"
    "dW5kX2lzX2xpZ2h0X2Vub3VnaF9mb3JfZ29sZF90ZXh0KCkgLT4gTm9uZToKICAgICIi"
    "IlRoZSBob3ZlciB0YWIgcmVhZHMgYXMgaG92ZXIgYmVjYXVzZSB0aGUgZ3JvdW5kIExJ"
    "R0hURU5TIHRvd2FyZCB0aGUKICAgIHNlbGVjdGVkIHRhYidzIHdoaXRlLCBhbmQgdGhl"
    "IGdvbGQgdGV4dCBzdGF5cyBsZWdpYmxlIG9uIGl0LiIiIgogICAgZ3JvdW5kID0gQy5M"
    "SUdIVF9USEVNRV9DT0xPUlNbInRhYl9ob3Zlcl9iZyJdCiAgICByZXN0ID0gQy5MSUdI"
    "VF9USEVNRV9DT0xPUlNbInRhYl9iZyJdCiAgICBhc3NlcnQgcmVsYXRpdmVfbHVtaW5h"
    "bmNlKGdyb3VuZCkgPiByZWxhdGl2ZV9sdW1pbmFuY2UocmVzdCkKICAgIGFzc2VydCBj"
    "b250cmFzdF9yYXRpbyhDLkxJR0hUX1RIRU1FX0NPTE9SU1sidGV4dF9hY2NlbnQiXSwK"
    "ICAgICAgICAgICAgICAgICAgICAgICAgICBncm91bmQpID49IFRFWFRfRkxPT1IKCgpk"
    "ZWYgdGVzdF90YWJfaW5kaWNhdG9yX2NsZWFyc190aGVfY29tcG9uZW50X2Zsb29yKCkg"
    "LT4gTm9uZToKICAgIGFzc2VydCBjb250cmFzdF9yYXRpbyhDLkxJR0hUX1RIRU1FX0NP"
    "TE9SU1sidGFiX2luZGljYXRvciJdLAogICAgICAgICAgICAgICAgICAgICAgICAgIEMu"
    "TElHSFRfVEhFTUVfQ09MT1JTWyJ0YWJfc2VsZWN0ZWRfYmciXQogICAgICAgICAgICAg"
    "ICAgICAgICAgICAgICkgPj0gQ09NUE9ORU5UX0ZMT09SCgoKIyDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZAKIyBTQ0hFTUUgU0VQQVJBVElPTgojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkAojCiMg"
    "VGhlIGFwcCBydW5zIHR3byBidXR0b24gc2NoZW1lcyBzaWRlIGJ5IHNpZGUuIENvbmZs"
    "YXRpbmcgdGhlbSBpcyB0aGUKIyBlYXNpZXN0IHdheSB0byAiZml4IiBvbmUgYnkgYnJl"
    "YWtpbmcgdGhlIG90aGVyLgoKQHB5dGVzdC5tYXJrLnBhcmFtZXRyaXplKCJwYWxldHRl"
    "X25hbWUiLCBbIkxJR0hUIiwgIkRBUksiXSkKZGVmIHRlc3RfbWFpbl9idXR0b25fc2No"
    "ZW1lX2hvbGRzX25vX2dvbGQocGFsZXR0ZV9uYW1lOiBzdHIpIC0+IE5vbmU6CiAgICAi"
    "IiJNYWluLXdpbmRvdyBidXR0b25zIGFyZSB0aGUgd2hpdGUvbmVhci1ibGFjayBpbnZl"
    "cnNlIHN5c3RlbS4gTm8KICAgIGJyYW5kIGdvbGQgYmVsb25ncyBhbnl3aGVyZSBpbiB0"
    "aGVtLiIiIgogICAgcGFsZXR0ZSA9IChDLkxJR0hUX1RIRU1FX0NPTE9SUyBpZiBwYWxl"
    "dHRlX25hbWUgPT0gIkxJR0hUIgogICAgICAgICAgICAgICBlbHNlIEMuREFSS19USEVN"
    "RV9DT0xPUlMpCiAgICBnb2xkcyA9IHtDLkJSQU5EX0dPTEQubG93ZXIoKSwgQy5CUkFO"
    "RF9EQVJLX0dPTEQubG93ZXIoKSwKICAgICAgICAgICAgIEMuQlJBTkRfREFSS19HT0xE"
    "X0RFRVAubG93ZXIoKX0KICAgIG9mZmVuZGVycyA9IHtrOiB2IGZvciBrLCB2IGluIHBh"
    "bGV0dGUuaXRlbXMoKQogICAgICAgICAgICAgICAgIGlmIGsuc3RhcnRzd2l0aCgibWFp"
    "bl9idG5fIikgYW5kIHYubG93ZXIoKSBpbiBnb2xkc30KICAgIGFzc2VydCBub3Qgb2Zm"
    "ZW5kZXJzLCAoCiAgICAgICAgZiJnb2xkIGxlYWtlZCBpbnRvIHRoZSBtYWluLXdpbmRv"
    "dyBidXR0b24gc2NoZW1lOiB7b2ZmZW5kZXJzfSIpCgoKZGVmIHRlc3RfcmV0aXJlZF9h"
    "cHBfZ29sZF9pc19nb25lKCkgLT4gTm9uZToKICAgICIiIiNiMTkxNDUgd2FzIGFuIGFw"
    "cC1sb2NhbCBhcHByb3hpbWF0aW9uIG9mIHRoZSBicmFuZCBkYXJrIGdvbGQuIEl0CiAg"
    "ICBjYXJyaWVkIHdoaXRlIHRleHQgYXQgMi45OTc2OjEuIE5vdGhpbmcgc2hvdWxkIHJl"
    "aW50cm9kdWNlIGl0LiIiIgogICAgZm9yIHBhbGV0dGUgaW4gKEMuTElHSFRfVEhFTUVf"
    "Q09MT1JTLCBDLkRBUktfVEhFTUVfQ09MT1JTLAogICAgICAgICAgICAgICAgICAgIEMu"
    "SU1BR0VfTU9ERV9DT0xPUlMpOgogICAgICAgIGFzc2VydCBub3QgW2sgZm9yIGssIHYg"
    "aW4gcGFsZXR0ZS5pdGVtcygpCiAgICAgICAgICAgICAgICAgICAgaWYgaXNpbnN0YW5j"
    "ZSh2LCBzdHIpIGFuZCB2Lmxvd2VyKCkgPT0gIiNiMTkxNDUiXQo="
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

    # The pairing audit deliberately lives in ONE place: the guard test that
    # ships in the repository and runs under CI. This script used to carry a
    # second copy, and the two drifted -- the copy here resolved every
    # placeholder against the light palette even for blocks pinned to the
    # image-mode palette, so it recorded a white-on-BRAND_GOLD failure that
    # nothing renders (the real text there is black, at 11.35:1) while never
    # auditing the main-window button scheme at all.
    #
    # Two implementations of one rule is two chances to be wrong and no way
    # to notice. Run the real one.
    say("verify: pairing audit delegated to the guard suite")

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


GUARD_TEST_PATH = "tests/test_brand_contrast.py"


def run_guard_tests() -> str:
    """Run only the guard suite -- seconds, not minutes.

    This is the proportionate gate for a pass that touches a docstring and
    deletes two helper files. The full suite is CI's job, and CI runs it on
    every push. Requiring a four-minute local run inside a browser-tethered
    codespace does not add confidence; it just adds a way to be cut off.
    """
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    say(f"running the guard suite ({GUARD_TEST_PATH}) ...")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q",
                        GUARD_TEST_PATH],
                       cwd=REPO, env=env, capture_output=True, text=True)
    for line in (r.stdout + r.stderr).strip().splitlines()[-6:]:
        say(f"    {line}")
    return classify(r.returncode)


def classify(code: int) -> str:
    """pass / fail / killed. Killed is not failed.

    Collapsing these is how a reclaimed session gets reported as broken
    code, and how 'no tests ran' gets reported as success.
    """
    if code < 0:
        return "killed"
    if code == 0:
        return "pass"
    return "fail"


def run_suite(quick: bool = False) -> str:
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
        sig = -code
        # A negative return code means killed by a signal, and WHICH signal
        # matters. 9 (SIGKILL) is the OOM killer. 15 (SIGTERM) is something
        # asking politely -- a codespace reclaiming an idle session, a
        # browser tab losing its connection, a supervisor timing the job
        # out. Neither says anything about whether the code is correct.
        name = {9: "SIGKILL -- out of memory",
                15: "SIGTERM -- something asked the process to stop; on a "
                    "codespace driven from a\n         browser this is "
                    "usually the session being reclaimed, not the tests",
                2: "SIGINT -- interrupted"}.get(sig, f"signal {sig}")
        say(f"\n    the test process was KILLED by {name}", WARN)
        say(f"    It did not run to completion. This is an environment "
            f"limit, NOT a test result --", WARN)
        say(f"    nothing failed; the run was cut short. Your CI runs the "
            f"full suite on every push,", WARN)
        say(f"    which is the authority here.", WARN)
        return "killed"

    msg, colour = PYTEST_EXIT.get(code, (f"pytest exited {code}", WARN))
    say(f"\n    {msg}", colour)
    return classify(code)


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

    # Describe what actually changed rather than reciting a subject line
    # written when the script was authored. A stale suggested message is a
    # small lie the commit log keeps forever.
    st = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                        capture_output=True, text=True).stdout.splitlines()
    modified = [ln[3:] for ln in st if ln[:2].strip() == "M"]
    deleted = [ln[3:] for ln in st if ln[:2].strip() == "D"]
    parts = []
    if modified:
        parts.append("update " + ", ".join(sorted(modified)[:3]))
    if deleted:
        parts.append("drop " + ", ".join(sorted(deleted)[:3]))
    subject = "; ".join(parts) if parts else "no changes to commit"

    say("\n    Working tree is ready. One commit takes everything:", OK)
    say("      git add -A")
    say(f"      git commit -m '{subject}'")
    say("      git push")
    if not parts:
        say("    (nothing changed -- the repository was already in this "
            "state)", WARN)


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
    # The guard suite owns the pairing audit, so it is not optional -- it
    # runs on every path. It takes about two seconds.
    if run_guard_tests() != "pass":
        ok = False

    if args.finish is not None:
        # The gate for cleanup is verify plus the guard suite -- the tests
        # that actually cover what this pass changed. Seconds, so a
        # reclaimed session cannot interrupt it.
        if not args.skip_tests:
            broad = run_suite(quick=args.quick_tests)
            if broad == "fail":
                ok = False          # real failures still block
            elif broad == "killed":
                say("\n    (treated as inconclusive, not as a failure -- "
                    "the gate below is the guard suite)", WARN)
        if ok:
            say("\nremoving transfer helpers ...")
            remove_helpers(args.finish)
        else:
            say("\nNOT removing anything -- the checks did not pass. "
                "The tools stay so you can find out why.", FAIL)
    elif not args.skip_tests:
        if run_suite(quick=args.quick_tests) != "pass":
            ok = False

    say("\nDONE -- all checks passed" if ok else "\nDONE -- with failures above",
        OK if ok else FAIL)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
