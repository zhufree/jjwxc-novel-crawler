# -*- coding: UTF-8 -*-
"""
Clean tool functions for LLM / AI agent usage.

Each function is stateless, side-effect-free (except file I/O for download),
and accepts a single Pydantic model as input so agents can use JSON schema
validation automatically.
"""

import os
import re
import sys
import tempfile
from typing import Any, List

import yaml
from pydantic import BaseModel, Field

# allow importing sibling modules whether running from project root or tools/
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import api
import chapter as chapter_mod
from downloader import NovelDownloader
from models import DownloadConfig


# ─────────────────────────────────────────────
# Input models
# ─────────────────────────────────────────────

class NovelUrl(BaseModel):
    url: str = Field(
        ...,
        description="Novel page URL, e.g. https://www.jjwxc.net/onebook.php?novelid=9091462",
    )


class ListChaptersInput(BaseModel):
    url: str = Field(
        ...,
        description="Novel page URL containing novelid parameter.",
    )
    state: str = Field(
        "",
        description="Chinese character conversion: '' = none, 's' = traditional→simplified, 't' = simplified→traditional.",
    )


class DownloadInput(BaseModel):
    url: str = Field(
        ...,
        description="Novel page URL containing novelid parameter.",
    )
    token: str = Field(
        "",
        description="Jjwxc App user token. Required for paid (locked) chapters.",
    )
    format_type: str = Field(
        "txt",
        description="Output format: 'txt', 'epub2', or 'epub3'.",
    )
    output_dir: str = Field(
        "",
        description=(
            "Directory to save output files. "
            "Defaults to a temp folder (tempfile.gettempdir()/jjwxc_downloads). "
            "In production, always set this explicitly."
        ),
    )
    state: str = Field(
        "",
        description="Chinese character conversion: '' = none, 's' = traditional→simplified, 't' = simplified→traditional.",
    )
    thread_num: int = Field(
        100,
        description="Number of concurrent download threads. Recommended: 50–200.",
    )
    chapter_start: int = Field(
        0,
        description="First chapter to download (1-indexed). 0 means start from chapter 1.",
    )
    chapter_end: int = Field(
        0,
        description="Last chapter to download (inclusive). 0 means download to the last chapter.",
    )
    save_per_chapter: bool = Field(
        False,
        description="TXT only. True = save each chapter as a separate file; False = merge into one file.",
    )
    remove_blank_lines: bool = Field(
        False,
        description="TXT only. Remove blank lines between paragraphs.",
    )
    show_number: bool = Field(
        True,
        description="Include chapter ID number in the chapter heading.",
    )
    show_title: bool = Field(
        True,
        description="Include chapter title text in the chapter heading.",
    )
    show_summary: bool = Field(
        True,
        description="Include chapter summary in the chapter heading.",
    )
    show_chinfo: bool = Field(
        False,
        description="Prepend word count and update date at the start of each chapter.",
    )
    del_thanks: bool = Field(
        False,
        description="Strip boilerplate 'thank you for the nutrient solution / landmine' lines from author's notes.",
    )
    add_cover: bool = Field(
        True,
        description="EPUB only. Download and embed the cover image.",
    )
    html_vol: bool = Field(
        False,
        description="EPUB2 only. Render volume titles as standalone HTML pages.",
    )
    special_intro: bool = Field(
        False,
        description="Use the web-page version of the novel synopsis (preserves original HTML layout). Default uses plain-text API synopsis.",
    )
    custom_title: str = Field(
        "",
        description="Custom chapter heading template. Variables: $1 = chapter ID, $2 = title, $3 = summary. Empty = use default.",
    )
    custom_vol: str = Field(
        "",
        description="Custom volume title template. Variables: $1 = volume index, $2 = volume name. Empty = default '§ name §'.",
    )
    css_text: str = Field(
        "",
        description="EPUB only. Custom CSS string embedded in the EPUB stylesheet.",
    )
    validate_only: bool = Field(
        False,
        description=(
            "If True, verify that the URL is reachable and the token is valid "
            "(by fetching novel info) without performing the actual download. "
            "Returns success=True and output_file='' if validation passes."
        ),
    )


