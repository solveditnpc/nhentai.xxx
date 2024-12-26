"""
Copyright (C) 2024  solveditnpc

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import re
import os
import asyncio
import traceback
import httpx
from bs4 import BeautifulSoup

def extract_manga_id(url):
    """
    Extract manga ID from nhentai.xxx URL
    
    :param url: Full URL of the manga on nhentai.xxx
    :return: Manga ID as a string
    """
    match = re.search(r'/g/(\d+)/?', url)
    if match:
        return match.group(1)
    
    parts = url.rstrip('/').split('/')
    for part in reversed(parts):
        if part.isdigit():
            return part
    
    raise ValueError(f"Could not extract manga ID from URL: {url}")

def safe_format_filename(name):
    """
    Safely format filename, handling None and empty string cases
    
    :param name: Input name to format
    :return: Formatted filename
    """
    if not name:
        return ''
    
    sanitized_name = re.sub(r'[<>:"/\\|?*]', '', name).strip()
    return sanitized_name[:255]  # Limit filename length

async def fetch_manga_images(manga_id):
    """
    Fetch manga image URLs using exact browser headers
    """
    # Base headers for image requests
    headers = {
        'Accept': 'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Host': 'i4.nhentaimg.com',  # Will be updated per request
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133',
        'X-Firefox-Spdy': 'h2'
    }
    
    # Headers for HTML page requests
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
    
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
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
            # First get the main gallery page
            gallery_url = f"https://nhentai.xxx/g/{manga_id}/"
            print(f"Fetching gallery page: {gallery_url}")
            
            response = await client.get(gallery_url, headers=page_headers)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for thumbnails
            print("\nLooking for thumbnails...")
            thumbs = soup.find_all('img', class_='lazyload')
            
            # Store all patterns we find
            patterns = []
            base_dirs = set()
            
            for thumb in thumbs:
                if 'data-src' in thumb.attrs:
                    src = thumb['data-src']
                    print(f"Found thumbnail: {src}")
                    
                    # Extract the pattern from thumbnail URL
                    # Example: http://i4.nhentaimg.com/016/y3v5c6xhgf/cover.jpg
                    match = re.search(r'i\d\.nhentaimg\.com/(\d+/[a-zA-Z0-9]+)/', src)
                    if match:
                        pattern = match.group(1)
                        base_dir = pattern.split('/')[0]  # Get the base directory (e.g., '016')
                        base_dirs.add(base_dir)
                        patterns.append(pattern)
                        print(f"Found pattern: {pattern}")
            
            if patterns:
                # Use the first pattern we found
                image_pattern = patterns[0]
                base_dir = list(base_dirs)[0]
                print(f"\nUsing pattern: {image_pattern}")
                print(f"Base directory: {base_dir}")
                
                # Now we can construct URLs for all pages
                image_urls = {}  # Changed to dict to maintain page numbers
                page = 1
                consecutive_failures = 0
                
                while consecutive_failures < 5:
                    url_found = False
                    for server in ['i1', 'i2', 'i3', 'i4', 'i5', 'i6']:
                        if url_found:
                            break
                        
                        # Update headers for each server
                        img_headers = headers.copy()
                        img_headers['Host'] = f'{server}.nhentaimg.com'
                        
                        # Try different URL patterns and extensions
                        test_urls = []
                        for ext in ['.jpg', '.png', '.webp']:
                            test_urls.extend([
                                f"http://{server}.nhentaimg.com/{image_pattern}/{page}{ext}",
                                f"https://{server}.nhentaimg.com/{image_pattern}/{page}{ext}",
                                f"http://{server}.nhentaimg.com/{base_dir}/{image_pattern.split('/')[-1]}/{page}{ext}",
                                f"https://{server}.nhentaimg.com/{base_dir}/{image_pattern.split('/')[-1]}/{page}{ext}"
                            ])
                        
                        for test_url in test_urls:
                            try:
                                response = await client.head(test_url, headers=img_headers)
                                if response.status_code == 200:
                                    image_urls[page] = test_url  # Store URL with page number as key
                                    print(f"Found page {page}")
                                    url_found = True
                                    consecutive_failures = 0
                                    break
                            except Exception as e:
                                continue
                        
                        if url_found:
                            break
                    
                    if not url_found:
                        consecutive_failures += 1
                        print(f"Could not find page {page} (Consecutive failures: {consecutive_failures})")
                        if consecutive_failures >= 5:
                            break
                    
                    page += 1
                
                if image_urls:
                    print(f"\nFound {len(image_urls)} images")
                    return image_urls, []  # Return dict instead of list
            
            print("\nDebug: Page source")
            print(response.text[:2000])
            raise ValueError("Could not find image pattern")
            
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            return {}, []  # Return empty dict instead of list

async def download_manga(url):
    """
    Download manga images
    """
    try:
        manga_id = extract_manga_id(url)
        download_folder = os.path.join(os.getcwd(), f"manga_{manga_id}")
        os.makedirs(download_folder, exist_ok=True)
        
        print(f"Starting download for manga {manga_id}...")
        image_urls, failed_pages = await fetch_manga_images(manga_id)
        
        if not image_urls:
            print("No images found to download")
            return None, []
        
        print(f"\nDownloading {len(image_urls)} images...")
        
        # Download images with exact headers
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
        
        downloaded_files = []
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=False,
            http2=True
        ) as client:
            for page_num, img_url in sorted(image_urls.items()):  # Sort by page number
                try:
                    # Update headers with correct host
                    img_headers = headers.copy()
                    img_headers['Host'] = img_url.split('/')[2]
                    
                    # Download image
                    response = await client.get(img_url, headers=img_headers)
                    response.raise_for_status()
                    
                    # Get file extension from URL
                    ext = os.path.splitext(img_url)[1]
                    if not ext:
                        ext = '.webp'  # Default to webp if no extension found
                    
                    # Save image with correct page number
                    filename = f"{page_num:03d}{ext}"
                    filepath = os.path.join(download_folder, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    downloaded_files.append(filepath)
                    print(f"Downloaded page {page_num}/{max(image_urls.keys())}")
                    
                except Exception as e:
                    print(f"Failed to download page {page_num}: {e}")
                    if page_num not in failed_pages:
                        failed_pages.append(page_num)
        
        if downloaded_files:
            print(f"\nDownload completed! Files saved in: {download_folder}")
            if failed_pages:
                print(f"Failed to download pages: {failed_pages}")
        else:
            print("Failed to download any images")
        
        return download_folder, failed_pages
        
    except Exception as e:
        print(f"Error downloading manga: {e}")
        traceback.print_exc()
        return None, []

async def main():
    """
    Main function to read manga URLs from user input and download each manga
    """
    while True:
        try:
            url = input("\nEnter nhentai.xxx manga URL (or press Enter to exit): ").strip()
            
            if not url:
                break
                
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            if 'nhentai.xxx' not in url:
                print("Please enter a valid nhentai.xxx URL")
                continue
                
            download_path, failed_pages = await download_manga(url)
            
            if download_path:
                print(f"\nManga downloaded to: {download_path}")
            else:
                print("\nFailed to download manga")
                
        except KeyboardInterrupt:
            print("\nDownload cancelled by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())