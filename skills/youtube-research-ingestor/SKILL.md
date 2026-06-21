---
name: youtube-research-ingestor
description: >
  Ingest a YouTube URL — lecture, interview, tutorial, talk — into a structured,
  local, source-graded research artifact: metadata, transcript (official subtitles
  first, local Whisper fallback), structured summary, an extracted-claims table,
  references/entities mentioned, a verification-needed list, optional technical
  artifacts (commands/code/config) and frame notes, and an audit. Local-first
  (yt-dlp + ffmpeg + whisper), treats YouTube as a SECONDARY source, never promotes
  an unsupported claim to fact, and never fabricates references, DOIs, timestamps,
  or quotations. Modes: transcript | summary | claims | scientific-review |
  technical-review | teaching-notes. Use when the user gives a YouTube URL and
  wants notes, a transcript, claim analysis, extracted references/tools/papers, or
  reproducible technical steps — NOT for copyrighted reproduction, paywall bypass,
  or processing patient-identifiable clinical material without lawful authorization.
allowed-tools: [Bash, Read, Write, WebFetch]
---

# youtube-research-ingestor

Turn a single YouTube URL into a durable, self-describing research artifact: a small
directory of markdown files that carry (a) where the content came from, (b) the
transcript, (c) a structured summary, (d) an extracted-claims table separating
opinion from evidence, (e) references and entities mentioned, (f) what still needs
primary-source verification, and (g) an audit of how the data was acquired and how
much to trust it.

This is an **INGEST** skill in the scriptorium lifecycle. It produces the raw,
sourced unit; it does not adjudicate truth.

## Scriptorium integration

This skill composes with the rest of the toolkit — don't reinvent their jobs:

- **Claim grading →** use `epistemic-status` for each row of `claims.md`
  (speculative → working → corroborated → operational → canonical, + contradicted),
  with the strict asymmetric-risk mode for clinical/medical claims. The
  `Verification status` column here is the input to that skill, not a substitute.
- **Durable note / provenance →** `field-note-from-url` writes the canonical
  provenance-frontmatter note; this skill's `metadata.md` + `summary.md` feed it.
- **Verifying claims against primary literature →** `literature-search` skill or the
  `research-scout` agent (PubMed/Crossref/OpenAlex), never the video itself.
- **Output location →** defaults below are universal; if a `profile.knowledge_base.path`
  is set, write the artifact under it instead.

## Purpose

Use this skill to ingest, transcribe, summarize, and critically analyze YouTube
videos for research, education, scientific writing, technical learning, and project
documentation. It converts a YouTube URL into a structured local research artifact:
metadata, transcript, structured summary, key claims, source-quality assessment,
missing references, possible unsupported statements, and reusable Markdown notes.

This skill is for analytical work, not entertainment browsing.

## Use this skill when

The user provides a YouTube URL and asks to:

- summarize a video, or extract its transcript
- analyze the scientific or technical claims
- convert a lecture/interview/tutorial into notes
- identify claims requiring verification
- extract references, tools, names, papers, software, or datasets mentioned
- compare video content with scientific literature or official documentation
- build project notes for an Obsidian/GitHub knowledge base

## Do not use this skill when

- the user asks for full copyrighted video reproduction
- the user wants to bypass paywalls or access restrictions
- the video is private or inaccessible
- the user asks to download, redistribute, or rehost copyrighted material
- the video contains patient-identifiable clinical data and lawful authorization
  has not been confirmed
- the task is answered better from primary literature, official documentation, or
  uploaded source files

## Core principle

Treat YouTube as a **secondary source** unless the video itself is the primary
object of analysis. For scientific, medical, legal, regulatory, or technical claims:

- do not treat the speaker's statement as automatically true
- mark unsupported claims
- recommend verification against primary sources (PubMed, DOI-bearing articles,
  official documentation, standards, guidelines, regulatory documents)

## Required input

At least one YouTube URL. Accepted forms:

```text
https://www.youtube.com/watch?v=VIDEO_ID
https://youtu.be/VIDEO_ID
https://www.youtube.com/live/VIDEO_ID
https://www.youtube.com/shorts/VIDEO_ID
```

Optional user instructions:

```text
language: pl|en|auto
output_dir: ./youtube-research
mode: summary | transcript | claims | scientific-review | technical-review | teaching-notes
verify_claims: yes|no
extract_references: yes|no
extract_commands: yes|no
extract_code: yes|no
extract_frames: yes|no
```

## Expected local dependencies

Prefer local-first tools. **Run this preflight gate FIRST, before Step 1.** If a
required tool is missing, stop and report what to install — do not start a run that
will fail halfway:

```bash
# Required: yt-dlp (metadata + subtitles + download), ffmpeg (audio/frames), python3.
for t in yt-dlp ffmpeg python3; do
  command -v "$t" >/dev/null || echo "MISSING (required): $t"
done
# Optional, only for the audio-transcription fallback (Step 3) and frame timing:
for t in whisper faster-whisper jq; do
  command -v "$t" >/dev/null || echo "missing (optional): $t"
done
```

