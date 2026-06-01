from pathlib import Path
import csv
import json
import re
import shutil


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
CSV_PATH = next(WORKSPACE.glob("*.csv"))
AUDIO_SOURCE = WORKSPACE / "word_audio"
AUDIO_TARGET = ROOT / "word_audio"
INDEX_PATH = ROOT / "index.html"


SPECIAL_SPEAK = {
    "odo(u)r": "odor",
    "behavio(u)r": "behavior",
    "fulfil(l)": "fulfill",
    "connection/-exion": "connection",
    "specialize/-ise": "specialize",
    "industrialize/-ise": "industrialize",
    "analyze/-yse": "analyze",
    "minimize/-ise": "minimize",
    "cozy/cosy": "cozy",
    "skeptical/sceptical": "skeptical",
}


def speak_text(word):
    if word in SPECIAL_SPEAK:
        return SPECIAL_SPEAK[word]
    if "/" in word:
        return word.split("/")[0]
    return word.replace("(", "").replace(")", "")


def safe_name(index, spoken):
    base = re.sub(r"[^a-z0-9]+", "_", spoken.lower()).strip("_")
    return f"{index:04d}_{base or ('word_' + str(index))}.wav"


def load_rows():
    rows = []
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader)
        for values in reader:
            index = int(values[0])
            word = values[3].strip()
            spoken = speak_text(word)
            rows.append(
                {
                    "index": index,
                    "day": int(values[1]),
                    "group": int(values[2]),
                    "word": word,
                    "speak": spoken,
                    "ipa": values[4].strip(),
                    "meaning": values[5].strip(),
                    "audio": "word_audio/" + safe_name(index, spoken),
                }
            )
    return rows


def replace_word_data(html, data):
    start = html.index('<script id="wordData" type="application/json">')
    data_start = html.index(">", start) + 1
    data_end = html.index("</script>", data_start)
    return html[:data_start] + data + html[data_end:]


def main():
    rows = load_rows()
    if AUDIO_SOURCE.exists() and not AUDIO_TARGET.exists():
        shutil.copytree(AUDIO_SOURCE, AUDIO_TARGET)

    html = INDEX_PATH.read_text(encoding="utf-8")
    data = json.dumps(rows, ensure_ascii=True, separators=(",", ":"))
    INDEX_PATH.write_text(replace_word_data(html, data), encoding="utf-8")
    print(f"built {len(rows)} words with Chinese meanings")


if __name__ == "__main__":
    main()
