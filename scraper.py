#!/usr/bin/env python3
"""
Scraper module for extracting documentation and project information.
Supports scraping from local project files and remote URLs (with robots.txt compliance).
Used as part of the Aspire + Agents + Python pipeline for automated documentation generation.
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.robotparser
from pathlib import Path
from datetime import datetime


def read_local_file(path: str) -> str:
    """Read content from a local file."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def fetch_url(url: str, timeout: int = 10) -> str:
    """Fetch content from a URL with a basic User-Agent header."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AgentCampDocBot/1.0 (+https://github.com/davidop/agentcamp-madrid-2026)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def is_allowed_by_robots(url: str) -> bool:
    """Check whether the given URL is allowed to be scraped according to robots.txt."""
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch("AgentCampDocBot", url)
    except Exception:
        # If robots.txt is not accessible, allow scraping
        return True


def strip_html_tags(html: str) -> str:
    """Remove HTML tags and return plain text."""
    # Remove script and style elements
    html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)[^>]*>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove all remaining tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def scrape_url(url: str, respect_robots: bool = True) -> dict:
    """
    Scrape a URL and return structured data.

    Args:
        url: The URL to scrape.
        respect_robots: If True, check robots.txt before scraping.

    Returns:
        A dict with keys: url, title, text, timestamp, error (optional).
    """
    result = {"url": url, "title": "", "text": "", "timestamp": datetime.now().isoformat()}

    if respect_robots and not is_allowed_by_robots(url):
        result["error"] = f"Scraping not allowed by robots.txt for {url}"
        print(f"⚠️  {result['error']}")
        return result

    try:
        html = fetch_url(url)

        # Extract title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if title_match:
            result["title"] = strip_html_tags(title_match.group(1)).strip()

        result["text"] = strip_html_tags(html)
        print(f"✅ Scraped URL: {url} ({len(result['text'])} chars)")
    except Exception as exc:
        result["error"] = str(exc)
        print(f"❌ Error scraping {url}: {exc}")

    return result


def scrape_project_files(root_dir: str, extensions: list = None) -> list:
    """
    Walk a directory tree and extract content from source files.

    Args:
        root_dir: Root directory to scan.
        extensions: List of file extensions to include (e.g. ['.cs', '.py']).
                    Defaults to common source/config extensions.

    Returns:
        List of dicts with keys: path, extension, content, size.
    """
    if extensions is None:
        extensions = [".cs", ".py", ".json", ".md", ".yaml", ".yml", ".csproj", ".sln"]

    results = []
    root = Path(root_dir)

    # Directories to skip
    skip_dirs = {"bin", "obj", "node_modules", ".git", ".vs", ".vscode", "__pycache__"}

    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        # Skip ignored directories
        if any(part in skip_dirs for part in file_path.parts):
            continue
        if file_path.suffix.lower() not in extensions:
            continue

        try:
            content = read_local_file(str(file_path))
            results.append({
                "path": str(file_path.relative_to(root)),
                "extension": file_path.suffix.lower(),
                "content": content,
                "size": len(content),
            })
        except Exception as exc:
            print(f"⚠️  Could not read {file_path}: {exc}")

    print(f"📂 Scanned {len(results)} files in {root_dir}")
    return results


def extract_aspire_metadata(project_files: list) -> dict:
    """
    Extract Aspire-specific metadata from scanned project files.

    Returns a dict with services, dependencies, resources, and endpoints.
    """
    metadata = {
        "services": [],
        "resources": [],
        "dependencies": [],
        "endpoints": [],
    }

    for file in project_files:
        content = file["content"]
        path = file["path"]

        # Detect AppHost Program.cs
        if "AppHost" in path and path.endswith("Program.cs"):
            active_lines = [l for l in content.splitlines() if not l.lstrip().startswith("//")]
            active_content = "\n".join(active_lines)

            # Services (AddProject) — deduplicated
            seen_services = set()
            for match in re.finditer(r'AddProject<Projects\.(\w+)>\("(\w+)"', active_content):
                key = match.group(2)
                if key not in seen_services:
                    seen_services.add(key)
                    metadata["services"].append({"class": match.group(1), "name": match.group(2)})

            # Resources (AddRedis, AddSqlServer, etc.) — deduplicated
            seen_resources = set()
            for match in re.finditer(r'\.(Add(?:Redis|SqlServer|RabbitMQ|Postgres|MongoDB|Kafka|Azure\w*|Nats|MySql|Oracle))\("(\w+)"', active_content):
                key = match.group(2)
                if key not in seen_resources:
                    seen_resources.add(key)
                    metadata["resources"].append({"type": match.group(1), "name": match.group(2)})

            # Build variable name → registered name mapping for dependency resolution
            var_to_name: dict = {}
            # AddProject variables: var apiService = builder.AddProject<...>("apiservice")
            for m in re.finditer(r'var\s+(\w+)\s*=.*?AddProject<Projects\.\w+>\("(\w+)"', active_content):
                var_to_name[m.group(1)] = m.group(2)
            # Resource variables: var cache = builder.AddRedis("cache")
            for m in re.finditer(r'var\s+(\w+)\s*=.*?\.Add(?:Redis|SqlServer|RabbitMQ|Postgres|MongoDB|Kafka|Azure\w*|Nats|MySql|Oracle)\("(\w+)"', active_content):
                var_to_name[m.group(1)] = m.group(2)
            # Database variables (may span multiple lines): .AddDatabase("productsDb")
            for m in re.finditer(r'var\s+(\w+)\s*=', active_content):
                var_name = m.group(1)
                # Look ahead up to 5 lines for .AddDatabase(...)
                snippet = active_content[m.start():m.start() + 300]
                db_m = re.search(r'\.AddDatabase\("(\w+)"', snippet)
                if db_m:
                    db_name = db_m.group(1)
                    var_to_name[var_name] = db_name
                    if db_name not in seen_resources:
                        seen_resources.add(db_name)
                        metadata["resources"].append({"type": "AddDatabase", "name": db_name})

            # Extract (from_service → to_resource/service) dependency edges
            # Parse each AddProject chain and its WithReference calls
            for m in re.finditer(
                r'(?:var\s+\w+\s*=\s*)?builder\.AddProject<Projects\.\w+>\("(\w+)"(.*?)(?=builder\.|$)',
                active_content,
                re.DOTALL,
            ):
                svc_name = m.group(1)
                chain = m.group(2)
                for ref_m in re.finditer(r'\.WithReference\((\w+)\)', chain):
                    dep_var = ref_m.group(1)
                    dep_name = var_to_name.get(dep_var, dep_var)
                    metadata["dependencies"].append({"from": svc_name, "to": dep_name})

        # API endpoints (MapGet / MapPost / MapPut / MapDelete)
        if path.endswith("Program.cs") and "AppHost" not in path:
            for match in re.finditer(r'\.(MapGet|MapPost|MapPut|MapDelete)\("([^"]+)"', content):
                metadata["endpoints"].append({"method": match.group(1).replace("Map", ""), "path": match.group(2), "file": path})

    return metadata


def save_scrape_results(results: list, output_path: str) -> None:
    """Save scrape results as JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved scrape results to {output_path}")


