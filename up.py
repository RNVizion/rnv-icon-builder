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
    "PT09PT09PT09PT09PT09PQoKVGhlc2UgdGVzdHMgZG8gbm90IGNoZWNrIHRoYXQgY29s"
    "b3VycyBoYXZlIHBhcnRpY3VsYXIgdmFsdWVzLiBUaGV5IGNoZWNrCnR3byB0aGluZ3Mg"
    "dGhhdCBhIHZhbHVlIHRlc3QgY2Fubm90OgoKICAxLiBFdmVyeSBjb25zdGFudCBsYWJl"
    "bGxlZCAiZGVyaXZlZCIgaXMgZ2VudWluZWx5IGNvbXB1dGVkIGZyb20gaXRzCiAgICAg"
    "c291cmNlLCBjaGVja2VkIGJ5IHBhcnNpbmcgdGhlIHNvdXJjZSByYXRoZXIgdGhhbiBi"
    "eSBjb21wYXJpbmcgYXQKICAgICBydW50aW1lLiBBIHdyaXR0ZW4tZG93biBsaXRlcmFs"
    "IHRoYXQgaGFwcGVucyB0byBlcXVhbAogICAgIGxpZ2h0ZW4oQlJBTkRfREFSS19HT0xE"
    "LCAtMTQpIGlzIGluZGlzdGluZ3Vpc2hhYmxlIGZyb20gdGhlIHJlYWwKICAgICB0aGlu"
    "ZyBvbmNlIHRoZSBtb2R1bGUgaXMgaW1wb3J0ZWQgLS0gYW5kIGl0IGlzIGV4YWN0bHkg"
    "d2hhdCBicmVha3MKICAgICB0aGUgbmV4dCB0aW1lIHRoZSBzb3VyY2UgY29sb3VyIG1v"
    "dmVzLiBPbmx5IHRoZSBBU1QgY2FuIHRlbGwgdGhlbQogICAgIGFwYXJ0LgoKICAyLiBF"
    "dmVyeSBmb3JlZ3JvdW5kL2JhY2tncm91bmQgcGFpciB0aGUgYXBwIGFjdHVhbGx5IHJl"
    "bmRlcnMgY2xlYXJzIHRoZQogICAgIFdDQUcgZmxvb3IsIHJlc29sdmVkIGFnYWluc3Qg"
    "dGhlIHJlYWwgYmFja2dyb3VuZCBpbiBzY29wZSByYXRoZXIKICAgICB0aGFuIGFnYWlu"
    "c3QgYW4gYXNzdW1lZCBvbmUuIEEgY2Vuc3VzIG9mIHZhbHVlcyBjYW5ub3QgZmluZCB0"
    "aGVzZToKICAgICBpbiBhbG1vc3QgZXZlcnkgZGVmZWN0IG9mIHRoaXMga2luZCBib3Ro"
    "IGNvbG91cnMgYXJlIGluZGl2aWR1YWxseQogICAgIGNvcnJlY3QgYW5kIGl0IGlzIHRo"
    "ZSBwYWlyaW5nIHRoYXQgZmFpbHMuCgpUaGUgZXhlbXB0aW9uIGxpc3QgaXMgYXNzZXJ0"
    "ZWQgaW4gQk9USCBkaXJlY3Rpb25zLiBBbiB1bmV4cGVjdGVkIGZhaWx1cmUKZmFpbHMg"
    "dGhlIHN1aXRlLCBhbmQgc28gZG9lcyBhbiBleGVtcHRpb24gdGhhdCBubyBsb25nZXIg"
    "bWF0Y2hlcyBhbnl0aGluZy4KRXhlbXB0aW9uIGxpc3RzIGFsd2F5cyBnbyBzdGFsZSBp"
    "biB0aGUgZGlyZWN0aW9uIHRoYXQgcmVwb3J0cyBjbGVhbiwgc28KdGhlIHNlY29uZCBo"
    "YWxmIGlzIHRoZSBoYWxmIHRoYXQgbWF0dGVycy4KIiIiCgpmcm9tIF9fZnV0dXJlX18g"
    "aW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgYXN0CmltcG9ydCBmdW5jdG9vbHMKaW1w"
    "b3J0IHJlCmltcG9ydCBzdWJwcm9jZXNzCmZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aAoK"
    "aW1wb3J0IHB5dGVzdAoKZnJvbSB1aSBpbXBvcnQgY29sb3JzIGFzIEMKCgpQUk9KRUNU"
    "X1JPT1QgPSBQYXRoKF9fZmlsZV9fKS5yZXNvbHZlKCkucGFyZW50LnBhcmVudApDT0xP"
    "UlNfUFkgPSBQUk9KRUNUX1JPT1QgLyAidWkiIC8gImNvbG9ycy5weSIKClRFWFRfRkxP"
    "T1IgPSA0LjUgICAgICAgICAgIyBXQ0FHIDEuNC4zLCBub3JtYWwtc2l6ZSB0ZXh0CkNP"
    "TVBPTkVOVF9GTE9PUiA9IDMuMCAgICAgIyBXQ0FHIDEuNC4xMSwgVUkgY29tcG9uZW50"
    "cyBhbmQgZ3JhcGhpY3MKCgojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkAojIENPTlRSQVNUCiMg"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQCgpkZWYgcmVsYXRpdmVfbHVtaW5hbmNlKGhleF9jb2xv"
    "cjogc3RyKSAtPiBmbG9hdDoKICAgIGggPSBoZXhfY29sb3IubHN0cmlwKCIjIikKICAg"
    "IGlmIGxlbihoKSA9PSAzOgogICAgICAgIGggPSAiIi5qb2luKGMgKiAyIGZvciBjIGlu"
    "IGgpCiAgICBjaCA9IFtpbnQoaFtpOmkgKyAyXSwgMTYpIC8gMjU1IGZvciBpIGluICgw"
    "LCAyLCA0KV0KICAgIGNoID0gW2MgLyAxMi45MiBpZiBjIDw9IDAuMDQwNDUgZWxzZSAo"
    "KGMgKyAwLjA1NSkgLyAxLjA1NSkgKiogMi40CiAgICAgICAgICBmb3IgYyBpbiBjaF0K"
    "ICAgIHJldHVybiAwLjIxMjYgKiBjaFswXSArIDAuNzE1MiAqIGNoWzFdICsgMC4wNzIy"
    "ICogY2hbMl0KCgpkZWYgY29udHJhc3RfcmF0aW8oZmc6IHN0ciwgYmc6IHN0cikgLT4g"
    "ZmxvYXQ6CiAgICBsMSwgbDIgPSBzb3J0ZWQoW3JlbGF0aXZlX2x1bWluYW5jZShmZyks"
    "IHJlbGF0aXZlX2x1bWluYW5jZShiZyldLAogICAgICAgICAgICAgICAgICAgIHJldmVy"
    "c2U9VHJ1ZSkKICAgIHJldHVybiAobDEgKyAwLjA1KSAvIChsMiArIDAuMDUpCgoKIyDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZAKIyBERVJJVkFUSU9OIEdVQVJECiMg4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQCgojIENvbnN0YW50cyB3aG9zZSBkb2NzdHJpbmcgY2xhaW1zIHRoZXkgYXJl"
    "IGRlcml2ZWQuIEVhY2ggbXVzdCBiZSBhIGNhbGwKIyBleHByZXNzaW9uIGluIHRoZSBz"
    "b3VyY2UsIG5vdCBhIGxpdGVyYWwuCkRFUklWRURfQ09OU1RBTlRTID0gewogICAgIkJS"
    "QU5EX0RBUktfR09MRF9ERUVQIiwKICAgICJCUkFORF9HT0xEX1JHQiIsCiAgICAiQlJB"
    "TkRfREFSS19HT0xEX1JHQiIsCn0KCiMgQ29uc3RhbnRzIHRoYXQgYXJlIHJlZ2lzdGVy"
    "ZWQgYnJhbmQgdmFsdWVzIGFuZCBtdXN0IHRoZXJlZm9yZSBiZSBsaXRlcmFscy4KIyBE"
    "ZXJpdmluZyBvbmUgb2YgdGhlc2Ugd291bGQgaW52ZXJ0IHRoZSByZWxhdGlvbnNoaXA6"
    "IHRoZSByZWdpc3RlciBpcyB0aGUKIyBzb3VyY2UsIHNvIGEgcmVnaXN0ZXJlZCBjb2xv"
    "dXIgY2Fubm90IGJlIGNvbXB1dGVkIGZyb20gc29tZXRoaW5nIGVsc2UuClJFR0lTVEVS"
    "RURfQ09OU1RBTlRTID0gewogICAgIkJSQU5EX0dPTEQiLAogICAgIkJSQU5EX0RBUktf"
    "R09MRCIsCn0KCgpkZWYgX21vZHVsZV9sZXZlbF9hc3NpZ25tZW50cygpIC0+IGRpY3Rb"
    "c3RyLCBhc3QuZXhwcl06CiAgICB0cmVlID0gYXN0LnBhcnNlKENPTE9SU19QWS5yZWFk"
    "X3RleHQoZW5jb2Rpbmc9InV0Zi04IikpCiAgICBvdXQ6IGRpY3Rbc3RyLCBhc3QuZXhw"
    "cl0gPSB7fQogICAgZm9yIG5vZGUgaW4gdHJlZS5ib2R5OgogICAgICAgIGlmIGlzaW5z"
    "dGFuY2Uobm9kZSwgYXN0LkFubkFzc2lnbikgYW5kIGlzaW5zdGFuY2Uobm9kZS50YXJn"
    "ZXQsIGFzdC5OYW1lKToKICAgICAgICAgICAgaWYgbm9kZS52YWx1ZSBpcyBub3QgTm9u"
    "ZToKICAgICAgICAgICAgICAgIG91dFtub2RlLnRhcmdldC5pZF0gPSBub2RlLnZhbHVl"
    "CiAgICAgICAgZWxpZiBpc2luc3RhbmNlKG5vZGUsIGFzdC5Bc3NpZ24pOgogICAgICAg"
    "ICAgICBmb3IgdCBpbiBub2RlLnRhcmdldHM6CiAgICAgICAgICAgICAgICBpZiBpc2lu"
    "c3RhbmNlKHQsIGFzdC5OYW1lKSBhbmQgbm9kZS52YWx1ZSBpcyBub3QgTm9uZToKICAg"
    "ICAgICAgICAgICAgICAgICBvdXRbdC5pZF0gPSBub2RlLnZhbHVlCiAgICByZXR1cm4g"
    "b3V0CgoKQHB5dGVzdC5tYXJrLnBhcmFtZXRyaXplKCJuYW1lIiwgc29ydGVkKERFUklW"
    "RURfQ09OU1RBTlRTKSkKZGVmIHRlc3RfZGVyaXZlZF9jb25zdGFudF9pc19hY3R1YWxs"
    "eV9jb21wdXRlZChuYW1lOiBzdHIpIC0+IE5vbmU6CiAgICAiIiJBIGRlcml2ZWQgY29u"
    "c3RhbnQgbXVzdCBiZSBhIGNhbGwsIG5vdCBhIGxpdGVyYWwgdGhhdCBsb29rcyByaWdo"
    "dC4iIiIKICAgIGFzc2lnbnMgPSBfbW9kdWxlX2xldmVsX2Fzc2lnbm1lbnRzKCkKICAg"
    "IGFzc2VydCBuYW1lIGluIGFzc2lnbnMsICgKICAgICAgICBmIntuYW1lfSBpcyBleHBl"
    "Y3RlZCB0byBleGlzdCBpbiB1aS9jb2xvcnMucHkgYW5kIGRvZXMgbm90LiAiCiAgICAg"
    "ICAgZiJJZiBpdCB3YXMgZGVsaWJlcmF0ZWx5IHJlbW92ZWQsIHJlbW92ZSBpdCBmcm9t"
    "IERFUklWRURfQ09OU1RBTlRTICIKICAgICAgICBmImluIHRoaXMgdGVzdCB0b28uIikK"
    "ICAgIG5vZGUgPSBhc3NpZ25zW25hbWVdCiAgICBhc3NlcnQgaXNpbnN0YW5jZShub2Rl"
    "LCBhc3QuQ2FsbCksICgKICAgICAgICBmIntuYW1lfSBpcyBkb2N1bWVudGVkIGFzIGRl"
    "cml2ZWQgYnV0IGlzIGFzc2lnbmVkIGEgbGl0ZXJhbCAiCiAgICAgICAgZiIoe2FzdC5k"
    "dW1wKG5vZGUpWzo4MF19KS4gT25jZSBpdCBpcyB3cml0dGVuIGRvd24gaXQgc3RvcHMg"
    "IgogICAgICAgIGYidHJhY2tpbmcgdGhlIGNvbG91ciBpdCBjYW1lIGZyb20sIGFuZCB0"
    "aGUgbmV4dCB0aW1lIHRoYXQgY29sb3VyICIKICAgICAgICBmIm1vdmVzIHRoaXMgb25l"
    "IHNpbGVudGx5IGRvZXMgbm90LiIpCgoKQHB5dGVzdC5tYXJrLnBhcmFtZXRyaXplKCJu"
    "YW1lIiwgc29ydGVkKFJFR0lTVEVSRURfQ09OU1RBTlRTKSkKZGVmIHRlc3RfcmVnaXN0"
    "ZXJlZF9jb25zdGFudF9pc19hX2xpdGVyYWwobmFtZTogc3RyKSAtPiBOb25lOgogICAg"
    "IiIiQSByZWdpc3RlcmVkIGJyYW5kIHZhbHVlIG11c3QgYmUgd3JpdHRlbiBkb3duLCBu"
    "b3QgY29tcHV0ZWQuIiIiCiAgICBhc3NpZ25zID0gX21vZHVsZV9sZXZlbF9hc3NpZ25t"
    "ZW50cygpCiAgICBhc3NlcnQgbmFtZSBpbiBhc3NpZ25zLCBmIntuYW1lfSBtaXNzaW5n"
    "IGZyb20gdWkvY29sb3JzLnB5IgogICAgbm9kZSA9IGFzc2lnbnNbbmFtZV0KICAgIGFz"
    "c2VydCBpc2luc3RhbmNlKG5vZGUsIGFzdC5Db25zdGFudCkgYW5kIGlzaW5zdGFuY2Uo"
    "bm9kZS52YWx1ZSwgc3RyKSwgKAogICAgICAgIGYie25hbWV9IGlzIGEgcmVnaXN0ZXJl"
    "ZCBicmFuZCBjb2xvdXIgYW5kIG11c3QgYmUgYSBsaXRlcmFsLiAiCiAgICAgICAgZiJE"
    "ZXJpdmluZyBpdCB3b3VsZCBtYWtlIHRoZSByZWdpc3RlciBkZXBlbmQgb24gdGhlIGFw"
    "cCBpbnN0ZWFkICIKICAgICAgICBmIm9mIHRoZSBvdGhlciB3YXkgcm91bmQuIikKCgpk"
    "ZWYgdGVzdF9kZWVwX2dvbGRfdHJhY2tzX2l0c19zb3VyY2UoKSAtPiBOb25lOgogICAg"
    "IiIiQ2hhbmdpbmcgQlJBTkRfREFSS19HT0xEIG11c3QgbW92ZSB0aGUgZGVyaXZhdGl2"
    "ZSB3aXRoIGl0LiIiIgogICAgYXNzZXJ0IEMuQlJBTkRfREFSS19HT0xEX0RFRVAgPT0g"
    "Qy5saWdodGVuKEMuQlJBTkRfREFSS19HT0xELCAtMTQpCiAgICBhc3NlcnQgQy5CUkFO"
    "RF9EQVJLX0dPTERfREVFUCAhPSBDLkJSQU5EX0RBUktfR09MRAoKCkBweXRlc3QubWFy"
    "ay5wYXJhbWV0cml6ZSgiY29uc3QscmdiIiwgWwogICAgKCJCUkFORF9HT0xEIiwgIkJS"
    "QU5EX0dPTERfUkdCIiksCiAgICAoIkJSQU5EX0RBUktfR09MRCIsICJCUkFORF9EQVJL"
    "X0dPTERfUkdCIiksCl0pCmRlZiB0ZXN0X3JnYl90dXBsZV9tYXRjaGVzX2l0c19oZXgo"
    "Y29uc3Q6IHN0ciwgcmdiOiBzdHIpIC0+IE5vbmU6CiAgICAiIiJUaGUgUkdCLXR1cGxl"
    "IGJsaW5kIHNwb3QuCgogICAgQSBoYXJkY29kZWQgKDE3NywgMTQ1LCA2OSkgaXMgaW52"
    "aXNpYmxlIHRvIGV2ZXJ5IGhleC1iYXNlZCBzZWFyY2gsIHNvCiAgICBpdCBzdXJ2aXZl"
    "cyBzd2VlcHMgdGhhdCBjYXRjaCBldmVyeSBvdGhlciByZWZlcmVuY2UgdG8gdGhlIGNv"
    "bG91ci4KICAgIERlcml2aW5nIGl0IHJlbW92ZXMgdGhlIGhpZGluZyBwbGFjZTsgdGhp"
    "cyB0ZXN0IGtlZXBzIGl0IHJlbW92ZWQuCiAgICAiIiIKICAgIHIsIGcsIGIgPSBnZXRh"
    "dHRyKEMsIHJnYikKICAgIGFzc2VydCBnZXRhdHRyKEMsIGNvbnN0KS5sb3dlcigpID09"
    "IGYiI3tyOjAyeH17ZzowMnh9e2I6MDJ4fSIKCgpkZWYgdGVzdF9saWdodGVuX3ByZXNl"
    "cnZlc19odWVfYnlfc2hpZnRpbmdfY2hhbm5lbHNfdW5pZm9ybWx5KCkgLT4gTm9uZToK"
    "ICAgIGJhc2UgPSAiIzhjNzMzNyIKICAgIG91dCA9IEMubGlnaHRlbihiYXNlLCAtMTQp"
    "CiAgICBiciwgYmdfLCBiYiA9IEMuX3RvX3JnYihiYXNlKQogICAgb3JyLCBvZywgb2Ig"
    "PSBDLl90b19yZ2Iob3V0KQogICAgYXNzZXJ0IChiciAtIG9yciwgYmdfIC0gb2csIGJi"
    "IC0gb2IpID09ICgxNCwgMTQsIDE0KQoKCmRlZiB0ZXN0X2xpZ2h0ZW5fY2xhbXBzX2lu"
    "c3RlYWRfb2Zfd3JhcHBpbmcoKSAtPiBOb25lOgogICAgYXNzZXJ0IEMubGlnaHRlbigi"
    "I2ZmZmZmZiIsIDQwKSA9PSAiI2ZmZmZmZiIKICAgIGFzc2VydCBDLmxpZ2h0ZW4oIiMw"
    "MDAwMDAiLCAtNDApID09ICIjMDAwMDAwIgoKCiMg4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
    "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQCiMg"
    "UEFJUklORyBBVURJVAojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkAoKIyBQYWlycyB0aGF0IHJl"
    "bmRlciBiZWxvdyB0aGUgZmxvb3Igb24gcHVycG9zZSwgZWFjaCB3aXRoIHRoZSByZWFz"
    "b24uCiMgQm90aCBoYWx2ZXMgb2YgdGhpcyBkaWN0IGFyZSBhc3NlcnRlZCAtLSBzZWUg"
    "dGhlIG1vZHVsZSBkb2NzdHJpbmcuCkFDQ0VQVEVEOiBkaWN0W3R1cGxlW3N0ciwgc3Ry"
    "XSwgc3RyXSA9IHsKICAgICgiIzAwMDAwMCIsICIjMzMzMzMzIik6CiAgICAgICAgIm1h"
    "aW4td2luZG93IGJ1dHRvbiBob3Zlci4gVGhlIG1haW4gd2luZG93IHVzZXMgYSB3aGl0"
    "ZS9uZWFyLWJsYWNrICIKICAgICAgICAiaW52ZXJzZSBzY2hlbWUgaW4gd2hpY2ggdGhl"
    "IHRleHQgc3RheXMgYmxhY2sgd2hpbGUgdGhlIGJhY2tncm91bmQgIgogICAgICAgICJk"
    "YXJrZW5zOyB0aGlzIGlzIHRoZSBhcHAncyBkZWxpYmVyYXRlIGRlc2lnbiwgbm90IGFu"
    "IG92ZXJzaWdodCwgIgogICAgICAgICJhbmQgaXQgaXMgc2VwYXJhdGUgZnJvbSB0aGUg"
    "Z29sZCBkaWFsb2ctYnV0dG9uIHNjaGVtZS4iLAogICAgKCIjMDAwMDAwIiwgIiM0NDQ0"
    "NDQiKToKICAgICAgICAibWFpbi13aW5kb3cgYnV0dG9uIHByZXNzZWQsIHNhbWUgaW52"
    "ZXJzZSBzY2hlbWUuIiwKICAgICgiI2ZmZmZmZiIsICIjZDJiYzkzIik6CiAgICAgICAg"
    "IkJSQU5EX0dPTEQgYXMgYSBsaXN0LWl0ZW0gZmlsbCB3aXRoIHdoaXRlIHRleHQuIEJS"
    "QU5EX0dPTEQgaXMgYSAiCiAgICAgICAgInJlZ2lzdGVyZWQgdmFsdWUgYW5kIGlzIG5v"
    "dCBpbiBzY29wZSBmb3IgdGhlIGRhcmstZ29sZCBhbGlnbm1lbnQuICIKICAgICAgICAi"
    "UmVjb3JkZWQgaGVyZSBzbyBpdCBzdGF5cyB2aXNpYmxlIHJhdGhlciB0aGFuIGZvcmdv"
    "dHRlbi4iLAogICAgKCIjYWFhYWFhIiwgIiNmZmZmZmYiKToKICAgICAgICAiZGlzYWJs"
    "ZWQgY29udHJvbCB0ZXh0LiBXQ0FHIDEuNC4zIGV4ZW1wdHMgZGlzYWJsZWQgY29udHJv"
    "bHMuIiwKICAgICgiIzU1NTU1NSIsICIjMWExYTFhIik6CiAgICAgICAgImRpc2FibGVk"
    "IGNvbnRyb2wgdGV4dCwgZGFyayB0aGVtZS4gU2FtZSBleGVtcHRpb24uIiwKICAgICgi"
    "IzY2NjY2NiIsICIjZTBlMGUwIik6CiAgICAgICAgIk9TLXNpbXVsYXRpb24gY2hyb21l"
    "IGluIGNvbnRleHRfcHJldmlldy5weSwgd2hpY2ggcmVwcm9kdWNlcyAiCiAgICAgICAg"
    "InBsYXRmb3JtIFVJIHNvIHVzZXJzIGNhbiBwcmV2aWV3IGFuIGljb24gaW4gc2l0dS4g"
    "SXQgbXVzdCBtYXRjaCAiCiAgICAgICAgInRoZSBwbGF0Zm9ybSwgbm90IHRoZSBicmFu"
    "ZC4iLAogICAgKCIjODg4ODg4IiwgIiMyYTJhMmEiKToKICAgICAgICAiT1Mtc2ltdWxh"
    "dGlvbiBjaHJvbWUsIGRhcmsuIFNhbWUgcmVhc29uLiIsCn0KCl9IRVggPSByZS5jb21w"
    "aWxlKHIiIyg/OlswLTlhLWZBLUZdezN9fFswLTlhLWZBLUZdezZ9KVxiIikKCiMgVGhl"
    "IFFTUyBsaXZlcyBpbnNpZGUgZi1zdHJpbmdzLCBzbyBpdHMgYnJhY2VzIGFyZSBkb3Vi"
    "bGVkLiBNYXRjaGluZyBzaW5nbGUKIyBicmFjZXMgaGVyZSBmaW5kcyBub3RoaW5nIGF0"
    "IGFsbCAtLSBhbmQgZmluZGluZyBub3RoaW5nIHJlYWRzIGV4YWN0bHkgbGlrZQojIGZp"
    "bmRpbmcgbm8gZGVmZWN0cywgd2hpY2ggaXMgd2h5IHRlc3RfdGhlX2F1ZGl0X2ZpbmRz"
    "X3NvbWV0aGluZ190b19hdWRpdAojIGV4aXN0cyBiZWxvdy4KIwoKZGVmIF9ydWxlcyhz"
    "cmM6IHN0cikgLT4gbGlzdFt0dXBsZVtzdHIsIHN0cl1dOgogICAgIiIiWWllbGQgKHNl"
    "bGVjdG9yLCBib2R5KSBmb3IgZWFjaCBRU1MgcnVsZSBpbiBvbmUgc291cmNlIGZpbGUu"
    "CgogICAgRGVsaWJlcmF0ZWx5IGEgc2NhbiByYXRoZXIgdGhhbiBhIHJlZ2V4LiBUaGUg"
    "b2J2aW91cyBwYXR0ZXJuLAogICAgYGAoW157fV0rPylcXHtcXHsoLio/KVxcfVxcfWBg"
    "LCBiYWNrdHJhY2tzIHF1YWRyYXRpY2FsbHkgb24gZmlsZXMgdGhpcwogICAgc2l6ZSAt"
    "LSBpdCB0b29rIGZvcnR5IHNlY29uZHMgcGVyIHBhc3MuIFRoZSBvYnZpb3VzIGZpeCwg"
    "dGlnaHRlbmluZyB0aGUKICAgIGJvZHkgdG8gYGBbXnt9XSpgYCwgaXMgd3JvbmcgZm9y"
    "IGEgZGlmZmVyZW50IHJlYXNvbjogUVNTIGJvZGllcyBhcmUgZnVsbAogICAgb2YgZi1z"
    "dHJpbmcgcGxhY2Vob2xkZXJzIGxpa2UgYGB7Y1sndGFiX2JnJ119YGAsIHNvIGEgYnJh"
    "Y2UtZnJlZSBib2R5CiAgICBjbGFzcyBzdG9wcyBkZWFkIGF0IHRoZSBmaXJzdCBvbmUg"
    "YW5kIGZpbmRzIGEgZnJhY3Rpb24gb2YgdGhlIHJ1bGVzLgogICAgRmluZGluZyBhIGZy"
    "YWN0aW9uIG9mIHRoZSBydWxlcyByZWFkcyBleGFjdGx5IGxpa2UgZmluZGluZyBubyBk"
    "ZWZlY3RzLAogICAgd2hpY2ggaXMgd2hhdCB0ZXN0X3RoZV9hdWRpdF9maW5kc19zb21l"
    "dGhpbmdfdG9fYXVkaXQgaXMgdGhlcmUgdG8gY2F0Y2guCgogICAgVGhlIHNlbGVjdG9y"
    "IGlzIHRoZSBsYXN0IGxpbmUgb2YgdGV4dCBiZXR3ZWVuIHRoZSBlbmQgb2YgdGhlIHBy"
    "ZXZpb3VzCiAgICBibG9jayBhbmQgdGhlIHN0YXJ0IG9mIHRoaXMgb25lLCB3aGljaCBp"
    "cyB3aGVyZSBRdCdzIHNlbGVjdG9yIHNpdHMuCiAgICAiIiIKICAgIG91dCA9IFtdCiAg"
    "ICBjdXJzb3IgPSAwCiAgICB3aGlsZSBUcnVlOgogICAgICAgIHN0YXJ0ID0gc3JjLmZp"
    "bmQoInt7IiwgY3Vyc29yKQogICAgICAgIGlmIHN0YXJ0ID09IC0xOgogICAgICAgICAg"
    "ICBicmVhawogICAgICAgIGVuZCA9IHNyYy5maW5kKCJ9fSIsIHN0YXJ0ICsgMikKICAg"
    "ICAgICBpZiBlbmQgPT0gLTE6CiAgICAgICAgICAgIGJyZWFrCiAgICAgICAgbGVhZCA9"
    "IHNyY1tjdXJzb3I6c3RhcnRdLnN0cmlwKCkKICAgICAgICBzZWxlY3RvciA9IGxlYWQu"
    "c3BsaXRsaW5lcygpWy0xXS5zdHJpcCgpIGlmIGxlYWQgZWxzZSAiIgogICAgICAgIG91"
    "dC5hcHBlbmQoKHNlbGVjdG9yLCBzcmNbc3RhcnQgKyAyOmVuZF0pKQogICAgICAgIGN1"
    "cnNvciA9IGVuZCArIDIKICAgIHJldHVybiBvdXQKCgpkZWYgX25vcm1hbGlzZShoZXhf"
    "Y29sb3I6IHN0cikgLT4gc3RyOgogICAgaCA9IGhleF9jb2xvci5sc3RyaXAoIiMiKQog"
    "ICAgaWYgbGVuKGgpID09IDM6CiAgICAgICAgaCA9ICIiLmpvaW4oYyAqIDIgZm9yIGMg"
    "aW4gaCkKICAgIHJldHVybiAiIyIgKyBoLmxvd2VyKCkKCgpkZWYgX3Jlc29sdmUodG9r"
    "ZW46IHN0ciwgcGFsZXR0ZTogZGljdFtzdHIsIHN0cl0pIC0+IHN0ciB8IE5vbmU6CiAg"
    "ICAiIiJUdXJuIG9uZSBRU1MgdmFsdWUgaW50byBhIGNvbmNyZXRlIGhleCwgb3IgTm9u"
    "ZSBpZiBpdCBpcyBub3Qgb25lLiIiIgogICAgdG9rZW4gPSB0b2tlbi5zdHJpcCgpLnJz"
    "dHJpcCgiOyIpLnN0cmlwKCkKICAgIGlmIF9IRVguZnVsbG1hdGNoKHRva2VuKToKICAg"
    "ICAgICByZXR1cm4gX25vcm1hbGlzZSh0b2tlbikKICAgICMge2NbJ2tleSddfSAvIHtj"
    "b2xvcnNbJ2tleSddfSAvIHt0aGVtZVsna2V5J119CiAgICBtID0gcmUuZnVsbG1hdGNo"
    "KHIiXHtccypcdytcW1snXCJdKFtcd1wtXSspWydcIl1cXVxzKlx9IiwgdG9rZW4pCiAg"
    "ICBpZiBtOgogICAgICAgIHYgPSBwYWxldHRlLmdldChtLmdyb3VwKDEpKQogICAgICAg"
    "IHJldHVybiBfbm9ybWFsaXNlKHYpIGlmIGlzaW5zdGFuY2Uodiwgc3RyKSBhbmQgX0hF"
    "WC5mdWxsbWF0Y2godikgZWxzZSBOb25lCiAgICAjIGJhcmUge0NPTlNUQU5UfQogICAg"
    "bSA9IHJlLmZ1bGxtYXRjaChyIlx7XHMqKFtBLVpfXVtBLVowLTlfXSopXHMqXH0iLCB0"
    "b2tlbikKICAgIGlmIG06CiAgICAgICAgdiA9IGdldGF0dHIoQywgbS5ncm91cCgxKSwg"
    "Tm9uZSkKICAgICAgICByZXR1cm4gX25vcm1hbGlzZSh2KSBpZiBpc2luc3RhbmNlKHYs"
    "IHN0cikgYW5kIF9IRVguZnVsbG1hdGNoKHYpIGVsc2UgTm9uZQogICAgcmV0dXJuIE5v"
    "bmUKCgpkZWYgX3RyYWNrZWRfcHl0aG9uX2ZpbGVzKCkgLT4gbGlzdFtQYXRoXToKICAg"
    "ICIiIkVudW1lcmF0ZSBmcm9tIGdpdCByYXRoZXIgdGhhbiBmcm9tIGEgbGlzdCB3cml0"
    "dGVuIGRvd24gaGVyZS4KCiAgICBBIGhhcmRjb2RlZCBmaWxlIGxpc3QgZ29lcyBzdGFs"
    "ZSB0aGUgbW9tZW50IGEgbW9kdWxlIGlzIGFkZGVkLCBhbmQgaXQKICAgIGdvZXMgc3Rh"
    "bGUgaW4gdGhlIGRpcmVjdGlvbiB0aGF0IHJlcG9ydHMgY2xlYW4uCiAgICAiIiIKICAg"
    "IHIgPSBzdWJwcm9jZXNzLnJ1bihbImdpdCIsICJscy1maWxlcyIsICIteiIsICIqLnB5"
    "Il0sCiAgICAgICAgICAgICAgICAgICAgICAgY3dkPVBST0pFQ1RfUk9PVCwgY2FwdHVy"
    "ZV9vdXRwdXQ9VHJ1ZSwgdGV4dD1UcnVlKQogICAgaWYgci5yZXR1cm5jb2RlICE9IDA6"
    "ICAgICAgICAgICAgICAgICAgICAgICAjIG5vdCBhIGdpdCBjaGVja291dAogICAgICAg"
    "IHJldHVybiBzb3J0ZWQocCBmb3IgcCBpbiBQUk9KRUNUX1JPT1Qucmdsb2IoIioucHki"
    "KQogICAgICAgICAgICAgICAgICAgICAgaWYgIl9fcHljYWNoZV9fIiBub3QgaW4gcC5w"
    "YXJ0cykKICAgIHJldHVybiBzb3J0ZWQoKFBST0pFQ1RfUk9PVCAvIG4pIGZvciBuIGlu"
    "IHIuc3Rkb3V0LnNwbGl0KCJcMCIpCiAgICAgICAgICAgICAgICAgIGlmIG4gYW5kIChQ"
    "Uk9KRUNUX1JPT1QgLyBuKS5leGlzdHMoKSkKCgpAZnVuY3Rvb2xzLmxydV9jYWNoZSht"
    "YXhzaXplPTEpCmRlZiBfc291cmNlcygpIC0+IHR1cGxlW3R1cGxlW3N0ciwgc3RyXSwg"
    "Li4uXToKICAgICIiIihyZWxhdGl2ZSBwYXRoLCB0ZXh0KSBmb3IgZXZlcnkgdHJhY2tl"
    "ZCBQeXRob24gZmlsZSwgcmVhZCBvbmNlLiIiIgogICAgcmV0dXJuIHR1cGxlKChzdHIo"
    "cC5yZWxhdGl2ZV90byhQUk9KRUNUX1JPT1QpKSwKICAgICAgICAgICAgICAgICAgcC5y"
    "ZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IiwgZXJyb3JzPSJpZ25vcmUiKSkKICAgICAg"
    "ICAgICAgICAgICBmb3IgcCBpbiBfdHJhY2tlZF9weXRob25fZmlsZXMoKSkKCgpkZWYg"
    "YXVkaXRfcGFsZXR0ZShwYWxldHRlOiBkaWN0W3N0ciwgc3RyXSkgLT4gbGlzdFt0dXBs"
    "ZVtzdHIsIHN0ciwgZmxvYXQsIHN0cl1dOgogICAgZmluZGluZ3MgPSBbXQogICAgZm9y"
    "IHJlbCwgc3JjIGluIF9zb3VyY2VzKCk6CiAgICAgICAgZm9yIHNlbGVjdG9yLCBib2R5"
    "IGluIF9ydWxlcyhzcmMpOgogICAgICAgICAgICBmZyA9IGJnID0gTm9uZQogICAgICAg"
    "ICAgICBmb3IgZGVjbCBpbiBib2R5LnNwbGl0KCI7Iik6CiAgICAgICAgICAgICAgICBp"
    "ZiAiOiIgbm90IGluIGRlY2w6CiAgICAgICAgICAgICAgICAgICAgY29udGludWUKICAg"
    "ICAgICAgICAgICAgIHByb3AsIF8sIHZhbHVlID0gZGVjbC5wYXJ0aXRpb24oIjoiKQog"
    "ICAgICAgICAgICAgICAgcHJvcCA9IHByb3Auc3RyaXAoKQogICAgICAgICAgICAgICAg"
    "aWYgcHJvcCA9PSAiY29sb3IiOgogICAgICAgICAgICAgICAgICAgIGZnID0gX3Jlc29s"
    "dmUodmFsdWUsIHBhbGV0dGUpCiAgICAgICAgICAgICAgICBlbGlmIHByb3AgaW4gKCJi"
    "YWNrZ3JvdW5kLWNvbG9yIiwgImJhY2tncm91bmQiKToKICAgICAgICAgICAgICAgICAg"
    "ICBiZyA9IF9yZXNvbHZlKHZhbHVlLCBwYWxldHRlKQogICAgICAgICAgICBpZiBmZyBh"
    "bmQgYmc6CiAgICAgICAgICAgICAgICByYXRpbyA9IGNvbnRyYXN0X3JhdGlvKGZnLCBi"
    "ZykKICAgICAgICAgICAgICAgIGlmIHJhdGlvIDwgVEVYVF9GTE9PUjoKICAgICAgICAg"
    "ICAgICAgICAgICBmaW5kaW5ncy5hcHBlbmQoKGZnLCBiZywgcm91bmQocmF0aW8sIDQp"
    "LAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgZiJ7cmVsfSA6OiB7"
    "c2VsZWN0b3J9IikpCiAgICByZXR1cm4gZmluZGluZ3MKCgpkZWYgdGVzdF90aGVfYXVk"
    "aXRfZmluZHNfc29tZXRoaW5nX3RvX2F1ZGl0KCkgLT4gTm9uZToKICAgICIiIkd1YXJk"
    "IHRoZSBndWFyZC4KCiAgICBJZiB0aGUgUVNTIGZvcm1hdCBjaGFuZ2VzIGFuZCB0aGUg"
    "cnVsZSByZWdleCBzdG9wcyBtYXRjaGluZywgZXZlcnkKICAgIGNvbnRyYXN0IHRlc3Qg"
    "YmVsb3cgcGFzc2VzIHZhY3VvdXNseS4gVGhpcyBhc3NlcnRzIHRoZSB3YWxrZXIgaXMg"
    "c3RpbGwKICAgIHJlYWNoaW5nIHJlYWwgcnVsZXMuCiAgICAiIiIKICAgIHRvdGFsID0g"
    "c3VtKGxlbihfcnVsZXMoc3JjKSkgZm9yIF9yZWwsIHNyYyBpbiBfc291cmNlcygpKQog"
    "ICAgYXNzZXJ0IHRvdGFsID4gMTAwLCAoCiAgICAgICAgZiJ0aGUgUVNTIHdhbGtlciBt"
    "YXRjaGVkIG9ubHkge3RvdGFsfSBydWxlcyBhY3Jvc3MgdGhlIHJlcG9zaXRvcnksICIK"
    "ICAgICAgICBmIndoaWNoIG1lYW5zIGl0IGhhcyBzdG9wcGVkIHBhcnNpbmcgdGhlIHN0"
    "eWxlc2hlZXRzIHJhdGhlciB0aGFuICIKICAgICAgICBmInRoYXQgdGhlIHN0eWxlc2hl"
    "ZXRzIGdvdCBzbWFsbGVyIikKCgpAcHl0ZXN0Lm1hcmsucGFyYW1ldHJpemUoInRoZW1l"
    "X25hbWUiLCBbIkxJR0hUIiwgIkRBUksiXSkKZGVmIHRlc3Rfbm9fdW5hY2NlcHRlZF9j"
    "b250cmFzdF9mYWlsdXJlcyh0aGVtZV9uYW1lOiBzdHIpIC0+IE5vbmU6CiAgICBwYWxl"
    "dHRlID0gKEMuTElHSFRfVEhFTUVfQ09MT1JTIGlmIHRoZW1lX25hbWUgPT0gIkxJR0hU"
    "IgogICAgICAgICAgICAgICBlbHNlIEMuREFSS19USEVNRV9DT0xPUlMpCiAgICBiYWQg"
    "PSBbZiBmb3IgZiBpbiBhdWRpdF9wYWxldHRlKHBhbGV0dGUpIGlmIChmWzBdLCBmWzFd"
    "KSBub3QgaW4gQUNDRVBURURdCiAgICBhc3NlcnQgbm90IGJhZCwgIlxuIi5qb2luKAog"
    "ICAgICAgIGYiICB7cjo+N306MSAge2ZnfSBvbiB7Ymd9ICA8LSB7d2hlcmV9IiBmb3Ig"
    "ZmcsIGJnLCByLCB3aGVyZSBpbiBiYWQpCgoKZGVmIHRlc3RfZXZlcnlfZXhlbXB0aW9u"
    "X3N0aWxsX2FwcGxpZXMoKSAtPiBOb25lOgogICAgIiIiVGhlIGhhbGYgdGhhdCBtYXR0"
    "ZXJzLgoKICAgIEFuIGV4ZW1wdGlvbiBmb3IgYSBwYWlyaW5nIHRoYXQgbm8gbG9uZ2Vy"
    "IGV4aXN0cyBpcyBhbiBleGVtcHRpb24gdGhhdAogICAgd2lsbCBzaWxlbnRseSBjb3Zl"
    "ciBhIGZ1dHVyZSBkZWZlY3QuIFJlbW92aW5nIGRlYWQgZW50cmllcyBrZWVwcyB0aGUK"
    "ICAgIGxpc3QgaG9uZXN0LgogICAgIiIiCiAgICBzZWVuID0gc2V0KCkKICAgIGZvciBw"
    "YWxldHRlIGluIChDLkxJR0hUX1RIRU1FX0NPTE9SUywgQy5EQVJLX1RIRU1FX0NPTE9S"
    "Uyk6CiAgICAgICAgZm9yIGZnLCBiZywgX3IsIF93IGluIGF1ZGl0X3BhbGV0dGUocGFs"
    "ZXR0ZSk6CiAgICAgICAgICAgIHNlZW4uYWRkKChmZywgYmcpKQogICAgZGVhZCA9IHNv"
    "cnRlZChrIGZvciBrIGluIEFDQ0VQVEVEIGlmIGsgbm90IGluIHNlZW4pCiAgICBhc3Nl"
    "cnQgbm90IGRlYWQsICgKICAgICAgICAidGhlc2UgZXhlbXB0aW9ucyBubyBsb25nZXIg"
    "bWF0Y2ggYW55dGhpbmcgdGhlIGFwcCByZW5kZXJzIGFuZCAiCiAgICAgICAgZiJzaG91"
    "bGQgYmUgZGVsZXRlZDoge2RlYWR9IikKCgojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkAojIFRI"
    "RSBUV08gR09MRCBST0xFUwojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkAojCiMgTGlnaHQgbW9k"
    "ZSB1c2VzIGV4YWN0bHkgdHdvIGdvbGRzLCBiZWNhdXNlIG9uZSBjYW5ub3QgZG8gYm90"
    "aCBqb2JzOiBhCiMgZ29sZCBsaWdodCBlbm91Z2ggdG8gY2Fycnkgd2hpdGUgdGV4dCBh"
    "dCA0LjU6MSBpcyB0b28gbGlnaHQgdG8gQkUgdGV4dAojIG9uIGFueXRoaW5nIGJ1dCBw"
    "dXJlIHdoaXRlLiBUaGUgbHVtaW5hbmNlIGJhbmRzIGRvIG5vdCBvdmVybGFwLgoKTElH"
    "SFRfU1VSRkFDRVMgPSBbIiNmZmZmZmYiLCAiI2ZhZmFmYSIsICIjZjVmNWY1IiwgIiNm"
    "MGYwZjAiLCAiI2VlZWVlZSJdCgoKZGVmIHRlc3RfZmlsbF9nb2xkX2NhcnJpZXNfd2hp"
    "dGVfdGV4dCgpIC0+IE5vbmU6CiAgICBhc3NlcnQgY29udHJhc3RfcmF0aW8oIiNmZmZm"
    "ZmYiLCBDLkJSQU5EX0RBUktfR09MRCkgPj0gVEVYVF9GTE9PUgoKCmRlZiB0ZXN0X3Rl"
    "eHRfZ29sZF9jbGVhcnNfZXZlcnlfbGlnaHRfc3VyZmFjZSgpIC0+IE5vbmU6CiAgICBm"
    "YWlsdXJlcyA9IFsocywgcm91bmQoY29udHJhc3RfcmF0aW8oQy5CUkFORF9EQVJLX0dP"
    "TERfREVFUCwgcyksIDQpKQogICAgICAgICAgICAgICAgZm9yIHMgaW4gTElHSFRfU1VS"
    "RkFDRVMKICAgICAgICAgICAgICAgIGlmIGNvbnRyYXN0X3JhdGlvKEMuQlJBTkRfREFS"
    "S19HT0xEX0RFRVAsIHMpIDwgVEVYVF9GTE9PUl0KICAgIGFzc2VydCBub3QgZmFpbHVy"
    "ZXMsICgKICAgICAgICBmInRoZSB0ZXh0IGdvbGQgbm8gbG9uZ2VyIGNsZWFycyBldmVy"
    "eSBsaWdodCBzdXJmYWNlOiB7ZmFpbHVyZXN9IikKCgpAcHl0ZXN0Lm1hcmsucGFyYW1l"
    "dHJpemUoImtleSIsIFsKICAgICJ0ZXh0X2FjY2VudCIsICJidXR0b25faG92ZXJfdGV4"
    "dCIsICJhY2NlbnRfYnV0dG9uX3RleHQiLApdKQpkZWYgdGVzdF9nb2xkX3RleHRfa2V5"
    "c191c2VfdGhlX3RleHRfZ29sZChrZXk6IHN0cikgLT4gTm9uZToKICAgIGFzc2VydCBD"
    "LkxJR0hUX1RIRU1FX0NPTE9SU1trZXldID09IEMuQlJBTkRfREFSS19HT0xEX0RFRVAK"
    "CgpAcHl0ZXN0Lm1hcmsucGFyYW1ldHJpemUoImtleSIsIFsKICAgICJzZWxlY3RlZF9i"
    "ZyIsICJidXR0b25fcHJlc3NlZF9iZyIsICJhY2NlbnRfYnV0dG9uX3ByZXNzZWRfYmci"
    "LAogICAgImNoZWNrYm94X2NoZWNrZWRfYmciLCAibGlzdF9zZWxlY3RlZF9iZyIsCl0p"
    "CmRlZiB0ZXN0X2dvbGRfZmlsbF9rZXlzX3VzZV90aGVfZmlsbF9nb2xkKGtleTogc3Ry"
    "KSAtPiBOb25lOgogICAgIiIiRmlsbHMgbXVzdCBub3QgdGFrZSB0aGUgdGV4dCBnb2xk"
    "OiBpdCBkb2VzIG5vdCBjYXJyeSB3aGl0ZSB0ZXh0LiIiIgogICAgYXNzZXJ0IEMuTElH"
    "SFRfVEhFTUVfQ09MT1JTW2tleV0gPT0gQy5CUkFORF9EQVJLX0dPTEQKCgpkZWYgdGVz"
    "dF90YWJfaG92ZXJfZ3JvdW5kX2lzX2xpZ2h0X2Vub3VnaF9mb3JfZ29sZF90ZXh0KCkg"
    "LT4gTm9uZToKICAgICIiIlRoZSBob3ZlciB0YWIgcmVhZHMgYXMgaG92ZXIgYmVjYXVz"
    "ZSB0aGUgZ3JvdW5kIExJR0hURU5TIHRvd2FyZCB0aGUKICAgIHNlbGVjdGVkIHRhYidz"
    "IHdoaXRlLCBhbmQgdGhlIGdvbGQgdGV4dCBzdGF5cyBsZWdpYmxlIG9uIGl0LiIiIgog"
    "ICAgZ3JvdW5kID0gQy5MSUdIVF9USEVNRV9DT0xPUlNbInRhYl9ob3Zlcl9iZyJdCiAg"
    "ICByZXN0ID0gQy5MSUdIVF9USEVNRV9DT0xPUlNbInRhYl9iZyJdCiAgICBhc3NlcnQg"
    "cmVsYXRpdmVfbHVtaW5hbmNlKGdyb3VuZCkgPiByZWxhdGl2ZV9sdW1pbmFuY2UocmVz"
    "dCkKICAgIGFzc2VydCBjb250cmFzdF9yYXRpbyhDLkxJR0hUX1RIRU1FX0NPTE9SU1si"
    "dGV4dF9hY2NlbnQiXSwKICAgICAgICAgICAgICAgICAgICAgICAgICBncm91bmQpID49"
    "IFRFWFRfRkxPT1IKCgpkZWYgdGVzdF90YWJfaW5kaWNhdG9yX2NsZWFyc190aGVfY29t"
    "cG9uZW50X2Zsb29yKCkgLT4gTm9uZToKICAgIGFzc2VydCBjb250cmFzdF9yYXRpbyhD"
    "LkxJR0hUX1RIRU1FX0NPTE9SU1sidGFiX2luZGljYXRvciJdLAogICAgICAgICAgICAg"
    "ICAgICAgICAgICAgIEMuTElHSFRfVEhFTUVfQ09MT1JTWyJ0YWJfc2VsZWN0ZWRfYmci"
    "XQogICAgICAgICAgICAgICAgICAgICAgICAgICkgPj0gQ09NUE9ORU5UX0ZMT09SCgoK"
    "IyDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi"
    "lZDilZDilZDilZDilZDilZDilZAKIyBTQ0hFTUUgU0VQQVJBVElPTgojIOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkAojCiMgVGhlIGFwcCBydW5zIHR3byBidXR0b24gc2NoZW1lcyBzaWRl"
    "IGJ5IHNpZGUuIENvbmZsYXRpbmcgdGhlbSBpcyB0aGUKIyBlYXNpZXN0IHdheSB0byAi"
    "Zml4IiBvbmUgYnkgYnJlYWtpbmcgdGhlIG90aGVyLgoKQHB5dGVzdC5tYXJrLnBhcmFt"
    "ZXRyaXplKCJwYWxldHRlX25hbWUiLCBbIkxJR0hUIiwgIkRBUksiXSkKZGVmIHRlc3Rf"
    "bWFpbl9idXR0b25fc2NoZW1lX2hvbGRzX25vX2dvbGQocGFsZXR0ZV9uYW1lOiBzdHIp"
    "IC0+IE5vbmU6CiAgICAiIiJNYWluLXdpbmRvdyBidXR0b25zIGFyZSB0aGUgd2hpdGUv"
    "bmVhci1ibGFjayBpbnZlcnNlIHN5c3RlbS4gTm8KICAgIGJyYW5kIGdvbGQgYmVsb25n"
    "cyBhbnl3aGVyZSBpbiB0aGVtLiIiIgogICAgcGFsZXR0ZSA9IChDLkxJR0hUX1RIRU1F"
    "X0NPTE9SUyBpZiBwYWxldHRlX25hbWUgPT0gIkxJR0hUIgogICAgICAgICAgICAgICBl"
    "bHNlIEMuREFSS19USEVNRV9DT0xPUlMpCiAgICBnb2xkcyA9IHtDLkJSQU5EX0dPTEQu"
    "bG93ZXIoKSwgQy5CUkFORF9EQVJLX0dPTEQubG93ZXIoKSwKICAgICAgICAgICAgIEMu"
    "QlJBTkRfREFSS19HT0xEX0RFRVAubG93ZXIoKX0KICAgIG9mZmVuZGVycyA9IHtrOiB2"
    "IGZvciBrLCB2IGluIHBhbGV0dGUuaXRlbXMoKQogICAgICAgICAgICAgICAgIGlmIGsu"
    "c3RhcnRzd2l0aCgibWFpbl9idG5fIikgYW5kIHYubG93ZXIoKSBpbiBnb2xkc30KICAg"
    "IGFzc2VydCBub3Qgb2ZmZW5kZXJzLCAoCiAgICAgICAgZiJnb2xkIGxlYWtlZCBpbnRv"
    "IHRoZSBtYWluLXdpbmRvdyBidXR0b24gc2NoZW1lOiB7b2ZmZW5kZXJzfSIpCgoKZGVm"
    "IHRlc3RfcmV0aXJlZF9hcHBfZ29sZF9pc19nb25lKCkgLT4gTm9uZToKICAgICIiIiNi"
    "MTkxNDUgd2FzIGFuIGFwcC1sb2NhbCBhcHByb3hpbWF0aW9uIG9mIHRoZSBicmFuZCBk"
    "YXJrIGdvbGQuIEl0CiAgICBjYXJyaWVkIHdoaXRlIHRleHQgYXQgMi45OTc2OjEuIE5v"
    "dGhpbmcgc2hvdWxkIHJlaW50cm9kdWNlIGl0LiIiIgogICAgZm9yIHBhbGV0dGUgaW4g"
    "KEMuTElHSFRfVEhFTUVfQ09MT1JTLCBDLkRBUktfVEhFTUVfQ09MT1JTLAogICAgICAg"
    "ICAgICAgICAgICAgIEMuSU1BR0VfTU9ERV9DT0xPUlMpOgogICAgICAgIGFzc2VydCBu"
    "b3QgW2sgZm9yIGssIHYgaW4gcGFsZXR0ZS5pdGVtcygpCiAgICAgICAgICAgICAgICAg"
    "ICAgaWYgaXNpbnN0YW5jZSh2LCBzdHIpIGFuZCB2Lmxvd2VyKCkgPT0gIiNiMTkxNDUi"
    "XQo="
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
                f"       Fix (same list this repo's CI installs):\n"
                f"         sudo apt-get update && sudo apt-get install -y "
                f"--no-install-recommends \\\n"
                f"           {QT_APT_PACKAGES}")
    return None


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
    for path in tracked(".py", ".md", ".json"):
        for i, line in enumerate(path.read_text(encoding="utf-8",
                                                errors="ignore").splitlines(), 1):
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


def run_suite() -> bool:
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    say("running the full test suite ...")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q"],
                       cwd=REPO, env=env, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-15:]
    for line in tail:
        say(f"    {line}")
    return r.returncode == 0


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
    ap.add_argument("--skip-tests", action="store_true",
                    help="skip the full pytest run at the end")
    args = ap.parse_args()

    if args.snapshots_only:
        check_dependencies()
        src = COLORS.read_text(encoding="utf-8")
        if OLD_SYM in src or NEW_SYM not in src:
            die("--snapshots-only is for finishing a run that already "
                "applied steps 1-7, and this repository has not had them "
                "applied. Run the script without flags instead.")
        say("resuming at step 8 -- steps 1-7 are already in place", OK)
        step_snapshots()

    if not (args.verify_only or args.snapshots_only):
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
        ok = run_suite() and ok
    say("\nDONE -- all checks passed" if ok else "\nDONE -- with failures above",
        OK if ok else FAIL)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
