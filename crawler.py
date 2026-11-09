
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque


def crawl_website(domain, max_pages=50, max_depth=2):

    domain = domain.strip().lower()

    if "://" not in domain:
        domain = "https://" + domain

    parsed = urlparse(domain)

    if not parsed.hostname:
        raise ValueError("Domain tidak valid")

    host = parsed.hostname

    if not host or "." not in host:
        raise ValueError("Domain tidak valid")

    start_url = f"{parsed.scheme}://{host}/"

    session = requests.Session()
    session.headers.update({
        "User-Agent": "PYHUNTER-Crawler/1.0"
    })

    queue = deque([(start_url, 0)])
    visited = set()
    results = set()

    while queue and len(visited) < max_pages:

        current_url, depth = queue.popleft()

        current_url, _ = urldefrag(current_url)

        if current_url in visited:
            continue

        visited.add(current_url)

        try:
            response = session.get(
                current_url,
                timeout=10
            )

            if response.status_code != 200:
                continue

            content_type = response.headers.get(
                "Content-Type", ""
            )

            if "text/html" not in content_type:
                continue

            results.add(current_url)

            if depth >= max_depth:
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

                parsed_link = urlparse(next_url)

                if parsed_link.scheme not in ("http", "https"):
                    continue

                if parsed_link.hostname != host:
                    continue

                if next_url not in visited:
                    queue.append((
                        next_url,
                        depth + 1
                    ))

        except requests.RequestException:
            continue

    session.close()

    return sorted(results)
