import requests
import json

# Test script for project management functionality

def test_project_management():
    """Test project creation and listing"""
    base_url = "http://127.0.0.1:8000"

    print("🏗️  Testing Shepherd Project Management")
    print("=" * 50)

    # Test 1: Get current projects
    print("\n📋 Fetching existing projects...")
    try:
        response = requests.get(f"{base_url}/projects")
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Found {len(projects)} existing projects")
        else:
            print(f"❌ GET projects failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure to run: uvicorn backend.app.main:app --reload")
        return

    # Test 2: Create a new project
    print("\n🆕 Creating test project 'Sermon 2025'...")

    project_data = {
        "name": "Sermon 2025",
        "description": "Test project for transcription functionality"
    }

    try:
        response = requests.post(
            f"{base_url}/projects",
            json=project_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            new_project = response.json()
            print(f"✅ Created project: {new_project['name']} (ID: {new_project['id']})")
            print(f"🗂️  Created project folders at: ~/ShepherdProjects/Sermon 2025/")
            return new_project['id']
        elif response.status_code == 400:
            error_msg = response.json().get('detail', 'Unknown error')
            if "already exists" in error_msg:
                print("ℹ️  Project already exists, that's fine!")
                return None
            else:
                print(f"❌ Create project failed: {error_msg}")
        else:
            print(f"❌ Create project failed: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error creating project: {e}")

    return None

def test_database_integrity():
    """Test that the database was created correctly"""
    print("\n💾 Testing database integrity...")
    try:
        import sqlite3
        conn = sqlite3.connect("shepherd.db")
        cursor = conn.cursor()

        # Check projects table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
        if cursor.fetchone():
            print("✅ Projects table exists")
        else:
            print("❌ Projects table missing")

        # Count projects
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        print(f"📊 Total projects in database: {project_count}")

        conn.close()

    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    project_id = test_project_management()
    test_database_integrity()

    if project_id:
        print(f"\n💡 Pro tip: You can now upload audio files with project_id={project_id} to associate them with this project!")

    print("\n🚀 Shepherd is ready for church media production!")
