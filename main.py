import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://streambtw.com"
PLAYLIST_FILE = "streambtw.m3u"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/133.0.0.0",
    "Referer": BASE_URL + "/",
    "Origin": BASE_URL,
    "Accept": "*/*",
}

def get_match_links():
    """Scrape the main page to extract match titles, logos, and iframe links."""
    response = requests.get(BASE_URL, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to load {BASE_URL}: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    matches = []

    for card in soup.find_all("div", class_="card"):
        title_tag = card.find("h5", class_="card-title")
        match_title = title_tag.text.strip() if title_tag else "Unknown Match"

        logo_tag = card.find("img", class_="league-logo")
        logo_url = logo_tag["src"] if logo_tag else "https://via.placeholder.com/150"

        link_tag = card.find("a", href=True, class_="btn")
        if link_tag:
            iframe_url = link_tag["href"]
            full_url = iframe_url if iframe_url.startswith("http") else BASE_URL + iframe_url
            matches.append((match_title, logo_url, full_url))

    return matches

def extract_m3u8_from_iframe(iframe_url):
    """Scrape an iframe page to find m3u8 links."""
    response = requests.get(iframe_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to load {iframe_url}: {response.status_code}")
        return None

    m3u8_match = re.search(r'(https?://[^\s]+\.m3u8)', response.text)
    return m3u8_match.group(1) if m3u8_match else None

def generate_m3u_playlist(streams):
    """Generate an M3U playlist string."""
    m3u_content = "#EXTM3U\n\n"
    
    for title, logo, m3u8_url in streams:
        m3u_content += f'''#EXTINF:-1 tvg-logo="{logo}" group-title="StreamBTW",{title}
#EXTVLCOPT:http-origin={BASE_URL}
#EXTVLCOPT:http-referrer={BASE_URL}/
#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}
{m3u8_url}\n\n'''

    return m3u_content

if __name__ == "__main__":
    print("Fetching match links...")
    match_links = get_match_links()

    streams = []

    if not match_links:
        print("No matches found.")
    else:
        print(f"Found {len(match_links)} matches. Checking for m3u8 streams...\n")
        for match_title, logo, iframe in match_links:
            print(f"Checking: {match_title} -> {iframe}")
            m3u8_link = extract_m3u8_from_iframe(iframe)
            if m3u8_link:
                streams.append((match_title, logo, m3u8_link))
                print(f"Found M3U8: {m3u8_link}\n")
            else:
                print("No M3U8 link found.\n")

    if streams:
        playlist_content = generate_m3u_playlist(streams)
        with open(PLAYLIST_FILE, "w", encoding="utf-8") as file:
            file.write(playlist_content)
        print(f"Playlist saved as {PLAYLIST_FILE}")
    else:
        print("No streams found. Playlist not created.")
