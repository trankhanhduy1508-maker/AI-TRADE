"""Single normal-page HistData free-download feasibility check (read-only).

No hidden-endpoint guessing, captcha bypass, paid FTP, login, raw archive
publication, trading/broker API, or evaluation of strategy returns.
Only follows a direct same-origin public .zip anchor observed in the page.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import time
import zipfile
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from src.data_loader.histdata_m1_h4 import derive_complete_h4, MAX_CSV_BYTES

PUBLIC_PAGE=(
    "https://www.histdata.com/download-free-forex-historical-data/"
    "?/ascii/1-minute-bar-quotes/eurusd/2026/8"
)
MAX_HTML=600_000
MAX_ZIP=16_000_000


class PublicLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.forms=[]
        self._anchor=None
        self._form=None

    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=="a":
            self._anchor={"href":a.get("href",""),"text":""}
        if tag=="form":
            self._form={"method":a.get("method","GET").upper(),
                        "action":a.get("action",""),"inputs":[],"text":""}
            self.forms.append(self._form)
        if tag in ("input","button") and self._form is not None:
            self._form["inputs"].append({
                "type":a.get("type","submit" if tag=="button" else "text"),
                "name":a.get("name",""),
                "value_is_archive":("HISTDATA_COM_ASCII_EURUSD_M1_202608.zip" in
                                    a.get("value","")),
            })

    def handle_data(self, data):
        if self._anchor is not None:
            self._anchor["text"]+=data
        if self._form is not None:
            self._form["text"]+=data

    def handle_endtag(self, tag):
        if tag=="a" and self._anchor is not None:
            self.links.append(self._anchor)
            self._anchor=None
        if tag=="form":
            self._form=None


def _read(url: str, limit: int) -> bytes:
    req=Request(url,method="GET",headers={
        "User-Agent":"CWS-AutoTrade-research-source-probe/1.0",
        "Accept":"text/html,application/zip,application/octet-stream"})
    with urlopen(req,timeout=16) as response:
        final=urlsplit(response.geturl())
        if final.scheme!="https" or final.hostname not in (
                "www.histdata.com","histdata.com"):
            raise ValueError("EXTERNAL_DOWNLOAD_REDIRECT_NOT_APPROVED")
        data=response.read(limit+1)
        if not data or len(data)>limit:
            raise ValueError("RESPONSE_EMPTY_OR_OVERSIZE")
        return data


def inspect() -> dict:
    report={"source_page":PUBLIC_PAGE,"symbol":"EURUSD",
            "source_month":"202608",
            "purpose":"SOURCE_FEASIBILITY_ONLY_NO_BACKTEST",
            "status":"PAGE_UNAVAILABLE","raw_prices_publicly_stored":False,
            "account_or_broker_orders":0,
            "download_attempts":0,"actual_derived_h4_count":None,
            "holdout_opened":False}
    try:
        page=_read(PUBLIC_PAGE,MAX_HTML)
        parser=PublicLinkParser()
        parser.feed(page.decode("utf-8"))
        report["html_sha256"]=hashlib.sha256(page).hexdigest()
        report["public_zip_filename_advertised"]=(
            "HISTDATA_COM_ASCII_EURUSD_M1_202608.zip" in
            page.decode("utf-8",errors="replace"))
        report["form_methods"]=[x["method"] for x in parser.forms]
        report["form_schema"]=[{
            "method":x["method"],
            "action_path":urlsplit(urljoin(PUBLIC_PAGE,x["action"])).path,
            "inputs":x["inputs"],
            "text_is_archive":("HISTDATA_COM_ASCII_EURUSD_M1_202608.zip"
                               in x["text"])
        } for x in parser.forms]
        eligible=[]
        for link in parser.links:
            href=link["href"]
            label=link["text"].strip()
            if not href or not (".zip" in href.lower() or
                                ".zip" in label.lower()):
                continue
            absolute=urljoin(PUBLIC_PAGE,href)
            p=urlsplit(absolute)
            if (p.scheme=="https" and p.hostname in
                ("www.histdata.com","histdata.com")):
                eligible.append(absolute)
        report["direct_download_links_seen"]=len(eligible)
        if not eligible:
            report["status"]="FREE_DOWNLOAD_PAGE_REQUIRES_INTERACTIVE_STEP"
            return report
        # Observe and follow only ONE normal public link directly in HTML.
        url=eligible[0]
        if re.search(r"(ftp|sftp|subscription|pay|checkout)",url,re.I):
            report["status"]="DIRECT_LINK_REQUIRES_PAID_OR_SPECIAL_ACCESS"
            return report
        report["download_attempts"]=1
        rawzip=_read(url,MAX_ZIP)
        if not zipfile.is_zipfile(io.BytesIO(rawzip)):
            report["status"]="PUBLIC_LINK_NOT_A_ZIP"
            return report
        with zipfile.ZipFile(io.BytesIO(rawzip)) as archive:
            entries=[f for f in archive.infolist() if not f.is_dir()]
            matches=[f for f in entries if re.fullmatch(
                r"(?:DAT_ASCII|HISTDATA_COM_ASCII)_EURUSD_M1_202608\.csv",
                f.filename,re.I)]
            if len(matches)!=1 or len(entries)!=1:
                report["status"]="ZIP_ENTRY_FORMAT_UNVERIFIED"
                return report
            if matches[0].file_size>MAX_CSV_BYTES:
                report["status"]="ZIP_UNCOMPRESSED_TOO_LARGE"
                return report
            rawcsv=archive.read(matches[0])
            if len(rawcsv)>MAX_CSV_BYTES:
                report["status"]="CSV_EXCEEDS_LIMIT"
                return report
        derived=derive_complete_h4(rawcsv,symbol="EURUSD",
                                   received_at_utc=int(time.time()))
        report.update({
            "status":"REAL_FILE_DERIVED_H4_INTEGRITY_ONLY",
            "zip_sha256":hashlib.sha256(rawzip).hexdigest(),
            "csv_sha256":hashlib.sha256(rawcsv).hexdigest(),
            "m1_count":derived["m1_observations"],
            "actual_derived_h4_count":derived["h4_emitted"],
            "h4_rejected":derived["h4_blocks_rejected"],
            "source_native_h4":False,"bid_only":True,
            "data_license_and_long_term_retention":"NOT_AUDITED",
            "execution_fees":"UNAVAILABLE",
            "raw_prices_publicly_stored":False,
            "independent_forward_trades":0,
            "raw_source_bytes_persisted":False,
        })
    except Exception as exc:
        report["status"]="FREE_DOWNLOAD_INSPECTION_FAILED"
        report["failure_class"]=type(exc).__name__
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--probe",action="store_true")
    a=p.parse_args()
    if not a.probe:
        p.error("--probe required")
    result=inspect()
    print("HISTDATA_SOURCE_PROBE_JSON "+json.dumps(
        result,sort_keys=True,separators=(",",":")),flush=True)
    return 0  # status is in report; never fake provider-data PASS

if __name__=="__main__":
    raise SystemExit(main())
