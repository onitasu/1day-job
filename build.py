#!/usr/bin/env python3
"""
Build a self-contained static HTML viewer with all markdown embedded.
Output: dist/index.html
"""

import json
import os
import re

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')
RESEARCH_DIR = os.path.join(PROJECT_DIR, 'research')
DIST_DIR = os.path.join(PROJECT_DIR, 'dist')


def collect_md_files(directory):
    """Collect all .md files from a directory, sorted by name."""
    files = []
    if not os.path.isdir(directory):
        return files
    for name in sorted(os.listdir(directory)):
        if name.endswith('.md'):
            path = os.path.join(directory, name)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            files.append({'name': name, 'content': content})
    return files


def build():
    slides = collect_md_files(OUTPUT_DIR)
    research = collect_md_files(RESEARCH_DIR)

    print(f"  Slides:   {len(slides)} files")
    print(f"  Research: {len(research)} files")

    # Read the viewer template
    viewer_path = os.path.join(OUTPUT_DIR, 'viewer.html')
    with open(viewer_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Build the data payload
    data_json = json.dumps({
        'slides': slides,
        'research': research,
    }, ensure_ascii=False)

    # Replace the init() function and API calls with embedded data
    static_script = f"""
<script>
  // Embedded data - no server required
  const EMBEDDED_DATA = {data_json};
</script>
"""

    # Insert embedded data before the main script
    html = html.replace('<script>', static_script + '\n<script>', 1)

    # Replace the init function to use embedded data
    old_init = '''async function init() {
    try {
      const [slidesRes, researchRes] = await Promise.all([
        fetch('/api/files'),
        fetch('/api/research')
      ]);
      const slidesData = await slidesRes.json();
      const researchData = await researchRes.json();
      state.files = slidesData.files;
      state.research = researchData.files;'''

    new_init = '''async function init() {
    try {
      state.files = EMBEDDED_DATA.slides.map(f => ({ name: f.name, path: f.name }));
      state.research = EMBEDDED_DATA.research.map(f => ({ name: f.name, path: 'research/' + f.name }));

      // Pre-populate cache with embedded content
      EMBEDDED_DATA.slides.forEach(f => { state.cache[f.name] = f.content; });
      EMBEDDED_DATA.research.forEach(f => { state.cache['research/' + f.name] = f.content; });'''

    html = html.replace(old_init, new_init)

    # Write output
    os.makedirs(DIST_DIR, exist_ok=True)
    out_path = os.path.join(DIST_DIR, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"  Output:   {out_path} ({size_kb:.0f} KB)")
    print("  Done!")


if __name__ == '__main__':
    build()