# ─────────────────────────────────────────────
# Tool functions
# ─────────────────────────────────────────────

def get_novel_info(inp: NovelUrl) -> dict:
    """Fetch basic metadata for a Jjwxc novel. No token required.

    Args:
        inp: A NovelUrl containing the novel page URL.

    Returns:
        A dict with the following keys:

        - success (bool): Whether the request succeeded.
        - error (str): Error message on failure, empty string on success.
        - novel_id (str): Numeric novel ID extracted from the URL.
        - title (str): Novel title.
        - author (str): Author display name.
        - author_id (str): Author numeric ID.
        - cover_url (str): URL of the cover image.
        - total_chapters (int): Total chapter count (volume markers excluded).
        - novel_class (str): Genre label, e.g. "现代言情".
        - novel_style (str): Writing style label.
        - novel_tags (str): Comma-separated tags.
        - novel_size (str): Total character count as a string.
        - protagonist (str): Main character name(s).
        - costar (str): Supporting character name(s).
        - intro_short (str): Short synopsis.
        - intro (str): Full synopsis as plain text.
        - locked_chapters (List[str]): Chapter IDs locked by author (unreadable).
        - vip_chapters (List[str]): Chapter IDs that require purchase (VIP).

    Raises:
        ValueError: If the URL does not contain a valid novelid parameter.

    Examples:
        >>> result = get_novel_info(NovelUrl(url="https://www.jjwxc.net/onebook.php?novelid=9091462"))
        >>> result["success"]
        True
        >>> result["title"], result["author"]
        ('书名', '作者名')
    """
    m = re.search(r'novelid=(\d+)', inp.url)
    if not m:
        return {**_empty_info(), "success": False,
                "error": "Invalid URL: must contain novelid=<digits>"}

    novel_id = m.group(1)
    try:
        apicont, cdic, _ = api.fetch_novel_info(novel_id)
    except Exception as exc:
        return {**_empty_info(), "success": False, "error": str(exc)}

    if "message" in apicont and "novelIntro" not in apicont:
        return {**_empty_info(), "success": False,
                "error": apicont.get("message", "Failed to fetch novel info")}

    config = DownloadConfig()
    chapter_data, locked, vip = chapter_mod.parse_chapters(cdic, novel_id, config)

    raw_intro = apicont.get("novelIntro", "")
    intro_text = re.sub(r"&lt;br/?&gt;", "\n", raw_intro)
    intro_text = re.sub(r"<[^>]+>", "", intro_text).strip()

    return {
        "success": True,
        "error": "",
        "novel_id": novel_id,
        "title": apicont.get("novelName", ""),
        "author": apicont.get("authorName", ""),
        "author_id": apicont.get("authorId", ""),
        "cover_url": apicont.get("novelCover", ""),
        "total_chapters": len(chapter_data.href_list),
        "novel_class": apicont.get("novelClass", ""),
        "novel_style": apicont.get("novelStyle", ""),
        "novel_tags": apicont.get("novelTags", ""),
        "novel_size": apicont.get("novelSize", ""),
        "protagonist": apicont.get("protagonist", ""),
        "costar": apicont.get("costar", ""),
        "intro_short": apicont.get("novelIntroShort", ""),
        "intro": intro_text,
        "locked_chapters": locked,
        "vip_chapters": vip,
    }