- Any `MISSING (required)` line → **abort** and surface the install command below.
- `whisper`/`faster-whisper` are needed only when no subtitles exist (Step 3); if they
  are also missing and subtitles are unavailable, report transcript-acquisition failure
  rather than guessing content.

Install (Ubuntu/Kubuntu) only with user approval, never on a shared/clinical/regulated host:

```bash
sudo apt update && sudo apt install -y yt-dlp ffmpeg python3 python3-pip jq
python3 -m pip install --user faster-whisper   # optional
```

## Output structure

Default naming pattern (honor `profile.knowledge_base.path` if set, else `./youtube-research/`):

```text
youtube-research/<date>_<video_id>_<short_slug>/
├── metadata.json
├── metadata.md
├── transcript.raw.txt
├── transcript.cleaned.md
├── summary.md
├── claims.md
├── references-mentioned.md
├── verification-needed.md
├── technical-artifacts.md   # technical-review only
├── frame-notes.md           # if frames extracted
└── audit.md
```

Example: `youtube-research/2026-06-21_dQw4w9WgXcQ_ai_regulatory_affairs/`

## Workflow

### Step 1 — Identify the video and capture metadata

```bash
yt-dlp --print "%(id)s" "<URL>"
yt-dlp --dump-json --skip-download "<URL>" > metadata.json
yt-dlp --print "Title: %(title)s
Channel: %(channel)s
Uploader: %(uploader)s
Upload date: %(upload_date)s
Duration: %(duration_string)s
Webpage URL: %(webpage_url)s" "<URL>" > metadata.md
```

### Step 2 — Try official subtitles/transcript first

```bash
yt-dlp --list-subs "<URL>"
yt-dlp --skip-download --write-subs --write-auto-subs \
       --sub-langs "en,pl,en.*,pl.*" --convert-subs srt "<URL>"
```

Prefer manually created subtitles over automatic ones. If only VTT is available, keep
it and clean later.

### Step 3 — Local transcription fallback (only if subtitles unavailable)

Use only for legitimate research, teaching, accessibility, or private analysis.

```bash
yt-dlp -x --audio-format mp3 --audio-quality 0 "<URL>"
whisper audio.mp3 --language auto --task transcribe --output_format txt --output_dir .
```

Do not upload audio to third-party transcription services unless the user explicitly
requests it and confirms no privacy/confidentiality concerns.

### Step 4 — Clean the transcript

Create `transcript.cleaned.md`. Remove obvious artifacts (repeated timestamps, broken
speaker labels, mid-sentence subtitle line breaks, duplicate auto-caption phrases).
Do **not** silently rewrite technical meaning — preserve names, tools, model/drug
names, equations, regulatory references, and citations. If transcript quality is poor,
say so in `audit.md`.

### Step 5 — Structured summary (`summary.md`)

```markdown
# Summary

## Video metadata
- Title / Channel / URL / Upload date / Duration
- Transcript source / Transcript quality

## Executive summary
Brief 5–10 sentence summary.

## Main points
1. … 5.

## Practical implications
- Research / Clinical / Software-AI / Teaching / Regulation

## Limitations of the video
- …
```

### Step 6 — Extract claims (`claims.md`)

```markdown
# Claims extracted from the video

| ID  | Claim | Type | Support in video | Verification status | Notes |
|-----|-------|------|------------------|---------------------|-------|
| C01 |       | scientific / clinical / technical / regulatory / financial / historical / opinion / anecdotal / speculative / promotional | strong / moderate / weak | verified / unverified / contradicted / partially supported / needs primary source / outside scope |  |
```

If verification was not performed, do not label claims as verified. Grade survivors
with the `epistemic-status` skill.

### Step 7 — References and entities (`references-mentioned.md`)

Sections: Papers/books/reports · DOI/PMID/arXiv/Zenodo/GitHub links · People ·
Institutions · Software/tools/models · Standards/regulations/guidelines · Datasets.
Mark incomplete references explicitly, e.g.
`Incomplete reference: "the Stanford paper about medical LLMs" — needs identification.`

### Step 8 — Technical artifact extraction (`technical-artifacts.md`)

For technical videos, capture these sections:

- **Commands** — fenced `bash` blocks
- **Code snippets** — fenced blocks in the shown language
- **Configuration files** — fenced `yaml`/`json` blocks
- **Libraries / frameworks** — bullet list
- **Architecture notes** — bullet list
- **Reproducibility concerns** — bullet list

Do not invent commands or code not present in the video. Label every artifact:
`[verbatim from transcript]` · `[reconstructed]` · `[inferred]` · `[needs verification]`.

### Step 9 — Optional frame extraction (content-change, not fixed interval)

Only when visual content matters (diagrams, slides, charts, UI demos, on-screen code,
device setup). Prefer transcript-first analysis; do not overuse. (Needs the video, so
download it here: `yt-dlp -f "bv*+ba/b" -o video.mp4 "<URL>"`.)

**Default — scene-change detection.** Capture one frame each time the picture changes
enough (a new slide, a chart swap, a UI step) instead of blindly sampling every N
seconds. `scene` scores frame-to-frame difference on 0..1; emit a frame when it exceeds
a threshold, and `showinfo` logs each kept frame's timestamp so you can fill the table.

