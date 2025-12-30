#!/usr/bin/env python3
import os
import curses
import subprocess
import tempfile
import shutil
import urllib.request
from bs4 import BeautifulSoup

BASE = "https://huggingface.co"
ROOT = f"{BASE}/rhasspy/piper-voices/tree/main"

def play_wav_direct(path: str):
    """Play WAV audio while temporarily suspending curses."""
    players = ["ffplay", "paplay"]

    # Save curses state
    curses.def_prog_mode()
    curses.endwin()

    for player in players:
        if shutil.which(player):
            try:
                if player == "ffplay":
                    subprocess.run(
                        [player, "-autoexit", "-nodisp", path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                else:
                    subprocess.run(
                        [player, path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                break
            except Exception:
                continue

    # Restore curses state
    curses.reset_prog_mode()
    curses.curs_set(0)


def normalize_href(href):
    """Normalize BeautifulSoup href into a guaranteed string."""
    if isinstance(href, list):
        href = href[0]
    if not isinstance(href, str):
        return None
    return href


def fetch_links(url):
    """Return list of subdirectory names from a Hugging Face tree page."""
    html = urllib.request.urlopen(url).read().decode()
    soup = BeautifulSoup(html, "html.parser")

    links = []
    for a in soup.find_all("a"):
        href = normalize_href(a.get("href"))
        if not href:
            continue

        if "/tree/main/" in href:
            name = href.split("/")[-1]
            links.append(name)

    return sorted(set(links))


def fetch_samples(sample_tree_url):
    """Return list of sample WAV files inside the sample directory."""
    try:
        html = urllib.request.urlopen(sample_tree_url).read().decode()
    except:
        return [], []

    soup = BeautifulSoup(html, "html.parser")

    sample_files = []
    sample_hrefs = []

    for a in soup.find_all("a"):
        href = normalize_href(a.get("href"))
        if not href:
            continue

        if href.endswith(".wav") or href.endswith(".mp3"):
            sample_files.append(href.split("/")[-1])
            sample_hrefs.append(href)

    return sample_files, sample_hrefs


def tui_menu(stdscr, title, options, allow_back=False):
    curses.curs_set(0)
    idx = 0
    offset = 0

    # Insert Back option
    if allow_back:
        options = ["< Back"] + options

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.addstr(0, 0, title[:width-1], curses.A_BOLD)

        max_items = height - 3

        if idx < offset:
            offset = idx
        elif idx >= offset + max_items:
            offset = idx - max_items + 1

        for i in range(offset, min(len(options), offset + max_items)):
            y = (i - offset) + 2
            text = f"  {options[i]}"[:width-4]

            if i == idx:
                stdscr.addstr(y, 2, text, curses.A_REVERSE)
            else:
                stdscr.addstr(y, 2, text)

        key = stdscr.getch()

        if key == curses.KEY_UP and idx > 0:
            idx -= 1
        elif key == curses.KEY_DOWN and idx < len(options) - 1:
            idx += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            return options[idx]

def download(url, path):
    print(f"Downloading {url} → {path}")
    urllib.request.urlretrieve(url, path)

def main(stdscr):
    step = "prefix"

    lang_prefix = None
    lang_code = None
    voice = None
    quality = None

    while True:

        # Step 1: choose language prefix
        if step == "prefix":
            langs = fetch_links(ROOT)
            choice = tui_menu(stdscr, "Select language prefix", langs, allow_back=False)
            lang_prefix = choice
            step = "code"
            continue

        # Step 2: choose language code
        if step == "code":
            lang_url = f"{ROOT}/{lang_prefix}"
            lang_codes = fetch_links(lang_url)
            choice = tui_menu(stdscr, "Select language code", lang_codes, allow_back=True)

            if choice == "< Back":
                step = "prefix"
                continue

            lang_code = choice
            step = "voice"
            continue

        # Step 3: choose voice
        if step == "voice":
            voice_url = f"{ROOT}/{lang_prefix}/{lang_code}"
            voices = fetch_links(voice_url)
            choice = tui_menu(stdscr, "Select voice", voices, allow_back=True)

            if choice == "< Back":
                step = "code"
                continue

            voice = choice
            step = "quality"
            continue

        # Step 4: choose quality
        if step == "quality":
            quality_url = f"{ROOT}/{lang_prefix}/{lang_code}/{voice}"
            qualities = fetch_links(quality_url)
            choice = tui_menu(stdscr, "Select quality", qualities, allow_back=True)

            if choice == "< Back":
                step = "voice"
                continue

            quality = choice
            step = "samples"
            continue

        # Step 5: sample browser
        if step == "samples":
            sample_tree_url = f"{ROOT}/{lang_prefix}/{lang_code}/{voice}/{quality}/samples"
            sample_files, sample_hrefs = fetch_samples(sample_tree_url)

            if not sample_files:
                step = "model"
                continue

            action = tui_menu(
                stdscr,
                "Sample options",
                ["continue", "preview sample", "download sample"],
                allow_back=True
            )

            if action == "< Back":
                step = "quality"
                continue

            if action == "continue":
                step = "model"
                continue

            if action == "< Back":
                step = "quality"
                continue

            if action == "preview sample":
                sample_choice = tui_menu(stdscr, "Select sample to preview", sample_files, allow_back=True)

                if sample_choice == "< Back":
                    continue

                idx = sample_files.index(sample_choice)
                sample_url = f"{BASE}{sample_hrefs[idx]}".replace("/blob/", "/resolve/")

                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp_path = tmp.name
                download(sample_url, tmp_path)
                play_wav_direct(tmp_path)
                os.unlink(tmp_path)
                continue

            if action == "download sample":
                sample_choice = tui_menu(stdscr, "Select sample to download", sample_files, allow_back=True)

                if sample_choice == "< Back":
                    continue

                idx = sample_files.index(sample_choice)
                sample_url = f"{BASE}{sample_hrefs[idx]}".replace("/blob/", "/resolve/")
                sample_out = os.path.join("models", f"{voice}_{sample_choice}")
                download(sample_url, sample_out)
                continue

        # Step 6: choose model file
        if step == "model":
            model_url = f"{ROOT}/{lang_prefix}/{lang_code}/{voice}/{quality}"
            html = urllib.request.urlopen(model_url).read().decode()
            soup = BeautifulSoup(html, "html.parser")

            models = []
            model_hrefs = []

            for a in soup.find_all("a"):
                href = normalize_href(a.get("href"))
                if href and href.endswith(".onnx"):
                    models.append(href.split("/")[-1])
                    model_hrefs.append(href)

            choice = tui_menu(stdscr, "Select model file", models, allow_back=True)

            if choice == "< Back":
                step = "samples"
                continue

            model_file = choice

            selected_href = None
            for href in model_hrefs:
                if href.endswith(model_file):
                    selected_href = href
                    break

            if not selected_href:
                print("ERROR: Could not match model file to href.")
                return

            onnx_url = f"{BASE}{selected_href}".replace("/blob/", "/resolve/")
            json_url = f"{onnx_url}.json"

            model_name = model_file.replace(".onnx", "")
            out_dir = os.path.join("models", model_name)
            os.makedirs(out_dir, exist_ok=True)

            download(onnx_url, os.path.join(out_dir, model_file))
            download(json_url, os.path.join(out_dir, f"{model_name}.onnx.json"))

            print(f"\nModel saved to: {out_dir}")
            return

if __name__ == "__main__":
    curses.wrapper(main)
