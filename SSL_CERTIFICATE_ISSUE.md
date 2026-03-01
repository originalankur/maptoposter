# SSL Certificate Verification Issue

## Problem

When running the map poster generator on macOS with Python installed from python.org, you may encounter SSL certificate verification errors:

```
SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1002)'))
```

## Root Cause

Python on macOS does not use the system's root certificates by default. Instead, it requires its own set of certificates to be installed.

## Solution

### Option 1: Install Python Certificates (Recommended)

Run the certificate installer that comes with Python:

```bash
/Applications/Python\ 3.11/Install\ Certificates.command
```

Replace `3.11` with your Python version. This command installs the `certifi` package and creates the necessary symbolic links.

### Option 2: Use the --ignore-ssl-errors Flag (Not Recommended for Production)

For development/testing purposes only:

```bash
python3 create_map_poster.py --ignore-ssl-errors -c "City Name" -C "Country" -t theme_name
```

**⚠️ Warning:** This option disables SSL certificate verification and should never be used in production environments or when handling sensitive data.

## Implementation Details

The `--ignore-ssl-errors` flag works by:
1. Monkey-patching `ssl._create_default_https_context` to use `ssl._create_unverified_context`
2. Disabling urllib3 SSL warnings
3. Lazy-loading the geopy module after the SSL context has been patched

## References

- [Python SSL Certificate Verification](https://docs.python.org/3/library/ssl.html)
- [Python on macOS Certificate Issues](https://bugs.python.org/issue28150)
- [Certifi Package](https://github.com/certifi/python-certifi)
