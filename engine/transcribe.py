"""Распознавание речи (faster-whisper) с таймингом каждого слова.

    python3 engine/transcribe.py видео.mp4 projects/имя.words.json [--model large-v3-turbo]

Пишет JSON со словами и готовыми группами субтитров (по 1–2 слова). Файл можно
поправить руками (ошибки распознавания, акценты), проект берёт субтитры из него.

Нужен доступ к huggingface.co и *.hf.co (модель качается при первом запуске).
"""
import argparse
import json
import re
import sys

# Слова-паразиты: в субтитры не попадают (п. 6 стиля). Список можно дополнять.
FILLERS = {"ну", "вот", "да", "эээ", "ээ", "э", "ммм", "мм", "м", "типа"}
# Короткие слова не висят на экране отдельно, а приклеиваются к следующему.
SHORT = {"и", "а", "в", "во", "с", "со", "к", "ко", "у", "о", "об", "из", "на", "не", "ни",
         "мы", "мне", "же", "ли", "бы", "то", "по", "за", "от", "до", "что", "как"}


def transcribe(src, model="large-v3-turbo", language="ru"):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(src, language=language, word_timestamps=True, vad_filter=True,
                           vad_parameters=dict(min_silence_duration_ms=300, speech_pad_ms=100),
                           beam_size=5, condition_on_previous_text=False)
    words = []
    for s in segs:
        for w in s.words:
            words.append({"word": w.word.strip(), "start": round(w.start, 2),
                          "end": round(w.end, 2), "prob": round(w.probability, 2)})
    # «довольно -таки» → одно слово
    out = []
    for w in words:
        if out and w["word"].startswith("-"):
            out[-1]["word"] += w["word"]
            out[-1]["end"] = w["end"]
        else:
            out.append(w)
    return out


def clean(word):
    return re.sub(r"[^\w\-]", "", word.lower())


def subtitle_groups(words, max_chars=18):
    """Группы по 1–2 слова (п. 6 стиля).

    1) Фраза режется на паузах > 0,35 с и знаках препинания, паразиты выкидываются.
    2) Короткие слова («и», «мы», «не»…) приклеиваются к следующему слову.
    3) Соседние одиночные слова объединяются по два, если вместе не длиннее max_chars.
    """
    phrases, cur = [], []
    for i, w in enumerate(words):
        c = clean(w["word"])
        nxt = words[i + 1] if i + 1 < len(words) else None
        if c and c not in FILLERS:
            cur.append(w)
        if cur and (nxt is None or nxt["start"] - w["end"] > 0.35 or w["word"][-1:] in ",.!?"):
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)

    groups = []
    for ph in phrases:
        chunks, pre = [], []
        for w in ph:
            pre.append(w)
            if clean(w["word"]) not in SHORT:
                chunks.append(pre)
                pre = []
        if pre:  # хвост из коротких слов — к последнему куску
            if chunks:
                chunks[-1] += pre
            else:
                chunks.append(pre)
        merged = []
        for ch in chunks:
            last = merged[-1] if merged else None
            if (last is not None and len(last) == 1 and len(ch) == 1
                    and len(clean(last[0]["word"]) + clean(ch[0]["word"])) + 1 <= max_chars
                    and not getattr(last, "closed", False)):
                last.append(ch[0])
                merged[-1] = _Closed(last)
            else:
                merged.append(list(ch))
        for g in merged:
            groups.append({"text": " ".join(clean(w["word"]) for w in g),
                           "start": g[0]["start"], "end": g[-1]["end"], "accent": False})
    return groups


class _Closed(list):
    closed = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--language", default="ru")
    a = ap.parse_args()
    words = transcribe(a.src, a.model, a.language)
    data = {"model": a.model, "text": " ".join(w["word"] for w in words),
            "words": words, "subtitles": subtitle_groups(words)}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(data["text"])
    for g in data["subtitles"]:
        print(f"  {g['start']:6.2f}–{g['end']:6.2f}  {g['text']}")
    print(f"→ {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
