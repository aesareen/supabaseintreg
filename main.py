from supabase import create_client, Client
from dotenv import load_dotenv
import os
import polars as pl

load_dotenv()

# Replace these with your actual Supabase project URL and API key
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_API_KEY = os.getenv('SUPABASE_KEY')

def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_API_KEY)

def select_rows_from_table(client: Client, table_name: str) -> dict[str, str | int]:
    response = client.table(table_name).select("*").limit(50).execute()
    return response.data

# Example usage
if __name__ == "__main__":
    supabase = get_supabase_client()
    print("Supabase client created:", supabase)

    print(f'Reading in Data and Loading in as Polars DataFrame.')
    rows = select_rows_from_table(supabase, "puffles")
    rows_as_df: pl.DataFrame = pl.DataFrame(rows)
    print(rows_as_df)
