import os
import time
import yaml
import markdown
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import subprocess

# === CONFIG ===
OBSIDIAN_DAILY_NOTES = "/Users/ignasprakapas/Documents/Life/daily_notes"
SITE_REPO = "/Users/ignasprakapas/Coding Projects/portfolio"
BLOG_FOLDER = os.path.join(SITE_REPO, "blogs")
GIT_BRANCH = "main"
PROCESS_DELAY = 10  # seconds to wait before reading file after detection

class NewNoteHandler(FileSystemEventHandler):
    def process_file(self, filepath):
        time.sleep(PROCESS_DELAY)  # wait for Obsidian to finish saving
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"⚠ File {filepath} no longer exists — skipping.")
            return

        # extract YAML frontmatter if exists
        if content.startswith("---"):
            parts = content.split("---", 2)
            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2]
            title = frontmatter.get("title", os.path.basename(filepath))
        else:
            title = os.path.basename(filepath)
            body = content

        # convert to HTML
        html_body = markdown.markdown(body)

        # wrap in basic HTML template
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
<h1>{title}</h1>
{html_body}
</body>
</html>
"""
        # save in blog folder
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}.html"
        output_path = os.path.join(BLOG_FOLDER, filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"saved post to {output_path}")

        # confirmation
        publish = input(f"publish '{title}' to GitHub? (y/n): ").strip().lower()
        if publish == "y":
            subprocess.run(["git", "-C", SITE_REPO, "add", "."])
            subprocess.run(["git", "-C", SITE_REPO, "commit", "-m", f"add daily note {date_str}"])
            subprocess.run(["git", "-C", SITE_REPO, "push", "origin", GIT_BRANCH])
            print("post published")
        else:
            print("post saved locally, not published.")

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"new note detected: {event.src_path}")
            self.process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"note changed: {event.src_path}")
            self.process_file(event.src_path)

if __name__ == "__main__":
    event_handler = NewNoteHandler()
    observer = Observer()
    observer.schedule(event_handler, OBSIDIAN_DAILY_NOTES, recursive=False)
    observer.start()
    print("watching....")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
