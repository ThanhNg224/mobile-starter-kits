#!/usr/bin/env python3
"""Check the public repository links in Thanh's GitHub portfolio."""

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OWNER = "ThanhNg224"
API = "https://api.github.com"
REPO_LINK = re.compile(r"\]\(https://github\.com/(ThanhNg224/[\w.-]+)\)", re.IGNORECASE)
FEATURED = re.compile(r"^## Featured projects\s*\n(.*?)(?=^## |^<details>|\Z)", re.MULTILINE | re.DOTALL)


def github(path, accept="application/vnd.github+json"):
    request = Request(
        f"{API}/{path}",
        headers={"Accept": accept, "User-Agent": "mobile-starter-kits-portfolio-check"},
    )
    with urlopen(request, timeout=10) as response:
        return response.read()


def linked_repositories(name, featured_only=False):
    readme = github(f"repos/{OWNER}/{name}/readme", "application/vnd.github.raw+json").decode()
    if featured_only:
        section = FEATURED.search(readme)
        readme = section.group(1) if section else ""
    names = list(dict.fromkeys(REPO_LINK.findall(readme)))
    if not names:
        raise ValueError(f"No GitHub repository links found in {name}/README.md")
    return names


def check_repository(name):
    try:
        metadata = json.loads(github(f"repos/{name}"))
    except HTTPError as error:
        if error.code in (404, 410):
            return "UNAVAILABLE", "not accessible publicly"
        return "ERROR", f"GitHub API returned HTTP {error.code}"
    except (URLError, TimeoutError) as error:
        return "ERROR", f"network request failed ({error})"

    canonical = metadata["full_name"]
    if metadata["private"]:
        return "UNAVAILABLE", "private repository"
    if name.casefold() != canonical.casefold():
        return "REDIRECT", f"https://github.com/{canonical}"
    return "OK", metadata["html_url"]


def main():
    try:
        catalog = linked_repositories("mobile-starter-kits")
        featured = linked_repositories(OWNER, featured_only=True)
    except (URLError, TimeoutError, ValueError) as error:
        print(f"ERROR reading portfolio: {error}")
        return 1

    print(f"Checking {len(catalog)} starter links and {len(featured)} featured links.")
    names = dict.fromkeys(catalog + featured)
    results = [check_repository(name) for name in names]
    for name, (status, detail) in zip(names, results):
        print(f"{status:11} {name}  {detail}")
    return int(any(status != "OK" for status, _ in results))


if __name__ == "__main__":
    raise SystemExit(main())
