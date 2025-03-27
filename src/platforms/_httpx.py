import asyncio
from typing import Optional, Dict, Any

import aiofiles
import httpx

from config import API_KEY
from src.logger import LOGGER


class HttpxClient:
    def __init__(self, timeout: int = 10, download_timeout: int = 60):
        """
        Initialize the HTTP client with configurable timeouts.

        :param timeout: Timeout for general HTTP requests in seconds.
        :param download_timeout: Timeout for file downloads in seconds.
        """
        self.timeout = timeout
        self.download_timeout = download_timeout
        self.session = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()

    async def download_file(self, url: str, filename: str) -> Optional[str]:
        """
        Download a file asynchronously and save it to disk.

        :param url: The URL of the file to download.
        :param filename: The path where the file will be saved.
        :return: The filename if successful, otherwise None.
        """
        try:
            async with self.session.stream(
                    "GET", url, timeout=self.download_timeout
            ) as response:
                response.raise_for_status()
                async with aiofiles.open(filename, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)
                LOGGER.info(f"Downloaded file: {filename}")
                return filename
        except httpx.HTTPStatusError as e:
            LOGGER.error(
                f"HTTP error while downloading {url}: {e.response.status_code}"
            )
        except httpx.RequestError as e:
            LOGGER.error(f"Request failed while downloading {url}: {e}")
        except Exception as e:
            LOGGER.error(f"Unexpected error while downloading {url}: {e}")
        return None

    async def make_request(
            self, url: str, max_retries: int = 3, backoff_factor: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """
        Make an HTTP GET request with retries and exponential backoff.

        :param url: The URL to request.
        :param max_retries: Maximum number of retries.
        :param backoff_factor: Factor for exponential backoff.
        :return: The JSON response as a dictionary if successful, otherwise None.
        """
        if not url:
            LOGGER.warning("URL is empty")
            return None

        headers = {"X-API-Key": API_KEY}

        for attempt in range(max_retries):
            try:
                response = await self.session.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                LOGGER.error(f"HTTP error for {url}: {e.response.status_code}")
                if attempt == max_retries - 1:
                    return None
            except httpx.RequestError as e:
                LOGGER.error(f"Request failed for {url}: {e}")
                if attempt == max_retries - 1:
                    return None
            except Exception as e:
                LOGGER.error(f"Unexpected error for {url}: {e}")
                return None

            # Exponential backoff
            await asyncio.sleep(backoff_factor * (2 ** attempt))

        return None

    async def __aenter__(self):
        """Enter the async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager and close the session."""
        await self.close()
