#!/usr/bin/env python3
"""
Check which backend services are active in the RAG system.

Usage: python check_backend_status.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_postgres():
    """Check if PostgreSQL is configured and reachable."""
    use_postgres = os.getenv("USE_POSTGRES", "false").lower() == "true"
    database_url = os.getenv("DATABASE_URL")

    print("\n🗄️  PostgreSQL Status")
    print("=" * 50)
    print(f"   USE_POSTGRES: {use_postgres}")
    print(f"   DATABASE_URL configured: {'Yes' if database_url else 'No'}")

    if use_postgres and database_url:
        try:
            import psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"   ✅ Connected: {version.split(',')[0]}")

            # Check for tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            if tables:
                print(f"   Tables found: {', '.join([t[0] for t in tables])}")
            else:
                print("   ⚠️  No tables found - run init_database.py")

            conn.close()
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
    else:
        print("   ⚪ Not configured (using in-memory storage)")


def check_redis():
    """Check if Redis is configured and reachable."""
    use_redis = os.getenv("USE_REDIS_QUEUE", "false").lower() == "true"
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    print("\n🔴 Redis Status")
    print("=" * 50)
    print(f"   USE_REDIS_QUEUE: {use_redis}")
    print(f"   REDIS_URL: {redis_url}")

    if use_redis:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            info = r.info()
            print(f"   ✅ Connected: Redis {info['redis_version']}")
            print(f"   Uptime: {info['uptime_in_seconds']} seconds")
            print(f"   Used memory: {info['used_memory_human']}")

            # Check for queues
            keys = r.keys("rag:queue:*")
            if keys:
                print(f"   Queues found: {len(keys)}")
            else:
                print("   No queues found yet")
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
    else:
        print("   ⚪ Not configured (no background queue)")


def check_pinecone():
    """Check if Pinecone is configured."""
    use_pinecone = os.getenv("USE_PINECONE", "false").lower() == "true"
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "rag-agent")

    print("\n🌲 Pinecone Status")
    print("=" * 50)
    print(f"   USE_PINECONE: {use_pinecone}")
    print(f"   API Key configured: {'Yes' if api_key else 'No'}")

    if use_pinecone and api_key:
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=api_key)
            indexes = pc.list_indexes()

            if any(idx.name == index_name for idx in indexes):
                index = pc.Index(index_name)
                stats = index.describe_index_stats()
                print(f"   ✅ Connected to index: {index_name}")
                print(f"   Total vectors: {stats.total_vector_count}")
                print(f"   Dimension: {stats.dimension}")
                print(f"   Namespaces: {list(stats.namespaces.keys()) if stats.namespaces else 'default'}")
            else:
                print(f"   ⚠️  Index '{index_name}' not found")
                print(f"   Available indexes: {[idx.name for idx in indexes]}")
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
    else:
        print("   ⚪ Not configured (using FAISS local)")


def check_faiss():
    """Check if FAISS vector store exists."""
    vector_store_path = Path("data/vector_store")

    print("\n📦 FAISS (Local Vector Store)")
    print("=" * 50)

    if vector_store_path.exists():
        files = list(vector_store_path.glob("*"))
        if files:
            print(f"   ✅ Vector store found at: {vector_store_path}")
            for f in files:
                size_kb = f.stat().st_size / 1024
                print(f"      - {f.name}: {size_kb:.1f} KB")
        else:
            print(f"   ⚠️  Directory exists but empty")
    else:
        print("   ⚪ Not initialized yet (upload documents first)")


def check_observability():
    """Check if observability is enabled."""
    enabled = os.getenv("ENABLE_OBSERVABILITY", "false").lower() == "true"
    exporter_type = os.getenv("OTEL_EXPORTER_TYPE", "console")
    endpoint = os.getenv("OTEL_EXPORTER_ENDPOINT", "http://localhost:4317")
    service_name = os.getenv("OTEL_SERVICE_NAME", "rag-agent")

    print("\n🔭 OpenTelemetry Observability")
    print("=" * 50)
    print(f"   ENABLE_OBSERVABILITY: {enabled}")

    if enabled:
        print(f"   Service name: {service_name}")
        print(f"   Exporter type: {exporter_type}")

        if exporter_type == "otlp":
            print(f"   OTLP endpoint: {endpoint}")
            # Try to connect to endpoint
            try:
                import socket
                import urllib.parse
                parsed = urllib.parse.urlparse(endpoint)
                host = parsed.hostname or 'localhost'
                port = parsed.port or 4317

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()

                if result == 0:
                    print(f"   ✅ Endpoint reachable at {host}:{port}")
                else:
                    print(f"   ❌ Cannot reach {host}:{port}")
            except Exception as e:
                print(f"   ⚠️  Could not test endpoint: {e}")
        elif exporter_type == "console":
            print("   📝 Traces will be printed to console")
        elif exporter_type == "jaeger":
            jaeger_host = os.getenv("JAEGER_HOST", "localhost")
            jaeger_port = os.getenv("JAEGER_PORT", "6831")
            print(f"   Jaeger agent: {jaeger_host}:{jaeger_port}")
    else:
        print("   ⚪ Not enabled (no tracing)")


def check_policy_engine():
    """Check if policy engine is enabled."""
    use_policies = os.getenv("USE_POLICY_ENGINE", "true").lower() == "true"
    policy_file = Path("src/policy/default_policies.yaml")

    print("\n🛡️  Policy Engine")
    print("=" * 50)
    print(f"   USE_POLICY_ENGINE: {use_policies}")

    if use_policies:
        if policy_file.exists():
            print(f"   ✅ Policy file found: {policy_file}")
            with open(policy_file) as f:
                lines = f.readlines()
                # Count policy rules
                tool_policies = sum(1 for line in lines if line.strip().startswith('- rule_id:'))
                print(f"   Policy rules defined: {tool_policies}")
        else:
            print("   ⚠️  Policy file not found")
    else:
        print("   ⚪ Disabled (no policy enforcement)")


def check_persistence():
    """Check what data is persisted to disk."""
    print("\n💾 Data Persistence")
    print("=" * 50)

    # Check episodic memory
    episodic_path = Path("data/episodic_memory")
    if episodic_path.exists():
        episodes = list(episodic_path.glob("*.json"))
        print(f"   Episodic memory: {len(episodes)} sessions saved")
    else:
        print("   Episodic memory: No sessions yet")

    # Check learning data
    learning_file = Path("data/learning/learning_data.pkl")
    if learning_file.exists():
        size_kb = learning_file.stat().st_size / 1024
        print(f"   Learning data: {size_kb:.1f} KB")
    else:
        print("   Learning data: Not initialized")

    # Check reflections
    reflections_file = Path("data/reflections/reflections.jsonl")
    if reflections_file.exists():
        with open(reflections_file) as f:
            count = sum(1 for line in f if line.strip())
        print(f"   Reflections: {count} entries")
    else:
        print("   Reflections: No entries yet")


def main():
    print("\n" + "="*50)
    print("   RAG SYSTEM BACKEND STATUS CHECK")
    print("="*50)

    check_postgres()
    check_redis()
    check_pinecone()
    check_faiss()
    check_observability()
    check_policy_engine()
    check_persistence()

    print("\n" + "="*50)
    print("   STATUS CHECK COMPLETE")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
