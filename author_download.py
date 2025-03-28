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
import httpx
import shutil
from bs4 import BeautifulSoup
from typing import List, Optional
from parallel_download import download_manga

async def get_total_pages(client: httpx.AsyncClient, base_url: str, headers: dict) -> int:
    """Get the total number of pages for a search result or listing."""
    response = await client.get(base_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the last page number from pagination
    last_page = 1
    pagination = soup.find('div', class_='pagination')
    if pagination:
        page_links = pagination.find_all('a', class_='page')
        if page_links:
            try:
                last_page = max(int(link.text) for link in page_links if link.text.isdigit())
            except ValueError:
                pass
    return last_page

async def search_author(author_name: str) -> List[tuple[str, int]]:
    """
    Search for manga URLs by author name on nhentai.xxx
    
    :param author_name: Name of the author to search for
    :return: List of tuples containing (manga_url, page_number)
    """
    headers = {
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
    
    async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
        manga_links = []
        current_page = 1
        continue_search = True
        
        while continue_search:
            # Format URL based on page number
            if current_page == 1:
                page_url = f'https://nhentai.xxx/search/?key={author_name}'
            else:
                page_url = f'https://nhentai.xxx/search/?key={author_name}&page={current_page}'
            
            print(f"\nScanning page {current_page}...")
            print(f"URL: {page_url}")
            
            try:
                response = await client.get(page_url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all manga links on current page
                galleries = soup.find_all('div', class_='gallery_item')
                found_manga_on_page = False
                
                for gallery in galleries:
                    link = gallery.find('a')
                    if link and 'href' in link.attrs:
                        manga_url = f'https://nhentai.xxx{link["href"]}'
                        if not any(url for url, _ in manga_links if url == manga_url):
                            manga_links.append((manga_url, current_page))
                            print(f"Added manga: {manga_url}")
                            found_manga_on_page = True
                
                # First check if we found any manga
                if not found_manga_on_page:
                    print("\nNo manga found on current page, stopping search")
                    continue_search = False
                    continue

                # Try different ways to find pagination
                pagination = None
                # Method 1: Look for pagination div
                pagination_div = soup.find('div', class_='pagination')
                if pagination_div:
                    pagination = pagination_div
                
                # Method 2: Look for any numbered links that could be pages
                if not pagination:
                    all_links = soup.find_all('a')
                    page_links = [a for a in all_links if a.text.isdigit()]
                    if page_links:
                        pagination = page_links

                # Method 3: Look for next/previous links
                if not pagination:
                    next_links = [a for a in soup.find_all('a') if '>' in a.text or 'next' in a.text.lower()]
                    if next_links:
                        pagination = next_links

                # Debug pagination detection
                print(f"\nPagination detection result: {'Found' if pagination else 'Not found'}")
                
                # Process pagination if found
                if pagination:
                    # Get all page numbers from the page
                    all_numbers = []
                    if isinstance(pagination, list):
                        all_numbers = [int(a.text) for a in pagination if a.text.isdigit()]
                    else:
                        all_numbers = [int(a.text) for a in pagination.find_all('a') if a.text.isdigit()]
                    
                    # Try to get the next page number
                    next_page = current_page + 1
                    
                    # Test if next page exists by making a HEAD request
                    next_url = f'https://nhentai.xxx/search/?key={author_name}&page={next_page}'
                    try:
                        test_response = await client.head(next_url, headers=headers)
                        if test_response.status_code == 200:
                            current_page = next_page
                            print(f"Moving to page {current_page}...")
                            await asyncio.sleep(1)  # Small delay between requests
                            continue
                    except Exception as e:
                        print(f"Error testing next page: {str(e)}")
                
                # If we reach here, we couldn't find more pages
                print("\nNo more pages found")
                continue_search = False
                
            except Exception as e:
                print(f"Error fetching page {current_page}: {str(e)}")
                continue_search = False
        
        if not manga_links:
            print("No manga found across all pages")
        else:
            print(f"\nTotal manga found: {len(manga_links)} across {current_page} pages")
        
        return manga_links

async def get_page_manga_urls(page_url: str) -> List[str]:
    """
    Get all manga URLs from a specific page on nhentai.xxx
    
    :param page_url: URL of the page to scrape
    :return: List of manga URLs
    """
    headers = {
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
    
    async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
        response = await client.get(page_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        manga_links = []
        
        # Find all manga links on the page
        for link in soup.find_all('a', href=re.compile(r'/g/\d+')):
            manga_url = f'https://nhentai.xxx{link["href"]}'
            if manga_url not in manga_links:
                manga_links.append(manga_url)
        
        return manga_links

async def main():
    print("Welcome to nhentai.xxx Manga Downloader!")
    print("1. Download manga by author name")
    print("2. Download manga from specific page")
    
    # Ask for download location
    default_download_dir = os.path.join(os.getcwd(), 'downloads')
    download_dir = input(f"Enter download directory path (press Enter for default: {default_download_dir}): ").strip()
    
    # Use default if no input provided
    if not download_dir:
        download_dir = default_download_dir
    
    # Create directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)
    print(f"\nDownloads will be saved to: {download_dir}\n")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == '1':
        author_name = input("Enter author name: ").strip()
        print(f"\nSearching for manga by {author_name}...")
        manga_data = await search_author(author_name)
        
        if not manga_data:
            print(f"No manga found for author: {author_name}")
            return
            
        print(f"\nFound {len(manga_data)} manga by {author_name} across multiple pages")
        
        # Group manga by page number
        manga_by_page = {}
        for url, page in manga_data:
            if page not in manga_by_page:
                manga_by_page[page] = []
            manga_by_page[page].append(url)
        
        print("\nManga found by page:")
        manga_index = 1
        indexed_manga = []
        for page in sorted(manga_by_page.keys()):
            print(f"\nPage {page}:")
            for url in manga_by_page[page]:
                print(f"{manga_index}. {url}")
                indexed_manga.append(url)
                manga_index += 1
        
    elif choice == '2':
        page_url = input("Enter the nhentai.xxx page URL: ").strip()
        if not page_url.startswith('https://nhentai.xxx/'):
            print("Invalid URL. URL must be from nhentai.xxx")
            return
            
        print("\nFetching manga from the page...")
        manga_urls = await get_page_manga_urls(page_url)
        indexed_manga = manga_urls
        
        if not manga_urls:
            print("No manga found on the specified page")
            return
            
        print(f"\nFound {len(manga_urls)} manga on the page")
        print("\nManga URLs found:")
        for i, url in enumerate(manga_urls, 1):
            print(f"{i}. {url}")
        
    else:
        print("Invalid choice. Please enter 1 or 2.")
        return
    
    print("\nDo you want to:")
    print("1. Download all manga")
    print("2. Select specific manga to download")
    download_choice = input("Enter your choice (1 or 2): ").strip()
    
    manga_to_download = []
    if download_choice == '1':
        manga_to_download = indexed_manga
    elif download_choice == '2':
        print("\nEnter the numbers of the manga you want to download (comma-separated)")
        print("Example: 1,3,5 to download the 1st, 3rd, and 5th manga")
        selections = input("Numbers: ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selections.split(',')]
            for idx in indices:
                if 0 <= idx < len(indexed_manga):
                    manga_to_download.append(indexed_manga[idx])
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas.")
            return
    else:
        print("Invalid choice. Please enter 1 or 2.")
        return
    
    if not manga_to_download:
        print("No manga selected for download.")
        return
    
    print(f"\nStarting downloads... ({len(manga_to_download)} manga total)")
    try:
        for i, url in enumerate(manga_to_download, 1):
            try:
                print(f"\nDownloading manga {i}/{len(manga_to_download)}...")
                await download_manga(url, download_dir)
                print(f"Successfully downloaded: {url}")
            except Exception as e:
                print(f"Failed to download {url}: {str(e)}")
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user. Already downloaded manga are saved.")
        return
    
    print("\nAll downloads completed!")
    
    # Create pdf directory and collect PDFs
    pdf_dir = os.path.join(download_dir, 'pdf')
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Counter for found PDFs
    pdf_count = 0
    
    # Walk through directory
    for root, _, files in os.walk(download_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                # Skip if file is already in pdf directory
                if root == pdf_dir:
                    continue
                    
                source_path = os.path.join(root, file)
                dest_path = os.path.join(pdf_dir, file)
                
                # Copy file
                try:
                    shutil.copy2(source_path, dest_path)
                    pdf_count += 1
                    print(f'Copied: {file}')
                except Exception as e:
                    print(f'Error copying {file}: {str(e)}')
    
    print(f'\nPDF Collection completed! {pdf_count} PDF files were copied to {pdf_dir}')

if __name__ == '__main__':
    asyncio.run(main())