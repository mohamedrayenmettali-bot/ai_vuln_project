from __future__ import annotations

from app.config import settings as _settings

EPSS_BATCH_MAX_CVES = _settings.EPSS_BATCH_MAX_CVES
PREDICT_BATCH_MAX_FINDINGS = _settings.PREDICT_BATCH_MAX_FINDINGS
PROCESS_TIME_HEADER = _settings.PROCESS_TIME_HEADER
REQUEST_ID_HEADER = _settings.REQUEST_ID_HEADER

settings = _settings
