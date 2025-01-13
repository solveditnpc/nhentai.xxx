"""
Copyright (C) 2024  solveditnpc

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import re
import os
import asyncio
import traceback
import httpx
import img2pdf
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

@dataclass
class ImagePattern:
    """Data class to store image pattern information"""
    pattern: str
    base_dir: str

@dataclass
class VerificationResult:
    """Data class to store verification result"""
    page_num: int
    url: Optional[str]
    server: Optional[str]
    extension: Optional[str]

def extract_manga_id(url: str) -> str:
    """Extract manga ID from nhentai.xxx URL"""
    match = re.search(r'/g/(\d+)/?', url)
    if match:
        return match.group(1)
    
    parts = url.rstrip('/').split('/')
    for part in reversed(parts):
        if part.isdigit():
            return part
    
    raise ValueError(f"Could not extract manga ID from URL: {url}")

def safe_format_filename(name: str) -> str:
    """Safely format filename, handling None and empty string cases"""
    if not name:
        return ''
    
    sanitized_name = re.sub(r'[<>:"/\\|?*]', '', name).strip()
    return sanitized_name[:255]

def calculate_optimal_concurrency(total_pages: int) -> int:
    """
    Calculate optimal number of concurrent downloads based on manga characteristics
    
    Rules:
    - Minimum concurrency: 3
    - Maximum concurrency: 10
    - For manga with <= 25 pages: 3 concurrent downloads
    - For manga with > 25 pages: Scales up to max 10 based on page count
    - Takes into account system limitations
    
    :param total_pages: Total number of pages in the manga
    :return: Optimal number of concurrent downloads
    """
    if total_pages <= 25:
        return 3
        
    # Scale concurrency based on page count
    # More pages = more concurrent downloads, up to a maximum
    cpu_count = os.cpu_count() or 4  # Fallback to 4 if cpu_count is None
    base_concurrency = min(cpu_count * 2, 10)  # Don't exceed 10 even on many-core systems
    
    if total_pages <= 50:
        return min(5, base_concurrency)
    elif total_pages <= 100:
        return min(7, base_concurrency)
    else:
        return base_concurrency  # Use maximum allowed concurrency for large manga

def calculate_optimal_concurrency_verification(total_urls: int) -> int:
    """
    Calculate optimal number of concurrent verifications
    
    Rules for verification:
    - Minimum concurrency: 5 (verification is less resource-intensive than downloading)
    - Maximum concurrency: 20 (higher than download as it's just HEAD requests)
    - For <= 50 URLs: 5 concurrent verifications
    - For > 50 URLs: Scales up to max 20 based on URL count
    - Takes into account system limitations
    
    :param total_urls: Total number of URLs to verify
    :return: Optimal number of concurrent verifications
    """
    if total_urls <= 50:
        return 5
        
    cpu_count = os.cpu_count() or 4
    base_concurrency = min(cpu_count * 4, 20)  # More aggressive than download concurrency
    
    if total_urls <= 100:
        return min(10, base_concurrency)
    elif total_urls <= 200:
        return min(15, base_concurrency)
    else:
        return base_concurrency

async def verify_image_url(
    client: httpx.AsyncClient,
    page_num: int,
    pattern: ImagePattern,
    server: str,
    headers: Dict[str, str],
    semaphore: asyncio.Semaphore
) -> VerificationResult:
    """Verify a single image URL with all possible combinations"""
    async with semaphore:
        img_headers = headers.copy()
        img_headers['Host'] = f'{server}.nhentaimg.com'
        
        for ext in ['.jpg', '.png', '.webp']:
            test_urls = [
                f"http://{server}.nhentaimg.com/{pattern.pattern}/{page_num}{ext}",
                f"https://{server}.nhentaimg.com/{pattern.pattern}/{page_num}{ext}",
                f"http://{server}.nhentaimg.com/{pattern.base_dir}/{pattern.pattern.split('/')[-1]}/{page_num}{ext}",
                f"https://{server}.nhentaimg.com/{pattern.base_dir}/{pattern.pattern.split('/')[-1]}/{page_num}{ext}"
            ]
            
            for test_url in test_urls:
                try:
                    response = await client.head(test_url, headers=img_headers)
                    if response.status_code == 200:
                        return VerificationResult(page_num, test_url, server, ext)
                except Exception:
                    continue
    
    return VerificationResult(page_num, None, None, None)

async def fetch_manga_images(manga_id: str) -> Tuple[Dict[int, str], List[int]]:
    """Fetch manga image URLs using parallel verification"""
    headers = {
        'Accept': 'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Host': 'i4.nhentaimg.com',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133',
        'X-Firefox-Spdy': 'h2'
    }
    
    page_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Host': 'nhentai.xxx',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133',
        'Upgrade-Insecure-Requests': '1'
    }
    
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)  # Increased for parallel verification
    timeout = httpx.Timeout(10.0, connect=5.0)
    transport = httpx.AsyncHTTPTransport(retries=3)
    
    async with httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        transport=transport,
        follow_redirects=True,
        verify=False,
        http2=True
    ) as client:
        try:
            gallery_url = f"https://nhentai.xxx/g/{manga_id}/"
            print(f"Fetching gallery page: {gallery_url}")
            
            response = await client.get(gallery_url, headers=page_headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            print("\nLooking for thumbnails...")
            thumbs = soup.find_all('img', class_='lazyload')
            
            patterns = []
            base_dirs = set()
            
            for thumb in thumbs:
                if 'data-src' in thumb.attrs:
                    src = thumb['data-src']
                    print(f"Found thumbnail: {src}")
                    
                    match = re.search(r'i\d\.nhentaimg\.com/(\d+/[a-zA-Z0-9]+)/', src)
                    if match:
                        pattern = match.group(1)
                        base_dir = pattern.split('/')[0]
                        base_dirs.add(base_dir)
                        patterns.append(pattern)
                        print(f"Found pattern: {pattern}")
            
            if patterns:
                pattern = ImagePattern(patterns[0], list(base_dirs)[0])
                print(f"\nUsing pattern: {pattern.pattern}")
                print(f"Base directory: {pattern.base_dir}")
                
                # Start with a small batch to estimate total pages
                test_pages = list(range(1, 6))
                max_concurrent = calculate_optimal_concurrency_verification(len(test_pages))
                semaphore = asyncio.Semaphore(max_concurrent)
                
                verification_tasks = []
                for page_num in test_pages:
                    for server in ['i1', 'i2', 'i3', 'i4', 'i5', 'i6']:
                        task = verify_image_url(
                            client,
                            page_num,
                            pattern,
                            server,
                            headers,
                            semaphore
                        )
                        verification_tasks.append(task)
                
                print(f"Initial verification with {max_concurrent} concurrent tasks...")
                results = await asyncio.gather(*verification_tasks)
                
                # Find working server and estimate total pages
                working_server = None
                for result in results:
                    if result.url:
                        working_server = result.server
                        break
                
                if not working_server:
                    raise ValueError("Could not find working image server")
                
                print(f"Found working server: {working_server}")
                
                # Now verify all pages with the working server
                image_urls = {}
                page = 1
                consecutive_failures = 0
                verification_tasks = []
                
                while consecutive_failures < 5:
                    result = await verify_image_url(
                        client,
                        page,
                        pattern,
                        working_server,
                        headers,
                        semaphore
                    )
                    
                    if result.url:
                        image_urls[page] = result.url
                        print(f"Verified page {page}")
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        print(f"Could not verify page {page} (Consecutive failures: {consecutive_failures})")
                        if consecutive_failures >= 5:
                            break
                    
                    page += 1
                
                if image_urls:
                    print(f"\nVerified {len(image_urls)} images")
                    return image_urls, []
            
            print("\nDebug: Page source")
            print(response.text[:2000])
            raise ValueError("Could not find image pattern")
            
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            return {}, []

def convert_to_pdf(manga_dir: str, downloaded_files: List[str]) -> None:
    """Convert downloaded manga images to PDF"""
    try:
        image_files = sorted(downloaded_files)
        
        if not image_files:
            print(f"No images found in {manga_dir} to convert to PDF")
            return
            
        pdf_name = os.path.basename(manga_dir) + '.pdf'
        pdf_path = os.path.join(manga_dir, pdf_name)
        
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(image_files))
            
        print(f"Successfully created PDF: {pdf_path}")
        
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        traceback.print_exc()

async def download_image(
    client: httpx.AsyncClient,
    page_num: int,
    img_url: str,
    manga_dir: str,
    headers: Dict[str, str],
    semaphore: asyncio.Semaphore,
    downloaded_files: Set[str],
    failed_pages: Set[int],
    total_pages: int
) -> None:
    """Download a single image with semaphore control"""
    async with semaphore:
        try:
            img_headers = headers.copy()
            img_headers['Host'] = img_url.split('/')[2]
            
            response = await client.get(img_url, headers=img_headers)
            response.raise_for_status()
            
            ext = os.path.splitext(img_url)[1]
            if not ext:
                ext = '.webp'
            
            filename = f"{page_num:03d}{ext}"
            filepath = os.path.join(manga_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            downloaded_files.add(filepath)
            print(f"Downloaded page {page_num}/{total_pages}")
            
        except Exception as e:
            print(f"Failed to download page {page_num}: {e}")
            failed_pages.add(page_num)

async def download_manga(url: str) -> Tuple[str, List[int]]:
    """Download manga with parallel verification and downloading"""
    manga_id = extract_manga_id(url)
    base_dir = os.path.join(os.getcwd(), 'downloads')
    os.makedirs(base_dir, exist_ok=True)
    
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("Debug - HTML Content:")
        print(soup.prettify()[:1000])
        
        title_element = None
        selectors = [
            'div#info > h1',
            'div#info h1',
            'h1',
            'div.title',
            'h2.title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                print(f"Found element with selector '{selector}': {element.text.strip()}")
                if not title_element:
                    title_element = element
        
        manga_name = ''
        if title_element:
            manga_name = safe_format_filename(title_element.text.strip())
            print(f"Using manga title: {manga_name}")
        else:
            print("Warning: Could not find manga title")
            info_div = soup.select_one('#info')
            if info_div:
                first_text = info_div.get_text(strip=True).split('\n')[0]
                manga_name = safe_format_filename(first_text)
                print(f"Using fallback title from #info: {manga_name}")
        
        manga_dir = os.path.join(base_dir, f"{manga_id}_{manga_name}")
        print(f"Creating directory: {manga_dir}")
        os.makedirs(manga_dir, exist_ok=True)
        
        print(f"Starting verification and download for manga {manga_id}...")
        image_urls, _ = await fetch_manga_images(manga_id)
        
        if not image_urls:
            print("No images found to download")
            return None, []
        
        total_pages = len(image_urls)
        max_concurrent = calculate_optimal_concurrency(total_pages)
        print(f"\nDownloading {total_pages} images with {max_concurrent} concurrent downloads...")
        
        headers = {
            'Accept': 'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-GPC': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133',
            'X-Firefox-Spdy': 'h2'
        }
        
        downloaded_files: Set[str] = set()
        failed_pages: Set[int] = set()
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=False,
            http2=True
        ) as client:
            tasks = []
            for page_num, img_url in sorted(image_urls.items()):
                task = download_image(
                    client,
                    page_num,
                    img_url,
                    manga_dir,
                    headers,
                    semaphore,
                    downloaded_files,
                    failed_pages,
                    total_pages
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks)
        
        if downloaded_files:
            print(f"\nDownload completed! Files saved in: {manga_dir}")
            convert_to_pdf(manga_dir, list(sorted(downloaded_files)))  # Sort files before PDF conversion
            if failed_pages:
                print(f"Failed to download pages: {sorted(failed_pages)}")  # Sort failed pages for cleaner output
        else:
            print("Failed to download any images")
        
        return manga_dir, list(sorted(failed_pages))  # Sort failed pages in return value

def is_valid_nhentai_xxx_url(url: str) -> bool:
    """Validate if the URL is from nhentai.xxx"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return 'nhentai.xxx/g/' in url

async def main():
    try:
        with open('constants.txt', 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if not urls:
            print("No URLs found in constants.txt")
            return
        
        for url in urls:
            if 'https://' not in url and 'http://' not in url:
                continue
                
            if not is_valid_nhentai_xxx_url(url):
                print(f"Skipping invalid URL (not from nhentai.xxx): {url}")
                continue
            
            try:
                await download_manga(url)
                print(f"Successfully downloaded manga from: {url}")
            except Exception as e:
                print(f"Error downloading manga from {url}: {str(e)}")
                traceback.print_exc()
    except Exception as e:
        print(f"Error reading constants.txt: {str(e)}")
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
