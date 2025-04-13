from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import *
import requests
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, ClassVar, Dict
from notion_client import Client
import os

def truncate_at_sentence(text: str, n: int) -> str:
    """
    Truncates the input text to a maximum of `n` characters,
    ending at the last full stop (.) before the limit.
    Returns an empty string if no full stop is found within range.
    """
    if len(text) <= n:
        return text.strip()

    # Slice up to n characters and find the last full stop
    cutoff = text[:n].rfind(".")

    if cutoff == -1:
        return ""  # Or fallback to first n chars: return text[:n].strip()

    return text[:cutoff + 1].strip()