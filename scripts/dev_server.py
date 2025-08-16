#!/usr/bin/env python3
"""
Development server for The Villain in the Verse manuscript.
Provides live preview with auto-reload when files change.
"""

import http.server
import os
import socketserver
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class MarkdownHandler(FileSystemEventHandler):
    """Handle file system events for markdown files."""
    
    def __init__(self, rebuild_callback):
        self.rebuild_callback = rebuild_callback
        self.last_rebuild = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Only process markdown files and avoid backup directories
        if (event.src_path.endswith('.md') and 
            '__backup__' not in event.src_path and
            time.time() - self.last_rebuild > 2):  # Debounce
            
            print(f"📝 Detected change: {event.src_path}")
            self.last_rebuild = time.time()
            self.rebuild_callback()

class PreviewServer:
    """HTTP server for serving the HTML preview."""
    
    def __init__(self, port=8000, directory=None):
        self.port = port
        self.directory = directory or Path.cwd() / "build" / "_preview"
        self.httpd = None
        
    def start(self):
        """Start the HTTP server."""
        os.chdir(self.directory)
        handler = http.server.SimpleHTTPRequestHandler
        
        with socketserver.TCPServer(("", self.port), handler) as httpd:
            self.httpd = httpd
            print(f"🌐 Preview server running at http://localhost:{self.port}")
            print(f"📁 Serving files from: {self.directory}")
            httpd.serve_forever()

def build_html_preview():
    """Build HTML preview of the manuscript."""
    build_dir = Path(__file__).parent.parent / "build"
    preview_dir = build_dir / "_preview"
    preview_dir.mkdir(exist_ok=True)
    
    print("🔨 Building HTML preview...")
    
    try:
        # Run pandoc to generate HTML
        result = subprocess.run([
            "pandoc",
            "-d", "pandoc.yaml",
            "--standalone",
            "--toc",
            "--toc-depth=2", 
            "--css=preview.css",
            "--metadata", "title=The Villain in the Verse - Preview",
            "-o", str(preview_dir / "index.html"),
            "../manuscript/frontmatter/titlepage.md",
            "../manuscript/frontmatter/introduction.md",
            "../manuscript/part1_case_files/*.md",
            "../manuscript/part2_patterns/patterns_overview.md", 
            "../manuscript/part2_patterns/*.md",
            "../manuscript/part3_fallout/fallout_overview.md",
            "../manuscript/part4_apologetics/field_guide.md",
            "../manuscript/part5_exit_routes/exit_routes.md",
            "../manuscript/frontmatter/acknowledgments.md"
        ], cwd=build_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ HTML preview built successfully")
            return True
        else:
            print(f"❌ Build failed: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build error: {e}")
        return False

def create_preview_css():
    """Create CSS for the HTML preview."""
    css_content = """
/* Preview CSS for The Villain in the Verse */
body {
    font-family: 'Liberation Serif', Georgia, serif;
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
    padding: 2em;
    color: #333;
    background: #fafafa;
}

h1, h2, h3, h4, h5, h6 {
    color: #8B0000;
    margin-top: 2em;
}

h1 {
    border-bottom: 3px solid #8B0000;
    padding-bottom: 0.5em;
}

h2 {
    border-bottom: 2px solid #8B0000;
    padding-bottom: 0.3em;
}

blockquote {
    border-left: 4px solid #8B0000;
    padding-left: 1em;
    margin: 1em 0;
    font-style: italic;
    background: #f8f8f8;
    padding: 1em;
}

code {
    background: #f0f0f0;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'DejaVu Sans Mono', monospace;
}

pre {
    background: #f0f0f0;
    padding: 1em;
    border-radius: 5px;
    overflow-x: auto;
}

a {
    color: #00008B;
}

a:hover {
    color: #8B0000;
}

#TOC {
    background: #f0f8ff;
    border: 1px solid #ddd;
    padding: 1em;
    margin: 2em 0;
    border-radius: 5px;
}

#TOC ul {
    list-style-type: none;
}

#TOC > ul {
    padding-left: 0;
}

.updated-notice {
    position: fixed;
    top: 10px;
    right: 10px;
    background: #8B0000;
    color: white;
    padding: 10px;
    border-radius: 5px;
    opacity: 0;
    transition: opacity 0.3s;
    z-index: 1000;
}

.updated-notice.show {
    opacity: 1;
}

/* Print styles */
@media print {
    body {
        max-width: none;
        margin: 0;
        padding: 1cm;
        background: white;
    }
    
    h2 {
        page-break-before: always;
    }
    
    h1, h2, h3 {
        page-break-after: avoid;
    }
}
"""
    
    preview_dir = Path(__file__).parent.parent / "build" / "_preview"
    css_file = preview_dir / "preview.css"
    css_file.write_text(css_content)

def watch_and_rebuild(watch_paths):
    """Watch for file changes and rebuild when needed."""
    def rebuild():
        if build_html_preview():
            print("🔄 Preview updated")
    
    event_handler = MarkdownHandler(rebuild)
    observer = Observer()
    
    for path in watch_paths:
        if path.exists():
            observer.schedule(event_handler, str(path), recursive=True)
            print(f"👀 Watching: {path}")
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Stopped watching files")
    
    observer.join()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Development server for manuscript preview")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--no-watch", action="store_true", help="Don't watch for file changes")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--build-only", action="store_true", help="Just build preview and exit")
    args = parser.parse_args()
    
    # Build initial preview
    build_dir = Path(__file__).parent.parent / "build"
    preview_dir = build_dir / "_preview"
    preview_dir.mkdir(exist_ok=True)
    
    create_preview_css()
    
    if not build_html_preview():
        print("❌ Initial build failed")
        return 1
    
    if args.build_only:
        print(f"📄 Preview built: {preview_dir / 'index.html'}")
        return 0
    
    # Start file watcher in background
    if not args.no_watch:
        watch_paths = [
            Path(__file__).parent.parent / "manuscript",
            Path(__file__).parent.parent / "villain-verse-complete.md"
        ]
        
        watcher_thread = threading.Thread(
            target=watch_and_rebuild, 
            args=(watch_paths,),
            daemon=True
        )
        watcher_thread.start()
    
    # Open browser
    if not args.no_browser:
        url = f"http://localhost:{args.port}"
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    
    # Start server
    try:
        server = PreviewServer(args.port, preview_dir)
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        return 0
    except OSError as e:
        print(f"❌ Server error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