def main():
    """CLI entry point for the scraper."""
    import argparse

    parser = argparse.ArgumentParser(description="AgentCamp documentation scraper")
    parser.add_argument("--url", help="URL to scrape (respects robots.txt)")
    parser.add_argument("--project-dir", default="src", help="Local project directory to scan (default: src)")
    parser.add_argument("--output", default="docs/scrape-results.json", help="Output JSON file path")
    args = parser.parse_args()

    all_results = []

    # Scrape remote URL if provided
    if args.url:
        print(f"\n🌐 Scraping URL: {args.url}")
        url_data = scrape_url(args.url)
        all_results.append(url_data)

    # Always scan local project files
    project_root = os.path.join(os.path.dirname(__file__), args.project_dir)
    if os.path.isdir(project_root):
        print(f"\n📁 Scanning project files in: {project_root}")
        project_files = scrape_project_files(project_root)
        metadata = extract_aspire_metadata(project_files)
        all_results.append({
            "type": "project_scan",
            "root": args.project_dir,
            "file_count": len(project_files),
            "metadata": metadata,
            "timestamp": datetime.now().isoformat(),
        })
        print(f"🏗️  Found {len(metadata['services'])} services, {len(metadata['resources'])} resources, {len(metadata['endpoints'])} endpoints")

    # Save results
    output_path = os.path.join(os.path.dirname(__file__), args.output)
    save_scrape_results(all_results, output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
