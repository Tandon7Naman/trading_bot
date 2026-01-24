import json
import logging
from datetime import datetime

import redis

from config import TITAN_CONFIG

logger = logging.getLogger("TitanPublisher")

class RedisPublisher:
    # All news/sentiment/depository/tando logic removed.
