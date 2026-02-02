#!/usr/bin/env python3
"""
                    Search Term Analyzer - Find Heavy DB Queries

Usage:
    python search_analyzer.py --target "https://target.com" --terms terms.txt
    python search_analyzer.py --target "https://target.com" --auto
"""

import requests
import time
import sys
import argparse
import re
from collections import defaultdict
import urllib3
urllib3.disable_warnings()

# Colors
R = '\033[91m'
G = '\033[92m'
Y = '\033[93m'
C = '\033[96m'
B = '\033[1m'
M = '\033[95m'
X = '\033[0m'

if sys.platform == 'win32':
    import os
    os.system('color')

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_session(cookies=None):
    """Create session"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })
    if cookies:
        for k, v in cookies.items():
            session.cookies.set(k, v)
    return session


def parse_cookies(cookie_string):
    """Parse cookies"""
    cookies = {}
    if not cookie_string:
        return cookies
    for item in cookie_string.replace('\n', ';').split(';'):
        item = item.strip()
        if '=' in item:
            k, v = item.split('=', 1)
            cookies[k.strip()] = v.strip()
    return cookies


def load_terms_from_file(filepath):
    """Load terms from file, ignoring comments and empty lines"""
    terms = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#') and not line.startswith('─') and not line.startswith('═'):
                    terms.append(line)
    except Exception as e:
        print(f"{R}[-] Error loading file: {e}{X}")
    return terms


def extract_words_from_html(html, min_length=4):
    """Extract potential search terms from HTML content"""
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<[^>]+>', ' ', html)
    html = re.sub(r'&[a-z]+;', ' ', html)
    
    words = re.findall(r'\b[a-zA-Z0-9àèéìòùçäöüßñ]{%d,}\b' % min_length, html.lower())
    
    word_count = defaultdict(int)
    for word in words:
        word_count[word] += 1
    
    stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'are', 'from', 'have', 'has',
                 'been', 'will', 'would', 'could', 'should', 'their', 'there', 'what', 'when',
                 'where', 'which', 'who', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
                 'most', 'other', 'some', 'such', 'than', 'too', 'very', 'just', 'come', 'made',
                 'about', 'after', 'also', 'back', 'because', 'before', 'being', 'between'}
    
    return {word: count for word, count in word_count.items() 
            if word not in stopwords and count >= 2}


def auto_discover_terms(session, target_base, max_terms=50):
    """Auto-discover search terms from site content"""
    print(f"{Y}[*] Auto-discovering search terms...{X}")
    
    all_words = defaultdict(int)
    urls_to_check = [
        target_base,
        f"{target_base}/feed/",
        f"{target_base}/wp-json/wp/v2/posts?per_page=20",
        f"{target_base}/wp-json/wp/v2/categories?per_page=50",
        f"{target_base}/wp-json/wp/v2/tags?per_page=50",
    ]
    
    for url in urls_to_check:
        try:
            print(f"{C}    Fetching: {url[:60]}...{X}")
            r = session.get(url, timeout=30, verify=False)
            if r.status_code == 200:
                words = extract_words_from_html(r.text)
                for word, count in words.items():
                    all_words[word] += count
        except Exception as e:
            print(f"{Y}    Error: {e}{X}")
    
    sorted_words = sorted(all_words.items(), key=lambda x: x[1], reverse=True)
    terms = [word for word, count in sorted_words[:max_terms]]
    
    print(f"{G}[+] Discovered {len(terms)} potential terms{X}\n")
    return terms


def test_search_term(session, target_base, term, samples=3):
    """Test a search term and measure response time"""
    times = []
    results_count = 0
    status = 200
    
    for i in range(samples):
        try:
            url = f"{target_base}/?s={term}+{int(time.time())}"
            start = time.time()
            r = session.get(url, timeout=60, verify=False)
            elapsed = time.time() - start
            times.append(elapsed)
            status = r.status_code
            
            if 'search results' in r.text.lower() or 'risultati' in r.text.lower():
                match = re.search(r'(\d+)\s*(results?|risultat)', r.text.lower())
                if match:
                    results_count = int(match.group(1))
            
            time.sleep(0.2)
        except Exception as e:
            times.append(60.0)
    
    avg_time = sum(times) / len(times) if times else 0
    return {
        "term": term,
        "avg_time": avg_time,
        "min_time": min(times) if times else 0,
        "max_time": max(times) if times else 0,
        "results": results_count,
        "status": status
    }


def main():
    parser = argparse.ArgumentParser(
        description="WPStabber Search Analyzer - Find Heavy DB Query Terms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python search_analyzer.py -t "https://target.com" --terms search_terms_multilingual.txt
    python search_analyzer.py -t "https://target.com" --auto
    python search_analyzer.py -t "https://target.com" --auto -o heavy_terms.txt
        """
    )
    parser.add_argument("--target", "-t", required=True, help="Target URL")
    parser.add_argument("--terms", help="Terms file or comma-separated list")
    parser.add_argument("--auto", action="store_true", help="Auto-discover terms from site")
    parser.add_argument("--cookies", "-c", help="Cookies for CF bypass")
    parser.add_argument("--samples", type=int, default=3, help="Samples per term (default: 3)")
    parser.add_argument("--top", type=int, default=20, help="Show top N heaviest terms")
    parser.add_argument("--output", "-o", help="Save heavy terms to file")
    args = parser.parse_args()
    
    target_base = args.target.rstrip("/")
    cookies = parse_cookies(args.cookies) if args.cookies else {}
    session = get_session(cookies)
    
    print(f"""
{R}
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
{X}{C}                           Search Term Analyzer
                           Find Heavy DB Queries{X}

{B}Target:{X} {target_base}
""")
    
    # Get terms
    terms = []
    
    if args.auto:
        terms = auto_discover_terms(session, target_base)
    elif args.terms:
        if args.terms.endswith('.txt'):
            terms = load_terms_from_file(args.terms)
            if terms:
                print(f"{G}[+] Loaded {len(terms)} terms from {args.terms}{X}\n")
        else:
            terms = [t.strip() for t in args.terms.split(',') if t.strip()]
            print(f"{G}[+] Testing {len(terms)} terms{X}\n")
    else:
        print(f"{R}[-] Provide --terms or use --auto{X}")
        sys.exit(1)
    
    if not terms:
        print(f"{R}[-] No terms to test{X}")
        sys.exit(1)
    
    # Test baseline
    print(f"{Y}[*] Testing baseline (homepage)...{X}")
    try:
        start = time.time()
        r = session.get(target_base, timeout=30, verify=False)
        baseline = time.time() - start
        print(f"{G}[+] Baseline: {baseline:.3f}s (status: {r.status_code}){X}\n")
        
        if r.status_code == 403:
            print(f"{R}[-] CF blocking - provide cookies with -c{X}")
            sys.exit(1)
    except Exception as e:
        print(f"{R}[-] Error: {e}{X}")
        sys.exit(1)
    
    # Test each term
    print(f"{Y}[*] Testing {len(terms)} search terms ({args.samples} samples each)...{X}")
    print(f"{B}{'Term':<30} {'Avg':>8} {'Min':>8} {'Max':>8} {'Status':>8}{X}")
    print(f"{'─'*70}")
    
    results = []
    
    for i, term in enumerate(terms):
        result = test_search_term(session, target_base, term, args.samples)
        results.append(result)
        
        avg = result['avg_time']
        if avg > baseline * 5:
            color = R
        elif avg > baseline * 2:
            color = Y
        else:
            color = G
        
        status_color = R if result['status'] != 200 else G
        
        # Truncate long terms for display
        display_term = term[:28] + ".." if len(term) > 30 else term
        
        sys.stdout.write(
            f"{color}{display_term:<30}{X} "
            f"{avg:>7.2f}s "
            f"{result['min_time']:>7.2f}s "
            f"{result['max_time']:>7.2f}s "
            f"{status_color}{result['status']:>8}{X}\n"
        )
        sys.stdout.flush()
    
    # Sort by average time
    results.sort(key=lambda x: x['avg_time'], reverse=True)
    
    # Show top heavy terms
    print(f"""
{R}
    ╔╗ ╦  ╔═╗╔═╗╔╦╗  ╔╦╗╔═╗╦═╗╔╦╗╔═╗
    ╠╩╗║  ║ ║║ ║ ║║   ║ ║╣ ╠╦╝║║║╚═╗
    ╚═╝╩═╝╚═╝╚═╝═╩╝   ╩ ╚═╝╩╚═╩ ╩╚═╝
{X}""")
    
    print(f"{B}{'Rank':<6} {'Term':<30} {'Avg Time':>10} {'vs Baseline':>12}{X}")
    print(f"{'─'*62}")
    
    heavy_terms = []
    
    for i, result in enumerate(results[:args.top]):
        ratio = result['avg_time'] / baseline if baseline > 0 else 0
        
        if ratio > 5:
            color = R
            label = "☠️  LETHAL"
        elif ratio > 3:
            color = R
            label = "🩸 HEAVY"
        elif ratio > 2:
            color = Y
            label = "⚠️  SLOW"
        else:
            color = G
            label = "✓ NORMAL"
        
        display_term = result['term'][:28] + ".." if len(result['term']) > 30 else result['term']
        print(f"{i+1:<6} {color}{display_term:<30}{X} {result['avg_time']:>9.2f}s {ratio:>8.1f}x {label}")
        
        if ratio > 2:
            heavy_terms.append(result['term'])
    
    # Summary
    print(f"\n{C}{'─'*62}{X}")
    print(f"{B}Baseline:{X}      {baseline:.3f}s")
    print(f"{B}Terms Tested:{X}  {len(results)}")
    print(f"{B}Heavy Terms:{X}   {len(heavy_terms)} (>2x baseline)")
    
    if heavy_terms:
        print(f"\n{Y}Recommended for stress test:{X}")
        print(f"{G}{','.join(heavy_terms[:15])}{X}")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            for term in heavy_terms:
                f.write(f"{term}\n")
        print(f"\n{G}[+] Saved {len(heavy_terms)} heavy terms to {args.output}{X}")
    
    print()


if __name__ == "__main__":
    main()
