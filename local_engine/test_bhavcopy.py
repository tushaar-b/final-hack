from nselib import capital_market

def test_bhavcopy():
    # Use a recent past trading date to guarantee availability
    date_str = '17-06-2026'
    print(f"Testing nselib bhavcopy download for {date_str}...")
    try:
        df = capital_market.bhav_copy_with_delivery(date_str)
        print(f"Success! Downloaded {len(df)} rows.")
        print("\nColumns found:")
        print(df.columns.tolist())
    except Exception as e:
        print(f"Error fetching bhavcopy: {e}")

if __name__ == "__main__":
    test_bhavcopy()