def list_chapters(inp: ListChaptersInput) -> dict:
    """Return the full chapter list for a novel. No token required.

    Args:
        inp: A ListChaptersInput with url and optional state.

    Returns:
        A dict with the following keys:

        - success (bool): Whether the request succeeded.
        - error (str): Error message on failure.
        - novel_id (str): Numeric novel ID.
        - chapters (List[dict]): One entry per chapter:
            - index (int): 1-based sequential index.
            - title (str): Chapter title.
            - summary (str): Chapter summary / teaser.
            - locked (bool): True if locked by author (unreadable).
            - is_vip (bool): True if the chapter requires purchase (VIP).
            - url (str): Internal API URL for the chapter content.
        - volumes (List[dict]): One entry per volume marker:
            - name (str): Volume title.
            - place_id (str): Chapter ID after which this volume begins.

    Raises:
        ValueError: If the URL does not contain a valid novelid parameter.

    Examples:
        >>> result = list_chapters(ListChaptersInput(url="https://www.jjwxc.net/onebook.php?novelid=9091462"))
        >>> result["chapters"][0]
        {'index': 1, 'title': '...', 'summary': '...', 'locked': False, 'is_vip': True, 'url': '...'}
    """
    m = re.search(r'novelid=(\d+)', inp.url)
    if not m:
        return {"success": False, "error": "Invalid URL: must contain novelid=<digits>",
                "novel_id": "", "chapters": [], "volumes": []}

    novel_id = m.group(1)
    try:
        apicont, cdic, _ = api.fetch_novel_info(novel_id)
    except Exception as exc:
        return {"success": False, "error": str(exc),
                "novel_id": novel_id, "chapters": [], "volumes": []}

    if "message" in apicont and "novelIntro" not in apicont:
        return {"success": False, "error": apicont.get("message", ""),
                "novel_id": novel_id, "chapters": [], "volumes": []}

    config = DownloadConfig()
    config.state = inp.state
    chapter_data, locked_ids, vip_ids = chapter_mod.parse_chapters(cdic, novel_id, config)

    chapters = []
    for idx, (ch_url, title, summary) in enumerate(zip(
        chapter_data.href_list,
        chapter_data.titleindex,
        chapter_data.summary_list,
    )):
        cm = re.search(r'chapterId=(\d+)', ch_url)
        chap_id = cm.group(1) if cm else ""
        chapters.append({
            "index": idx + 1,
            "title": title,
            "summary": summary,
            "locked": chap_id in locked_ids,
            "is_vip": chap_id in vip_ids,
            "url": ch_url,
        })

    volumes = [
        {"name": name, "place_id": place}
        for name, place in zip(chapter_data.roll_sign, chapter_data.roll_sign_place)
    ]

    return {
        "success": True,
        "error": "",
        "novel_id": novel_id,
        "chapters": chapters,
        "volumes": volumes,
    }


