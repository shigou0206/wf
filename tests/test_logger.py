# tests/test_logger.py

import pytest
from engine.logger import Logger

def test_logger_output(caplog):
    caplog.set_level("DEBUG")
    Logger.debug("Test debug message", extra={"test_key": "test_value"})
    Logger.info("Test info message")
    Logger.warning("Test warning message")
    Logger.error("Test error message")
    Logger.critical("Test critical message")
    
    # 检查日志中是否包含部分测试字符串
    assert "Test debug message" in caplog.text
    assert "Test info message" in caplog.text
    assert "Test warning message" in caplog.text
    assert "Test error message" in caplog.text
    assert "Test critical message" in caplog.text