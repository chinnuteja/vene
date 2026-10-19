"""Allowlisted transport categories only. Never forward native SDK messages/SDP/tokens."""
import logging
import re


class SafeTransport(logging.Handler):
    def emit(self,record):
        message=record.getMessage().lower()
        category=next((needle for needle in ['wait_pc_connection','unauthorized','connection refused',
            'ice connection state','iceconnectionstate','failed to connect','signal connection',
            'connection timeout','connecting to'] if needle in message),None)
        if category:
            print('Native transport category: '+category,flush=True)


def install():
    logger=logging.getLogger('livekit')
    logger.handlers=[SafeTransport()]
    logger.propagate=False
    logger.setLevel(logging.INFO)
