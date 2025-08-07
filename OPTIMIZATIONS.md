# nhentai Optimizations Summary

This document summarizes the optimizations made to the nhentai project by billsargent.

## 1. HTTP Request Improvements

- Added `curl_cffi` with Chrome browser emulation for better Cloudflare bypass
- Updated `async_request` to use `curl_cffi` for consistent handling with the synchronous version
- Added fallback mechanism to `httpx` if `curl_cffi` fails

## 2. Caching System

- Added caching for API requests to reduce redundant network calls
- Created command-line options to control cache behavior:
  - `--clean-cache`: Clear cached responses
  - `--cache-timeout`: Set cache lifetime in seconds

## 3. Resource Management

- Improved `CompressedDownloader` class with proper resource cleanup
- Added context managers and error handling
- Fixed potential memory leaks in file handling

## 4. Memory Optimization

- Modified PDF generation to process images in chunks rather than loading all at once
- Increased chunk size for streaming downloads for better efficiency
- Added more efficient BytesIO handling

## 5. Error Handling & Retry Logic

- Implemented adaptive rate limiting based on server responses
- Added exponential backoff with jitter for retries
- Improved error reporting and recovery mechanisms

## 6. File I/O Safety

- Added atomic write operations to prevent corrupted files
- Added file integrity checking
- Implemented safe filename handling

## 7. Code Structure

- Created helper modules for specific functionality
- Added proper documentation and comments
- Improved exception handling throughout the codebase

## 8. Performance Improvements

- Optimized chunk sizes for file transfers
- Added concurrent downloads with better resource management
- Implemented more efficient file compression

## 9. Dependencies

- Updated dependencies to latest compatible versions
- Added requirements.txt for easier installation outside of Poetry

## Usage Tips

1. Use the cache system to reduce API calls:
   ```
   nhentai --search "keyword" --cache-timeout 86400
   ```

2. Clear cache if needed:
   ```
   nhentai --clean-cache
   ```

3. Configure browser emulation by setting cookie and user-agent:
   ```
   nhentai --cookie "your-cookie-string" --useragent "Chrome/110.0.0.0"
   ```

4. For large downloads, adjust threads for optimal performance:
   ```
   nhentai --id 123456 --threads 10
   ```

5. For PDF generation with large galleries, the chunked processing will automatically reduce memory usage.
