import asyncio
import random

from absl import flags, logging as log
from aiohttp import ClientSession

FLAGS = flags.FLAGS

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}
RETRYABLE_STATUSES = {403, 429, 465, 500, 502, 503, 504}


async def fetch(
    session: ClientSession,
    url: str,
    headers: dict[str, str] | None = None,
    retries: int = 3,
    backoff_base: float = 0.5,
) -> tuple[int, str]:
    log.info(f"fetching {url}")
    merged_headers = DEFAULT_HEADERS.copy()
    if headers:
        merged_headers.update(headers)
    for attempt in range(retries + 1):
        try:
            async with session.get(url, headers=merged_headers) as response:
                status = response.status
                content = await response.content.read()
                if status == 200 or status not in RETRYABLE_STATUSES or attempt == retries:
                    return status, content
                delay = backoff_base * (2**attempt) + random.uniform(0, 0.25)
                log.warning(f"retryable status={status} for {url}, retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
        except Exception as exc:  # NOQA
            if attempt == retries:
                log.exception(f"fetch failed for {url} after {retries + 1} attempts: {exc}")
                raise
            delay = backoff_base * (2**attempt) + random.uniform(0, 0.25)
            log.warning(f"fetch error for {url}: {exc}, retrying in {delay:.2f}s")
            await asyncio.sleep(delay)


def zip_blank_lines(lines):
    """If there are multiple blank lines, generate only one."""
    first_blank_line = False
    for line in lines:
        if line:
            first_blank_line = False
            yield line
        else:
            if first_blank_line:
                continue
            yield line
            first_blank_line = True
