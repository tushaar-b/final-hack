import pandas as pd
import requests
import io

def test_fetch_universe():
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    print(f"Fetching from: {url}")
    
    # Use requests to get the content with headers
    session = requests.Session()
    # Initial request to get cookies
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    
    # Now get the CSV
    response = session.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    df = pd.read_csv(io.StringIO(response.text))
    
    print("\nCSV Headers parsed:")
    print(df.columns.tolist())
    print(f"\nTotal rows: {len(df)}")
    
    if len(df) > 0:
        print("\nFirst 3 rows (subset):")
        print(df.head(3))

if __name__ == "__main__":
    test_fetch_universe()
