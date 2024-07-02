import os
import re
import zipfile
import xml.etree.ElementTree as ET
import requests
from collections import defaultdict
import logging
import concurrent.futures
import argparse
import gc
import unidecode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration of source and destination directories
source_directories = [
    '/path/to/your/comics/'
]
destination_root = '/path/to/your/links/'  # Destination directory for symlinks
discord_webhook_url = 'https://your_webhook_address' # Create a webhook (Eg: on discord) and put the link here

# Function to clean file and directory names
def clean_name(name):
    # Remove special characters except underscores, dashes, spaces, and apostrophes
    name = re.sub(r'[^\w\s\-\'À-ÿ]', '', name)
    name = name.replace(' ', '_')  # Replace spaces with underscores
    name = unidecode.unidecode(name)  # Remove accents
    return name

# Function to read and extract content from ComicInfo.xml
def extract_comicinfo_from_cbz(cbz_path):
    try:
        with zipfile.ZipFile(cbz_path, 'r') as zip_ref:
            if 'ComicInfo.xml' in zip_ref.namelist():
                with zip_ref.open('ComicInfo.xml') as file:
                    tree = ET.parse(file)
                    root = tree.getroot()
                    series = root.find('Series')
                    title = root.find('Title')

                    series_text = series.text if series is not None else 'N/A'
                    title_text = title.text if title is not None else 'N/A'

                    logging.info(f"Extracted from {cbz_path} - Series: {series_text}, Title: {title_text}")

                    return {
                        "series": series_text,
                        "title": title_text
                    }
            else:
                logging.warning(f"ComicInfo.xml not found in {cbz_path}")
                return None
    except Exception as e:
        logging.error(f"Error processing {cbz_path}: {e}")
        return None

# Function to create symlinks
def create_symlink(source, dest):
    try:
        if os.path.exists(source):
            if not os.path.exists(dest):
                os.symlink(source, dest)
                logging.info(f'Symlink created: {dest}')
            else:
                logging.info(f'Symlink already exists: {dest}')
        else:
            logging.warning(f"Source file does not exist: {source}")
    except Exception as e:
        logging.error(f"Failed to create symlink for {source}: {e}")

# Function to process a file
def process_file(cbz_path, stats, comics_db):
    info = extract_comicinfo_from_cbz(cbz_path)
    if info:
        stats["files_with_comicinfo"] += 1
        series = info["series"]
        title = info["title"]

        if series == 'N/A' or title == 'N/A':
            stats["files_with_missing_info"] += 1
        else:
            match = re.search(r'\.T(\d+)', cbz_path)
            volume = match.group(1) if match else "NoVolume"
            volume = volume.zfill(2)  # Format volume as two digits
            comics_db[(series, volume)].append((cbz_path, title))
    else:
        stats["files_without_comicinfo"] += 1
        process_file_without_comicinfo(cbz_path, stats, comics_db)

def process_file_without_comicinfo(cbz_path, stats, comics_db):
    filename = os.path.basename(cbz_path)
    directory = os.path.basename(os.path.dirname(cbz_path))
    series = directory  # Use the directory name as the series name

    logging.info(f"ComicInfo.xml not found in {cbz_path}. Creating symlink based on directory and filename.")

    dest_dir = os.path.join(destination_root, clean_name(series))
    os.makedirs(dest_dir, exist_ok=True)

    dest = os.path.join(dest_dir, filename)
    create_symlink(cbz_path, dest)
    
    stats["symlinks_created_filename"] += 1

def process_directories(source_directories):
    stats = {
        "total_files": 0,
        "files_with_comicinfo": 0,
        "files_without_comicinfo": 0,
        "files_with_missing_info": 0,
        "symlinks_created_comicinfo": 0,
        "symlinks_created_filename": 0,
        "symlinks_removed": 0,
        "duplicates": 0
    }
    comics_db = defaultdict(list)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for source_directory in source_directories:
            for root, _, files in os.walk(source_directory):
                for file in files:
                    if file.endswith(('.cbz', '.cbr', '.pdf')):
                        stats["total_files"] += 1
                        cbz_path = os.path.join(root, file)
                        futures.append(executor.submit(process_file, cbz_path, stats, comics_db))
        
        for future in concurrent.futures.as_completed(futures):
            future.result()

    # Create symlinks for the best files
    for (series, volume), files in comics_db.items():
        best_file = sorted(files, key=lambda x: os.path.getsize(x[0]), reverse=True)[0]
        source, title = best_file
        dest_dir = os.path.join(destination_root, clean_name(series))
        os.makedirs(dest_dir, exist_ok=True)

        ext = os.path.splitext(source)[1]

        if volume != "NoVolume":
            dest = os.path.join(dest_dir, f"{volume}.{clean_name(title)}{ext}")
        else:
            dest = os.path.join(dest_dir, clean_name(os.path.basename(source)))
        
        create_symlink(source, dest)
        stats["symlinks_created_comicinfo"] += 1
        stats["duplicates"] += len(files) - 1

    return stats

def cleanup_symlinks(destination_root, stats):
    for root, _, files in os.walk(destination_root):
        for file in files:
            symlink_path = os.path.join(root, file)
            if os.path.islink(symlink_path):
                target_path = os.readlink(symlink_path)
                if not os.path.exists(target_path):
                    os.unlink(symlink_path)
                    logging.info(f"Removed obsolete symlink: {symlink_path}")
                    stats["symlinks_removed"] += 1

# Function to send a notification to Discord
def send_discord_notification(stats):
    message = (
        f"Total files processed: {stats['total_files']}\n"
        f"Files with ComicInfo.xml: {stats['files_with_comicinfo']}\n"
        f"Files without ComicInfo.xml: {stats['files_without_comicinfo']}\n"
        f"Files with missing info: {stats['files_with_missing_info']}\n"
        f"Symlinks created based on existing comicinfo: {stats['symlinks_created_comicinfo']}\n"
        f"Symlinks created based on filenames (missing comicinfo): {stats['symlinks_created_filename']}\n"
        f"Duplicates detected (not reflinked): {stats['duplicates']}\n"
        f"Symlinks removed: {stats['symlinks_removed']}\n"
    )

    if len(message) > 2000:
        message = message[:1997] + '...'

    data = {"content": message}

    response = requests.post(discord_webhook_url, json=data)
    if response.status_code != 204:
        logging.error(f"Failed to send Discord notification: {response.status_code} - {response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process CBZ files and create symlinks.')
    parser.add_argument('--source', nargs='+', default=source_directories, help='List of source directories to process.')
    parser.add_argument('--dest', default=destination_root, help='Destination root directory for symlinks.')
    parser.add_argument('--webhook', default=discord_webhook_url, help='Discord webhook URL for notifications.')
    args = parser.parse_args()

    source_directories = args.source
    destination_root = args.dest
    discord_webhook_url = args.webhook

    # Process source directories
    stats = process_directories(source_directories)

    # Clean up obsolete symlinks
    cleanup_symlinks(destination_root, stats)

    # Send statistics to Discord
    send_discord_notification(stats)

    logging.info("Processing complete. Statistics sent to Discord.")
