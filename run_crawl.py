import os
import re
import json
import time
import socket
import ipaddress
import requests

from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
from collections import deque
from bs4 import BeautifulSoup


MAX_PAGES = 50
MAX_DEPTH = 2
USER_AGENT = "PYHUNTER-Crawler/1.0"


def validate_domain(value):
    value = value.strip()

    if "://" not in value:
        value = "https://" + value

    parsed = urlparse(value)
    host = parsed.hostname

    if not host or not re.fullmatch(
        r"[a-zA-Z0-9.-]+", host
    ):
        raise ValueError("Domain tidak valid")

    if "." not in host or ".." in host:
        raise ValueError("Domain tidak valid")

    # Pastikan domain mengarah ke IP publik
    try:
        addresses = socket.getaddrinfo(host, None)
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if not ip.is_global:
                raise ValueError(
                    "Domain bukan alamat IP publik"
                )
    except socket.gaierror:
        raise ValueError("Domain tidak dapat ditemukan")

    return host.lower()


def get_robots(session, base_url):
    robots_url = urljoin(base_url, "/robots.txt")

    parser = RobotFileParser()
    parser.set_url(robots_url)

    try:
        response = session.get(
            robots_url,
            timeout=10,
            allow_redirects=False
        )

        if response.status_code == 200:
            parser.parse(response.text.splitlines())
        else:
            parser.parse([])

    except requests.RequestException:
        parser.parse([])

    return parser


def crawl_website(domain):
    host = validate_domain(domain)
    base_url = "https://" + host + "/"

    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT
    })

    robots = get_robots(session, base_url)

    queue = deque([(base_url, 0)])
    visited = set()
    results = set()

    delay = robots.crawl_delay(USER_AGENT) or 1
    delay = max(1, min(delay, 5))

    while queue and len(visited) < MAX_PAGES:
        current_url, depth = queue.popleft()

        current_url, _ = urldefrag(current_url)

        if current_url in visited:
            continue

        parsed = urlparse(current_url)

        if parsed.hostname != host:
            continue

        if not robots.can_fetch(USER_AGENT, current_url):
            continue

        visited.add(current_url)

        try:
            response = session.get(
                current_url,
                timeout=10,
                allow_redirects=False
            )

            if response.status_code != 200:
                continue

            content_type = response.headers.get(
                "Content-Type", ""
            )

            if "text/html" not in content_type.lower():
                continue

            results.add(current_url)

            if depth >= MAX_DEPTH:
                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            for link in soup.find_all("a", href=True):
                next_url = urljoin(
                    current_url,
                    link["href"]
                )

                next_url, _ = urldefrag(next_url)
                next = urlparse(next_url)

                if next.scheme not in ("http", "https"):
                    continue

                if next.hostname != host:
                    continue

                if next_url not in visited:
                    queue.append((next_url, depth + 1))

        except requests.RequestException:
            continue

        time.sleep(delay)

    session.close()

    return sorted(results)


def main():
    domain = os.environ.get("TARGET_DOMAIN", "")

    if not domain:
        raise ValueError("TARGET_DOMAIN belum diisi")

    urls = crawl_website(domain)

    output = {
        "target": domain,
        "total": len(urls),
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "urls": urls
    }

    with open("results.json", "w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("Crawling selesai!")
    print("Jumlah URL:", len(urls))
    print("Hasil disimpan ke results.json")


if __name__ == "__main__":
    main()
