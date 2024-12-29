# Nhentai.xxx Manga Downloader

## Overview
This Python script enables downloading manga from nhentai.xxx through advanced web scraping techniques. Unlike nhentai.net which provides a public API, nhentai.xxx implements various anti-scraping measures including JavaScript-based page rendering and encrypted image galleries. This script successfully bypasses these protections using sophisticated pattern matching and direct image server access.

## Key Features
- Downloads complete manga chapters with correct page ordering
- Saves manga in organized folders with format: `mangaID_mangaName`
- Handles anti-scraping protections without using Selenium or browser automation
- Supports batch downloading through a constants.txt file
- Implements parallel downloads using asyncio for better performance
- Maintains proper HTTP headers to mimic browser behavior

## Technical Implementation

### Anti-Scraping Bypass
The script overcomes several anti-scraping measures:

1. **Browser Fingerprinting**
   - Implements exact browser headers including User-Agent, Accept, and Connection settings
   - Maintains proper HTTP/2 support through httpx
   - Sets appropriate security headers (DNT, Sec-Fetch) to appear as legitimate browser traffic

2. **Gallery Pattern Detection**
   - Instead of relying on JavaScript-rendered content, identifies image patterns from thumbnail URLs
   - Extracts server ID (i1-i4) and gallery hash from thumbnail sources
   - Reconstructs full-resolution image URLs using the discovered patterns

3. **Direct Image Access**
   - Bypasses CDN restrictions by using the same server (i1-i4) as detected from thumbnails
   - Maintains consistent image quality by accessing original files
   - Handles server-side rate limiting through retry mechanisms

### Image Gallery Extraction
The script uses a multi-step process to locate and download images:

1. **Initial Page Analysis**
   ```python
   # Fetch and parse the manga page
   response = await client.get(url)
   soup = BeautifulSoup(response.text, 'html.parser')
   ```

2. **Pattern Discovery**
   - Locates thumbnail images in the gallery
   - Extracts the server directory and unique hash pattern
   - Example pattern: `i4.nhentaimg.com/016/xgy5ijcq0k/1.jpg`

3. **URL Construction**
   - Uses extracted patterns to build full-resolution image URLs
   - Maintains proper page ordering through sequential numbering
   - Handles different image extensions (jpg, png, gif, webp)

### Parallel Processing
The script utilizes asyncio for efficient downloading:

1. **Connection Pool Management**
   ```python
   limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
   timeout = httpx.Timeout(10.0, connect=5.0)
   transport = httpx.AsyncHTTPTransport(retries=3)
   ```

2. **Concurrent Downloads**
   - Implements async/await pattern for non-blocking I/O
   - Manages multiple simultaneous connections
   - Handles connection pooling and retries

### Error Handling
Robust error handling ensures reliable downloads:

1. **Network Resilience**
   - Automatic retries for failed requests
   - Connection pool management
   - Timeout handling

2. **Content Validation**
   - Verifies image integrity
   - Handles missing pages gracefully
   - Reports failed downloads for user awareness

## Usage

### Prerequisites
```bash
pip install -r requirements.txt
```

### Running the Script
1. Add manga URLs to `constants.txt`:
   ```
   https://nhentai.xxx/g/XXXXX/
   https://nhentai.xxx/g/YYYYY/
   ```

2. Run the script:
   ```bash
   python nhentai.xxx.py
   ```

### Output Structure
```
downloads/
├── XXXXX_MangaName1/
│   ├── 001.jpg
│   ├── 002.jpg
│   └── ...
└── YYYYY_MangaName2/
    ├── 001.jpg
    ├── 002.jpg
    └── ...
```

## Technical Details

### Dependencies
- httpx: Modern HTTP client with HTTP/2 support
- beautifulsoup4: HTML parsing and navigation
- asyncio: Asynchronous I/O operations

### Performance Optimization
- Implements connection pooling
- Uses HTTP/2 for multiplexing
- Maintains persistent connections
- Implements proper error handling and retries

### Security Considerations
- Mimics legitimate browser behavior
- Implements rate limiting
- Uses proper HTTP headers
- Maintains session consistency

## Limitations
- Requires stable internet connection
- May be affected by server-side rate limiting
- Some manga may have missing pages due to server issues
- Download speed depends on server response times

## Future Improvements
- Implement resume capability for interrupted downloads
- Add support for custom download directories
- Enhance error reporting and logging
- Implement download queue management
- Add support for alternative image servers

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

Copyright (C) 2024  solveditnpc

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program comes with ABSOLUTELY NO WARRANTY. For details, see the GNU General Public License.

## Disclaimer
This script is for educational purposes only. Please respect the website's terms of service and use responsibly. Read the license for more information