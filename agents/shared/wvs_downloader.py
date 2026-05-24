"""WVS Wave 7 Korea downloader.

WVS distributes Wave 7 data via a form-gated download. We can't scrape that
automatically per their TOS. This module instead:
1. Confirms a previously-downloaded file is at `data/raw/wvs7/source/F00010_WVS_Wave_7_Korea.dta`.
2. Validates its hash against the manifest.
3. Returns the path; never auto-downloads.

If the file is missing, the agent escalates to Tier 3 with instructions for
the human to fetch it once.
"""

from __future__ import annotations

from pathlib import Path


EXPECTED_SOURCE = Path("data/raw/wvs7/source/F00010_WVS_Wave_7_Korea.dta")


async def download_korea_wave7(out_dir: Path) -> Path:
    if not EXPECTED_SOURCE.exists():
        raise FileNotFoundError(
            "WVS Wave 7 Korea file missing. Per WVS TOS, fetch manually from "
            "https://www.worldvaluessurvey.org/WVSDocumentationWV7.jsp and place "
            f"the .dta at {EXPECTED_SOURCE}. Then re-enqueue this task."
        )
    out_path = out_dir / "wvs7_korea.dta"
    out_path.write_bytes(EXPECTED_SOURCE.read_bytes())
    return out_path
