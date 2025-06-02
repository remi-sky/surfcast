import os

def main():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    print("🚀 Supabase URL:", supabase_url)
    print("🔑 Supabase Service Key (first 6 chars):", supabase_key[:6] + "..." if supabase_key else "Missing")

if __name__ == "__main__":
    main()
