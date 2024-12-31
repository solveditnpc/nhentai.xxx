# Nhentai.xxx Manga Downloader
## Installation and usage youtube video:
## Overview
This Python script enables downloading manga from nhentai.xxx through advanced web scraping techniques. Unlike nhentai.net which provides a public API, nhentai.xxx implements various anti-scraping measures including JavaScript-based page rendering and encrypted image galleries. This script successfully bypasses these protections using sophisticated pattern matching and direct image server access. Additionally, it now features automatic PDF generation, converting downloaded manga images into a single, easily readable PDF file.

## Installation Guide

### Windows Installation

1. **System Requirements**:
   - Windows 10 or later (64-bit recommended)
   - Internet connection for downloading packages

2. **Installing Python**:
   - Visit [python.org](https://www.python.org/downloads/)
   - Download the latest Python 3.8+ installer, recommended Python 3.10.0 for no installation issues
   - Run the installer with these important steps:
     1. Check "Add Python to PATH"
     2. Choose "Customize installation"
     3. Enable all optional features
     4. Set installation path (e.g., `C:\Python3`)

3. **Setting up the Development Environment**:
   ```cmd
   # Open Command Prompt as Administrator

   # Verify Python installation
   python --version
   pip --version

   # Create a project directory
   mkdir C:\manga-downloader
   cd C:\manga-downloader

   # Create and activate virtual environment
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Installing the Project**:
   - Download the project ZIP from GitHub
   - Extract to `C:\manga-downloader`
   - Install dependencies:
     ```cmd
     pip install -r requirements.txt
     ```

### Linux Installation

1. **System Requirements**:
   - Python 3.8 or higher
   - pip (Python package manager)
   - git (for cloning the repository)

2. **Installing System Dependencies**:
   ```bash
   # For Ubuntu/Debian-based systems
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git

   # For Fedora
   sudo dnf install python3 python3-pip git

   # For Arch Linux
   sudo pacman -S python python-pip git
   ```

3. **Setting up the Project**:
   ```bash
   # Clone the repository
   git clone https://github.com/solveditnpc/nhentai.xxx.git
   cd nhentai.xxx

   # Create a virtual environment
   python3 -m venv venv

   # Activate the virtual environment
   source venv/bin/activate

   # Install project dependencies
   pip install -r requirements.txt
   ```

4. **Verifying Installation**:
   ```bash
   # Check Python version
   python3 --version

   # Verify pip installation
   pip --version
   ```

## Key Features
- Downloads complete manga chapters with correct page ordering
- Saves manga in organized folders with format: `mangaID_mangaName`
- Handles anti-scraping protections without using Selenium or browser automation
- Supports batch downloading through a constants.txt file
- Implements parallel downloads using asyncio for better performance
- Maintains proper HTTP headers to mimic browser behavior
- **NEW**: Automatically generates PDF files for downloaded manga


## Usage Guide

### Basic Configuration

1. **Setting up URLs**:
   - Locate `constants.txt` in your project directory
   - Add manga URLs in the following format:
     ```
     https://nhentai.xxx/g/XXXXX/
     https://nhentai.xxx/g/YYYYY/
     ```
   - Each URL should be on a new line
   - URLs must be complete (including https://)
   - Only nhentai.xxx URLs are supported

2. **Running the Script**:
   ```bash
   # Windows
   python project.py
   ```
   
   ```bash
   # Linux
   python3 project.py
   ```


### Output Structure and PDF Generation

The script creates a well-organized output structure:
```
downloads/
├── XXXXX_MangaName1/
│   ├── 001.jpg
│   ├── 002.jpg
│   ├── ...
│   └── MangaName1.pdf    # Automatically generated PDF
└── YYYYY_MangaName2/
    ├── 001.jpg
    ├── 002.jpg
    ├── ...
    └── MangaName2.pdf    # Automatically generated PDF
```

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

### PDF Generation Features

1. **Automatic Processing**:
   - PDFs are generated automatically after all images are downloaded
   - No manual intervention required
   - Maintains original image quality
   - Pages are correctly ordered in the PDF

2. **File Organization**:
   - PDF files are named after the manga title
   - Stored in the same directory as the images
   - Easy to locate and access
   - Original images are preserved

3. **Quality Control**:
   - High-quality image conversion
   - Maintains aspect ratios
   - Optimized file size
   - Preserves image clarity

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

## Troubleshooting Guide

### Installation Issues

1. **Linux-specific**:
   - Permission errors: Use `sudo` for system-wide installations
   - Missing packages: Install build essentials
     ```bash
     sudo apt install build-essential python3-dev
     ```
   - Virtual environment issues:
     ```bash
     python3 -m pip install --user virtualenv
     ```

2. **Windows-specific**:
   - PATH issues: Manually add Python to system PATH
   - Permission errors: Run CMD as Administrator
   - SSL errors: Install Windows certificates
     ```cmd
     python -m pip install --upgrade certifi
     ```

### Download and PDF Issues

1. **Download Problems**:
   - Check internet connection
   - Verify URL format in constants.txt
   - Ensure sufficient disk space
   - Check console for error messages

2. **PDF Generation**:
   - Memory issues: Close other applications
   - File permission errors: Check folder permissions
   - Image conversion errors: Verify image files
   - PDF quality issues: Check source image quality

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