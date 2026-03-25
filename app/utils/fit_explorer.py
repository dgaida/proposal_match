import httpx
from bs4 import BeautifulSoup

def explore_fit():
    url = "https://fit.uni-kassel.de/home"
    print(f"Exploring {url}...")

    with httpx.Client() as client:
        response = client.get(url)
        print(f"Response Status: {response.status_code}")

        # Check for any interesting scripts or links
        soup = BeautifulSoup(response.content, "html.parser")
        scripts = soup.find_all("script")
        print(f"Found {len(scripts)} scripts.")
        for script in scripts:
            if script.get("src"):
                print(f"Script: {script.get('src')}")

        # Look for login forms or links
        links = soup.find_all("a")
        for link in links:
            if "login" in str(link).lower() or "anmelden" in str(link).lower():
                print(f"Possible Login Link: {link.get('href')}")

if __name__ == "__main__":
    explore_fit()
