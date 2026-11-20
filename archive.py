import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = "https://iptv-epg.org/files/epg-gb.xml"
OUTPUT = Path("epg.xml")


def fetch_xml(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return ET.parse(response).getroot()


def parse_time(value):
    return datetime.strptime(
        value.strip(),
        "%Y%m%d%H%M%S %z"
    ).astimezone(timezone.utc)


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)
    future_limit = now + timedelta(days=14)

    fresh = fetch_xml(SOURCE)

    if OUTPUT.exists():
        old = ET.parse(OUTPUT).getroot()
    else:
        old = ET.Element("tv", fresh.attrib)

    channels = {}
    programmes = {}

    for root in (old, fresh):
        for channel in root.findall("channel"):
            channels[channel.get("id")] = channel

        for programme in root.findall("programme"):
            try:
                start = parse_time(programme.get("start"))
                stop = parse_time(programme.get("stop"))
            except Exception:
                continue

            if stop < cutoff or start > future_limit:
                continue

            key = (
                programme.get("channel"),
                programme.get("start"),
                programme.get("stop")
            )

            programmes[key] = programme

    output = ET.Element("tv", fresh.attrib)

    for channel in channels.values():
        output.append(channel)

    for programme in sorted(
        programmes.values(),
        key=lambda p: (p.get("start", ""), p.get("channel", ""))
    ):
        output.append(programme)

    ET.indent(output, space="  ")

    ET.ElementTree(output).write(
        OUTPUT,
        encoding="utf-8",
        xml_declaration=True
    )

    print(f"Saved {len(programmes)} programmes")


if __name__ == "__main__":
    main()
