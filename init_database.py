"""
Database initialization script for PostgreSQL backend.

This script:
1. Checks PostgreSQL connection
2. Creates database if it doesn't exist
3. Initializes all tables and indexes
4. Validates the setup

Usage:
    python init_database.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_postgres_available():
    """Check if psycopg2 is installed."""
    try:
        import psycopg2
        return True
    except ImportError:
        print("❌ psycopg2 not installed")
        print("📦 Install with: pip install psycopg2-binary")
        return False


def check_postgres_configured():
    """Check if PostgreSQL is configured."""
    use_postgres = os.getenv('USE_POSTGRES', 'false').lower() == 'true'

    if not use_postgres:
        print("⚠️  PostgreSQL is not enabled")
        print("💡 Set USE_POSTGRES=true in your .env file to enable")
        return False

    # Check if connection string or individual params are set
    has_url = bool(os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL'))
    has_params = all([
        os.getenv('POSTGRES_USER'),
        os.getenv('POSTGRES_PASSWORD'),
        os.getenv('POSTGRES_HOST'),
        os.getenv('POSTGRES_DB')
    ])

    if not (has_url or has_params):
        print("❌ PostgreSQL connection not configured")
        print("💡 Set DATABASE_URL or individual POSTGRES_* variables in .env")
        return False

    return True


def test_connection():
    """Test PostgreSQL connection."""
    try:
        from src.database import PostgresBackend

        print("\n🔌 Testing PostgreSQL connection...")
        backend = PostgresBackend()

        # Try to get a connection
        with backend.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()

        print(f"✅ Connected to PostgreSQL")
        print(f"   Version: {version.split(',')[0]}")

        return backend

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


def initialize_database(backend):
    """Initialize database tables."""
    try:
        print("\n📊 Initializing database tables...")
        backend.initialize_database()
        print("✅ Database tables created successfully")

        # Verify tables
        with backend.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()

        print(f"\n📋 Created tables:")
        for table in tables:
            print(f"   • {table}")

        return True

    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False


def show_connection_info():
    """Display connection information."""
    print("\n📝 Connection Information:")

    # Get connection parameters
    database_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')

    if database_url:
        # Mask password in URL
        masked_url = database_url
        if '@' in masked_url:
            parts = masked_url.split('@')
            creds = parts[0].split('://')
            if len(creds) > 1 and ':' in creds[1]:
                user, _ = creds[1].split(':', 1)
                masked_url = f"{creds[0]}://{user}:****@{parts[1]}"

        print(f"   Connection String: {masked_url}")
    else:
        user = os.getenv('POSTGRES_USER', 'postgres')
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DB', 'rag_chatbot')

        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Database: {database}")
        print(f"   User: {user}")


def main():
    """Main initialization flow."""
    print("=" * 80)
    print("PostgreSQL Database Initialization")
    print("=" * 80)

    # Step 1: Check if psycopg2 is installed
    if not check_postgres_available():
        sys.exit(1)

    # Step 2: Check if PostgreSQL is configured
    if not check_postgres_configured():
        print("\n💡 To enable PostgreSQL:")
        print("   1. Install PostgreSQL (https://www.postgresql.org/download/)")
        print("   2. Create a database: createdb rag_chatbot")
        print("   3. Set USE_POSTGRES=true in .env")
        print("   4. Configure connection in .env (see .env.example)")
        print("   5. Run this script again")
        sys.exit(1)

    # Step 3: Show connection info
    show_connection_info()

    # Step 4: Test connection
    backend = test_connection()
    if not backend:
        print("\n💡 Check your connection settings in .env")
        sys.exit(1)

    # Step 5: Initialize database
    if not initialize_database(backend):
        backend.close()
        sys.exit(1)

    # Success
    print("\n" + "=" * 80)
    print("🎉 Database initialization complete!")
    print("=" * 80)
    print("\n✅ Your RAG chatbot is now configured with PostgreSQL")
    print("✅ Sessions and conversations will be persisted")
    print("✅ You can restore previous sessions in the UI")
    print("\n💡 Run the agent UI to start chatting:")
    print("   streamlit run run_agent_ui.py")

    backend.close()


if __name__ == "__main__":
    main()
