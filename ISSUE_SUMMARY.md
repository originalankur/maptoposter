# SSL Certificate Issue - Summary & Resolution

## Issue Overview
When running the maptoposter script on macOS with Python from python.org, SSL certificate verification errors occur during geocoding:

```
SSLError: certificate verify failed: unable to get local issuer certificate
```

## Root Cause
Python on macOS doesn't use system root certificates by default - it requires its own certificate bundle to be installed via the included installer script.

## Solution Implemented

### Pull Request Created
**PR #166**: [Add --ignore-ssl-errors flag and SSL certificate documentation](https://github.com/originalankur/maptoposter/pull/166)

**Branch**: `philipdenys:fix/add-ssl-ignore-option`

### Changes Made

1. **New `--ignore-ssl-errors` Command-Line Flag**
   - Allows bypassing SSL verification for development/testing
   - Shows warning when active
   - NOT recommended for production

2. **Implementation Details**
   - Monkey-patches `ssl._create_default_https_context` globally
   - Lazy-loads geopy module after SSL context is patched
   - Disables urllib3 warnings
   
3. **Documentation**
   - Created `SSL_CERTIFICATE_ISSUE.md` with comprehensive guide
   - Explains the recommended fix (Install Certificates.command)
   - Documents the workaround flag with security warnings

## Recommended Fix for Users

The BEST solution is to install Python's SSL certificates:

```bash
/Applications/Python\ 3.11/Install\ Certificates.command
```

This installs the `certifi` package and creates necessary symbolic links.

## Temporary Workaround

For testing/development only:

```bash
python3 create_map_poster.py --ignore-ssl-errors -c Antwerp -C Belgium -t japanese_ink -d 15000
```

⚠️ **Warning**: This disables certificate verification and should never be used in production!

## Repository Status

- **Fork**: https://github.com/philipdenys/maptoposter
- **Branch**: `fix/add-ssl-ignore-option`
- **Pull Request**: #166 to originalankur/maptoposter
- **Status**: Awaiting review

## Files Modified

1. `create_map_poster.py`
   - Added `--ignore-ssl-errors` argument
   - Moved geopy import to be lazy-loaded
   - Added SSL context patching logic
   - Added warning message

2. `SSL_CERTIFICATE_ISSUE.md` (new)
   - Comprehensive documentation
   - Problem description
   - Multiple solution paths
   - Security warnings

## Next Steps

1. Wait for maintainer review of PR #166
2. Address any feedback
3. Once merged, users can use either:
   - Install certificates (recommended)
   - Use --ignore-ssl-errors flag (development only)