```bash
mkdir -p frames
# THRESH knob: 0.3–0.4 = slide decks / talks; lower = more sensitive (subtle changes),
# higher = only hard cuts. Tune per video; start at 0.4.
ffmpeg -hide_banner -i video.mp4 \
  -vf "select='gt(scene,0.4)',showinfo" -vsync vfr -frame_pts 1 \
  frames/scene_%04d.jpg 2> frames/scene-times.log
# scene-times.log lines carry pts_time:<seconds> → map each frame to its timestamp.
```

**Fallbacks** (use only when scene-detect is wrong for the material):

```bash
# Talking-head with no slides, or you just want periodic checkpoints:
ffmpeg -i video.mp4 -vf "fps=1/30" frames/frame_%04d.jpg          # every 30 s
# Known moment of interest:
ffmpeg -ss 00:05:30 -i video.mp4 -frames:v 1 frames/at_0530.jpg   # single timestamp
```

`frame-notes.md`: table of `Timestamp | Frame file | What is visible | Relevance | Needs verification`.
Pull timestamps from `scene-times.log` (`pts_time`). If the threshold yields too many or
too few frames, re-run with a different value rather than keeping noise.

### Step 10 — Audit (`audit.md`)

Record: data acquisition (URL, metadata yes/no, transcript source, audio/video/frames
downloaded), quality assessment (transcript quality, speaker attribution, technical-term
reliability, language, major risks), copyright & privacy (no full copyrighted content
reproduced; no patient-identifiable data without authorization), scientific reliability
(YouTube = secondary; unsupported claims not promoted), and open issues.

## Verification policy

For medicine, science, law, finance, regulatory affairs, software dependencies, or
current events: verify externally before producing final conclusions; cite DOI, PMID,
official documentation, standards, or regulatory documents. If verification was not
done, write `Verification not performed in this run`.

For medical content: never infer clinical recommendations solely from YouTube;
distinguish education from clinical guidance; flag outdated statements, missing
guideline references, and stated/visible conflicts of interest.

## Output modes

| Mode | Produces |
|------|----------|
| `transcript` | metadata.md, transcript.raw.txt, transcript.cleaned.md, audit.md |
| `summary` | + summary.md |
| `claims` | metadata.md, transcript.cleaned.md, claims.md, verification-needed.md, audit.md |
| `scientific-review` | summary + claims + references-mentioned + verification-needed + audit |
| `technical-review` | summary + technical-artifacts + claims + audit |
| `teaching-notes` | summary + teaching-notes.md + questions.md + audit |

`scientific-review` also flags: unsupported biomedical claims, overgeneralizations,
conflicts with guidelines, missing comparator/methodology data, claims needing
DOI/PMID. `technical-review` also flags: reproducibility gaps, missing versions/hardware,
hidden dependencies, unclear commands, security and licensing concerns. `teaching-notes`
structures learning objectives, key concepts, common misconceptions, discussion
questions, and a practical exercise.

## Style requirements

Concise structured Markdown; tables for claims/references/tools/entities; mark
uncertainty explicitly with labels: `[verified]` `[unverified]` `[needs source]`
`[inferred]` `[speculative]` `[contradicted]` `[low transcript quality]`
`[AI Model-Based Prediction]`. **Do not fabricate references, DOIs, names,
timestamps, or quotations.**

## Quotation policy

Avoid long verbatim quotations. Short excerpts only when necessary for analysis;
include a timestamp if available; prefer paraphrase for summaries. Do not reproduce
substantial copyrighted transcript sections.

## Safety and privacy constraints

- Do not process patient-identifiable clinical material without confirmed lawful authorization.
- Do not upload confidential material to third-party APIs.
- Do not store sensitive transcripts outside the project directory.
- For GitHub commits, commit only summaries, user-authored notes, metadata, claim
  tables, and verification notes — **not** full transcripts unless the source license
  explicitly permits it.

## Minimal command template

```bash
URL="<PASTE_URL_HERE>"
OUTDIR="youtube-research/$(date +%F)_$(yt-dlp --print '%(id)s' "$URL")"
mkdir -p "$OUTDIR" && cd "$OUTDIR"
yt-dlp --dump-json --skip-download "$URL" > metadata.json
yt-dlp --print "Title: %(title)s
Channel: %(channel)s
Upload date: %(upload_date)s
Duration: %(duration_string)s
URL: %(webpage_url)s" "$URL" > metadata.md
yt-dlp --skip-download --write-subs --write-auto-subs \
       --sub-langs "en,pl,en.*,pl.*" --convert-subs srt "$URL"
```

## Done criteria

A run is complete only when: metadata was captured or its failure documented;
transcript was acquired or its failure documented; transcript quality was assessed;
the selected mode's output files were created; unsupported claims were separated from
verified facts; limitations were stated; and no copyrighted or confidential material
was inappropriately reproduced.

## Recommended final response to user

On success, list the created files, then give one-line **Key result** and
**Main limitation**. On transcript-acquisition failure, state the reason and offer:
provide another URL · provide downloaded subtitles · allow local audio transcription ·
use manual notes.
