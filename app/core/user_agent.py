import re


def parse_user_agent(ua: str | None) -> dict[str, str | None]:
    if not ua:
        return {"browser": None, "browser_version": None, "os": None, "device_type": None}

    ua_lower = ua.lower()

    browser = None
    browser_version = None
    os_name = None
    device_type = "desktop"

    if "mobile" in ua_lower or "android" in ua_lower and "mobile" in ua_lower:
        device_type = "mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        device_type = "tablet"

    if "msie" in ua_lower or "trident" in ua_lower:
        browser = "Internet Explorer"
        m = re.search(r"MSIE\s+(\d+[.\d]*)", ua)
        if m:
            browser_version = m.group(1)
    elif "edg/" in ua_lower:
        browser = "Edge"
        m = re.search(r"Edg/(\d+[.\d]*)", ua)
        if m:
            browser_version = m.group(1)
    elif "firefox/" in ua_lower:
        browser = "Firefox"
        m = re.search(r"Firefox/(\d+[.\d]*)", ua)
        if m:
            browser_version = m.group(1)
    elif "chrome/" in ua_lower and "edge" not in ua_lower:
        browser = "Chrome"
        m = re.search(r"Chrome/(\d+[.\d]*)", ua)
        if m:
            browser_version = m.group(1)
    elif "safari/" in ua_lower:
        browser = "Safari"
        m = re.search(r"Version/(\d+[.\d]*)", ua)
        if m:
            browser_version = m.group(1)

    if "windows" in ua_lower:
        os_name = "Windows"
    elif "mac os" in ua_lower or "macintosh" in ua_lower:
        os_name = "macOS"
    elif "linux" in ua_lower:
        os_name = "Linux"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "ios" in ua_lower or "iphone" in ua_lower or "ipad" in ua_lower:
        os_name = "iOS"

    return {
        "browser": browser,
        "browser_version": browser_version,
        "os": os_name,
        "device_type": device_type,
    }


def extract_domain(url: str | None) -> str | None:
    if not url:
        return None
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1) if m else None
