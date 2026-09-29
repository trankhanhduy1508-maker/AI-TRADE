"""One-shot normal free HistData download via its published page/form.

No hidden-endpoint guessing, captcha bypass, paid FTP, login, raw archive
publication, trading/broker API, or evaluation of strategy returns.
Uses one public ZIP anchor or the page's own exactly identified /get.php
form with original hidden fields and cookie, never a payment form.
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
from http.cookiejar import CookieJar
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import (
    Request, urlopen, HTTPCookieProcessor, build_opener,
)

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
                "value":a.get("value",""),
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


def _read(url: str, limit: int, *, opener=None) -> bytes:
    req=Request(url,method="GET",headers={
        "User-Agent":"CWS-AutoTrade-research-source-probe/1.0",
        "Accept":"text/html,application/zip,application/octet-stream"})
    with (opener.open if opener else urlopen)(req,timeout=16) as response:
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
        opener=build_opener(HTTPCookieProcessor(CookieJar()))
        page=_read(PUBLIC_PAGE,MAX_HTML,opener=opener)
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
            "inputs":[{k:i[k] for k in ("type","name","value_is_archive")}
                      for i in x["inputs"]],
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
        if eligible:
            # Follow one ordinary same-origin public ZIP anchor when present.
            url=eligible[0]
            if re.search(r"(ftp|sftp|subscription|pay|checkout)",url,re.I):
                report["status"]="DIRECT_LINK_REQUIRES_PAID_OR_SPECIAL_ACCESS"
                return report
            report["download_attempts"]=1
            rawzip=_read(url,MAX_ZIP,opener=opener)
        else:
            # Page inspection identified exactly one PUBLIC free-download
            # form POST /get.php. This is its normal browser submission,
            # using exactly the current page's own hidden fields and cookie.
            # Never submit /getStatus.php, PayPal or any unknown action.
            choices=[]
            for item in parser.forms:
                u=urlsplit(urljoin(PUBLIC_PAGE,item["action"]))
                if (item["method"]=="POST" and u.scheme=="https"
                    and u.hostname=="www.histdata.com"
                    and u.path=="/get.php" and not u.query
                    and not u.fragment):
                    choices.append(item)
            expected={"tk","date","datemonth","platform","timeframe","fxpair"}
            if not report["public_zip_filename_advertised"] or len(choices)!=1:
                report["status"]="FREE_DOWNLOAD_FORM_NOT_UNAMBIGUOUS"
                return report
            inputs=choices[0]["inputs"]
            if (len(inputs)!=6 or {i["name"] for i in inputs}!=expected
                or any(i["type"]!="hidden" or not i["value"]
                       for i in inputs)):
                report["status"]="FREE_DOWNLOAD_FORM_REQUIRES_INTERACTION"
                return report
            fields={i["name"]:i["value"] for i in inputs}
            report["public_form_selection"]={
                k:fields[k] for k in ("date","datemonth",
                                    "platform","timeframe","fxpair")}
            if fields["fxpair"].upper()!="EURUSD":
                report["status"]="FORM_SELECTED_WRONG_SOURCE_MARKET"
                return report
            target="https://www.histdata.com/get.php"
            req=Request(target,data=urlencode(fields).encode("utf-8"),
                        method="POST",headers={
                            "User-Agent":"CWS-AutoTrade-research-source-probe/1.0",
                            "Referer":PUBLIC_PAGE,
                            "Content-Type":"application/x-www-form-urlencoded",
                            "Accept":"application/zip,application/octet-stream"})
            report["download_attempts"]=1
            with opener.open(req,timeout=20) as response:
                final=urlsplit(response.geturl())
                if (final.scheme!="https" or final.hostname not in
                    ("www.histdata.com","histdata.com")):
                    raise ValueError("EXTERNAL_FORM_REDIRECT_NOT_APPROVED")
                rawzip=response.read(MAX_ZIP+1)
                if not rawzip or len(rawzip)>MAX_ZIP:
                    raise ValueError("FREE_FORM_RESPONSE_INVALID_SIZE")
            report["normal_public_form_used"]=True
        if not zipfile.is_zipfile(io.BytesIO(rawzip)):
            report["status"]="PUBLIC_LINK_NOT_A_ZIP"
            return report
        report["zip_sha256"]=hashlib.sha256(rawzip).hexdigest()
        with zipfile.ZipFile(io.BytesIO(rawzip)) as archive:
            report["zip_entry_metadata"]=[{
                "filename":f.filename[:180],
                "uncompressed_size":f.file_size,
                "is_directory":f.is_dir()
            } for f in archive.infolist()[:20]]
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
