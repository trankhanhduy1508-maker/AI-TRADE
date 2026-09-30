"""CWS MT5 session bridge selection.

Cloud MetaApi is the default production login path. A local MetaTrader5 terminal
is legacy/optional and is never required by the Android APK.
"""
from __future__ import annotations
import os
from src.execution.mt5_cloud_metaapi import MetaApiCloudBridge
from src.execution.mt5_session_bridge import Mt5SessionService, RealMetaTrader5Bridge

def bridge_factory_from_env():
    mode=os.environ.get("CWS_MT5_BRIDGE_MODE","METAAPI_CLOUD").strip().upper()
    if mode=="METAAPI_CLOUD":
        return MetaApiCloudBridge
    if mode=="LOCAL_TERMINAL":
        return RealMetaTrader5Bridge
    raise ValueError("unsupported CWS_MT5_BRIDGE_MODE")

def build_mt5_session_service(**kwargs):
    return Mt5SessionService(bridge_factory_from_env(), **kwargs)