def download_novel(inp: DownloadInput) -> dict:
    """Download a Jjwxc novel to TXT or EPUB format.

    Free chapters can be downloaded without a token. Paid (locked) chapters
    require a valid token obtained by capturing traffic from the Jjwxc App.

    Args:
        inp: A DownloadInput model containing all download options.

    Returns:
        A dict with the following keys:

        - success (bool): Whether the download completed without fatal errors.
        - error (str): Error message on failure, empty string on success.
        - output_file (str): Path to the generated file (TXT merge mode) or
          directory (per-chapter / EPUB mode).
        - novel_id (str): Numeric novel ID.
        - title (str): Novel title.
        - author (str): Author display name.
        - total (int): Number of chapters targeted for download.
        - downloaded (int): Number of chapters successfully downloaded.
        - failed (List[str]): Chapter IDs that failed (not purchased or network error).
        - action_needed (str | None): Hint for the LLM on what to do next.
          Values: ``"provide_token"`` (paid chapters require token),
          ``"check_url"`` (URL invalid or novel not found),
          ``"retry_later"`` (network error, safe to retry),
          ``None`` (no action needed).

    Raises:
        ValueError: If the URL is malformed or format_type is unsupported.

    Examples:
        Download full novel as merged TXT:

        >>> result = download_novel(DownloadInput(
        ...     url="https://www.jjwxc.net/onebook.php?novelid=9091462",
        ...     token="YOUR_TOKEN",
        ...     format_type="txt",
        ... ))
        >>> result["output_file"]
        '书名-作者名.9091462.txt'

        Download chapters 10–50 as individual TXT files, traditional→simplified:

        >>> result = download_novel(DownloadInput(
        ...     url="https://www.jjwxc.net/onebook.php?novelid=9091462",
        ...     token="YOUR_TOKEN",
        ...     format_type="txt",
        ...     chapter_start=10,
        ...     chapter_end=50,
        ...     save_per_chapter=True,
        ...     state="s",
        ... ))

        Download as EPUB3 with cover and custom volume template:

        >>> result = download_novel(DownloadInput(
        ...     url="https://www.jjwxc.net/onebook.php?novelid=9091462",
        ...     token="YOUR_TOKEN",
        ...     format_type="epub3",
        ...     add_cover=True,
        ...     custom_vol="第$1卷 $2",
        ... ))
    """
    m = re.search(r'novelid=(\d+)', inp.url)
    if not m:
        return {**_empty_download(inp.url), "success": False,
                "error": "Invalid URL: must contain novelid=<digits>",
                "action_needed": "check_url"}

    if inp.format_type not in ("txt", "epub2", "epub3"):
        return {**_empty_download(inp.url), "success": False,
                "error": f"Unsupported format '{inp.format_type}'. Choose: txt / epub2 / epub3",
                "action_needed": "check_url"}

    if inp.validate_only:
        try:
            apicont, _, _ = api.fetch_novel_info(m.group(1))
            if "message" in apicont and "novelIntro" not in apicont:
                return {**_empty_download(inp.url), "success": False,
                        "error": apicont.get("message", "Novel not found"),
                        "novel_id": m.group(1), "action_needed": "check_url"}
            return {**_empty_download(inp.url), "success": True, "error": "",
                    "novel_id": m.group(1), "action_needed": None}
        except Exception as exc:
            return {**_empty_download(inp.url), "success": False, "error": str(exc),
                    "novel_id": m.group(1), "action_needed": "retry_later"}

    # Token auto-resolution: caller value → config.yml → env var
    token = inp.token
    if not token:
        _cfg_path = os.path.join(_ROOT, "config.yml")
        if os.path.exists(_cfg_path):
            try:
                with open(_cfg_path, encoding="utf-8") as _f:
                    token = (yaml.safe_load(_f) or {}).get("token", "") or ""
            except Exception:
                token = ""
    if not token:
        token = os.environ.get("JJWXC_TOKEN", "")

    config = DownloadConfig()
    _skip = {"url", "output_dir", "validate_only"}
    for field in DownloadInput.model_fields:
        if field not in _skip and hasattr(config, field):
            setattr(config, field, getattr(inp, field))
    config.token = token
    config.output_dir = inp.output_dir or os.path.join(tempfile.gettempdir(), "jjwxc_downloads")
    config.validate_only = inp.validate_only

    downloader = NovelDownloader(config=config)

    try:
        success, output_file, error = downloader.download_novel(inp.url)
    except Exception as exc:
        return {**_empty_download(inp.url), "success": False, "error": str(exc),
                "novel_id": m.group(1), "action_needed": "retry_later"}

    info = downloader.novel_info
    chapter_data = downloader.chapter_data
    failed = downloader.fail_info

    action_needed = None
    if failed:
        action_needed = "provide_token"
    elif not success and error:
        action_needed = "retry_later"

    return {
        "success": success,
        "error": error or "",
        "output_file": output_file or "",
        "novel_id": m.group(1),
        "title": info.title if info else "",
        "author": info.author if info else "",
        "total": len(chapter_data.href_list) if chapter_data else 0,
        "downloaded": downloader.percent,
        "failed": failed,
        "action_needed": action_needed,
    }


# ─────────────────────────────────────────────
# Tool registry
# ─────────────────────────────────────────────

