import os, unittest
from unittest.mock import patch
from src.execution.mt5_bridge_factory import bridge_factory_from_env
from src.execution.mt5_cloud_metaapi import MetaApiCloudBridge
from src.execution.mt5_session_bridge import RealMetaTrader5Bridge

class BridgeFactory(unittest.TestCase):
    def test_default_is_cloud_no_windows(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertIs(bridge_factory_from_env(),MetaApiCloudBridge)
    def test_cloud_explicit(self):
        with patch.dict(os.environ,{"CWS_MT5_BRIDGE_MODE":"METAAPI_CLOUD"},clear=True):
            self.assertIs(bridge_factory_from_env(),MetaApiCloudBridge)
    def test_local_terminal_is_optional_legacy(self):
        with patch.dict(os.environ,{"CWS_MT5_BRIDGE_MODE":"LOCAL_TERMINAL"},clear=True):
            self.assertIs(bridge_factory_from_env(),RealMetaTrader5Bridge)
    def test_unknown_mode_fails_closed(self):
        with patch.dict(os.environ,{"CWS_MT5_BRIDGE_MODE":"MAGIC"},clear=True):
            with self.assertRaises(ValueError): bridge_factory_from_env()
