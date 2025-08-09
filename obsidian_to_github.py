import time
import os
import shutil
import yaml
import markdown
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import subprocess

# === CONFIG ===
OBSIDIAN_DAILY_NOTES = "/Users/ignasprakapas/Documents/Life/daily_notes"
SITE_REPO = "/Users/ignasprakapas/Coding Projects/portfolio"
BLOG_FOLDER = SITE_REPO
GIT_BRANCH = "main"

class NewNoteHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"New note detected: {event.src_path}")
            self.process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"Note modified: {event.src_path}")
            self.process_file(event.src_path)


    def process_file(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract YAML frontmatter if exists
        if content.startswith("---"):
            parts = content.split("---", 2)
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2]
            title = frontmatter.get("title", os.path.basename(filepath))
        else:
            title = os.path.basename(filepath)
            body = content

        # Convert markdown to HTML
        html_body = markdown.markdown(body)

        # Wrap in basic HTML template
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

        # Save in blog folder
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}.html"
        output_path = os.path.join(BLOG_FOLDER, filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Saved post to {output_path}")

        # Commit and push to GitHub
        subprocess.run(["git", "-C", SITE_REPO, "add", "."])
        subprocess.run(["git", "-C", SITE_REPO, "commit", "-m", f"Add daily note {date_str}"])
        subprocess.run(["git", "-C", SITE_REPO, "push", "origin", GIT_BRANCH])

        print("Post published to GitHub Pages!")

if __name__ == "__main__":
    event_handler = NewNoteHandler()
    observer = Observer()
    observer.schedule(event_handler, OBSIDIAN_DAILY_NOTES, recursive=False)
    observer.start()
    print("Watching for new daily notes... Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