def get_tools() -> List[dict]:
    """Return all available tools as a list of OpenAI function-calling dicts.

    Returns:
        List of tool definition dicts compatible with OpenAI / Anthropic
        function-calling APIs. Each entry has the shape::

            {
                "type": "function",
                "function": {
                    "name": str,
                    "description": str,
                    "parameters": <JSON Schema object>
                }
            }

    Examples:
        >>> import openai
        >>> from tools.tools import get_tools
        >>> response = openai.chat.completions.create(
        ...     model="gpt-4o",
        ...     messages=[{"role": "user", "content": "帮我查一下这本小说的信息 https://www.jjwxc.net/onebook.php?novelid=9091462"}],
        ...     tools=get_tools(),
        ... )
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_novel_info",
                "description": (
                    "Fetch basic metadata for a Jjwxc novel page (no token required). "
                    "Returns: title, author, author_id, cover_url, total_chapters, "
                    "novel_class, novel_tags, novel_size, protagonist, intro, locked_chapters. "
                    "Typical use: confirm novel identity + check for paid chapters "
                    "before deciding whether to download. "
                    "Constraint: URL must contain novelid=<digits>."
                ),
                "parameters": NovelUrl.model_json_schema(),
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_chapters",
                "description": (
                    "Return the full chapter list for a novel (no token required). "
                    "Each entry includes: index, title, summary, locked (bool), url. "
                    "Use when the user wants to browse chapter titles, check which chapters "
                    "are paid, or select a specific chapter range before downloading. "
                    "Most download tasks can skip this and go directly to download_novel."
                ),
                "parameters": ListChaptersInput.model_json_schema(),
            },
        },
        {
            "type": "function",
            "function": {
                "name": "download_novel",
                "description": (
                    "Download a Jjwxc novel to TXT / EPUB2 / EPUB3. "
                    "Free chapters work without token; paid chapters must have a valid jjwxc App token. "
                    "Use get_novel_info first to check locked_chapters before calling this. "
                    "Token tip: read from config.yml `token` field or env var JJWXC_TOKEN. "
                    "output_dir defaults to a temp folder; set explicitly in production. "
                    "Supports: chapter range (chapter_start/end, 1-based), "
                    "per-chapter TXT saving, Chinese conversion (state: s/t), "
                    "custom title/volume templates, EPUB cover, CSS. "
                    "Returns: {success, output_file, downloaded, total, failed, action_needed}. "
                    "action_needed values: provide_token | check_url | retry_later | null."
                ),
                "parameters": DownloadInput.model_json_schema(),
            },
        },
    ]


def call_tool(name: str, arguments: dict) -> Any:
    """Dispatch a tool call by name with a plain dict of arguments.

    This is the universal entry point for non-OpenAI frameworks
    (AutoGen, LangChain, CrewAI, etc.).

    Args:
        name: Tool function name. One of: get_novel_info, list_chapters,
            download_novel.
        arguments: Dict of keyword arguments matching the tool's input model.

    Returns:
        The return value of the called tool function.

    Raises:
        ValueError: If ``name`` does not match any registered tool.

    Examples:
        >>> from tools.tools import call_tool
        >>> info = call_tool("get_novel_info", {"url": "https://www.jjwxc.net/onebook.php?novelid=9091462"})
        >>> chapters = call_tool("list_chapters", {"url": "...", "state": "s"})
        >>> result = call_tool("download_novel", {"url": "...", "token": "...", "format_type": "epub3"})
    """
    _map = {
        "get_novel_info": lambda a: get_novel_info(NovelUrl(**a)),
        "list_chapters": lambda a: list_chapters(ListChaptersInput(**a)),
        "download_novel": lambda a: download_novel(DownloadInput(**a)),
    }
    if name not in _map:
        raise ValueError(f"Unknown tool '{name}'. Available: {list(_map.keys())}")
    return _map[name](arguments)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _empty_info() -> dict:
    return {
        "success": False, "error": "",
        "novel_id": "", "title": "", "author": "", "author_id": "",
        "cover_url": "", "total_chapters": 0, "novel_class": "",
        "novel_style": "", "novel_tags": "", "novel_size": "",
        "protagonist": "", "costar": "", "intro_short": "", "intro": "",
        "locked_chapters": [],
        "vip_chapters": [],
    }


def _empty_download(url: str) -> dict:
    m = re.search(r'novelid=(\d+)', url)
    return {
        "success": False, "error": "",
        "output_file": "", "novel_id": m.group(1) if m else "",
        "title": "", "author": "", "total": 0, "downloaded": 0, "failed": [],
    }
