# AI KHEMRA BRO v6.2: Audio Pipeline Hardening Report

**Release scope.** This report documents the verified reliability work for the v6.2 Khmer audio-generation and subtitle-timing paths. It covers the production Streamlit application, the real Edge TTS service, the FFmpeg MP3 mixer, and the `faster-whisper` CPU transcription path. The results below are reproducible using the committed regression tests.

> **Verification statement.** No internet-connected application can be certified as “100% guaranteed” because the Microsoft speech service, model downloads, browser sessions, Streamlit Cloud, and user-supplied media are external variables. This release is instead **tested across every critical path available in this environment**, with bounded failures, cleanup, and recoverable errors for the identified risks.

## 1. Four-track FFmpeg MP3 mixing

The production `create_mp3()` function accepts timestamped SRT dialogue, synthesizes each cue, converts it to deterministic 48 kHz stereo PCM WAV, and creates a single 192 kbps stereo MP3. FFmpeg filtergraphs require every labelled input/output pad to be connected; this is why the v6.2 no-music path must not create an extra unused `asplit` output.[1]

| Stage | Production behavior | Reliability purpose |
|---|---|---|
| **Cue rendering** | Each Khmer cue is generated with Edge TTS and converted from variable-bitrate MP3 to 48 kHz, two-channel PCM WAV. | PCM prevents bitrate-based duration estimation problems before timing and mixing. |
| **Dialogue track** | Direct speech is centered, high-passed, equalized, gently compressed, limited, trimmed to its own SRT window, faded, and delayed to its original timestamp. | Prevents clicks, inconsistent tone, and timing drift. |
| **Inner-thought track** | `M_THINK` and `F_THINK` cues use a low-volume stereo Haas treatment instead of a loud echo. | Keeps thoughts intelligible while separating them from direct speech. |
| **Voice bus** | All delayed dialogue tracks are combined by `amix`. If music is present, the bus uses `asplit=2`: one output drives music ducking and the other goes to the final mix. | Supplies exactly one connected stream to each consumer. |
| **Music track** | Optional music is filtered, reduced to -24 dB, trimmed to programme length, then ducked with `sidechaincompress` from the voice bus. | Keeps dialogue audible without muting music entirely. |
| **Ambience track** | Optional ambience is filtered, reduced to -23 dB, and trimmed to programme length. | Adds background texture without masking speech. |
| **Master** | Voice, ducked music, and ambience are combined, gently compressed, peak-limited, loudness-normalized, padded, trimmed, and encoded as 48 kHz stereo MP3. | Prevents clipping and makes output duration deterministic. |

### v6.2 no-music correction

Previously, the graph could split the voice bus into two outputs even when background music was absent. One output then had no consumer, producing FFmpeg’s **“Filter asplit has an unconnected output”** error. The no-music branch now routes the voice bus directly to `[voice_for_mix]`; `asplit=2` is used only when the sidechain compressor actually needs both outputs.

## 2. SRT overlap timing and synchronization

Whisper is configured with word timestamps and voice-activity detection. The app groups words into readable cues with boundaries based on natural gaps, punctuation, 5.5-second duration, or 34 characters. It adjusts only accidental overlaps of **120 ms or less**; meaningful overlaps in the original speech remain untouched.

| Timing rule | v6.2 behavior |
|---|---|
| **Original timestamp authority** | Every generated voice begins at the cue’s original SRT start time via `adelay`. |
| **Real overlaps** | A cue ending at 3.0 seconds and another beginning at 1.3 seconds are intentionally mixed together. The later cue does not truncate the first one. |
| **Micro-overlaps** | An overlap of 120 ms or less is treated as a likely segmentation artifact and aligned to the preceding end time. |
| **Speech fitting** | A synthesized clip is time-compressed only when necessary. `Speed Up Only` never slows a cue; `Speed Up & Slow Down` permits controlled adjustment from 0.75× through 1.65×. |
| **Click prevention** | Per-clip fades are scaled to each clip’s available duration before the cue is delayed and mixed. |

## 3. Reliability safeguards added in this hardening release

The application keeps the existing user features and adds only internal safeguards.

| Safeguard | Implementation | Failure prevented |
|---|---|---|
| **Bounded Edge TTS request** | Each provider request has a 75-second timeout. | A stalled online TTS request cannot block a project indefinitely. |
| **Three controlled synthesis attempts** | The chosen profile is attempted first, followed by two neutral-prosody fallbacks. | Temporary service or prosody failures have a recoverable path. |
| **Partial-file removal** | Temporary MP3 output is deleted before an attempt, after an invalid response, and in the cue-rendering cleanup block. | A failed provider response cannot be mistaken for valid audio later. |
| **Bounded TTS concurrency** | At most four independent TTS requests are active for one project. | Reduces provider throttling and resource spikes while keeping parallel rendering. |
| **Deterministic clip conversion** | Temporary output is converted with noninteractive FFmpeg to 48 kHz stereo PCM, with a 180-second timeout and size validation. | Avoids VBR duration ambiguity and prevents a hanging conversion job. |
| **Noninteractive final mix** | Final FFmpeg assembly uses `-nostdin`, a 900-second timeout, size validation, and the final stderr tail in failure feedback. | Prevents a terminal-input wait and makes mix failures diagnosable. |

The design remains compatible with `edge-tts` rate, pitch, and volume controls, which the library exposes for voice output configuration.[2] The `faster-whisper` configuration remains `base` on CPU with `int8`, a documented CPU mode that trades some precision for substantially lower resource usage.[3]

## 4. Regression and integration test report

All tests below passed after the safeguards were added.

| Check | What it verifies | Result |
|---|---|---|
| `pip3 check` | Installed dependency graph has no unresolved package conflicts. | **Passed** |
| `python3 -m py_compile` | Application and all test modules compile. | **Passed** |
| `test_tags.py` | Khmer and English speaker tags normalize correctly. | **Passed** |
| `test_overlap_timing.py` | The source retains the explicit no-next-cue-trimming rules. | **Passed** |
| `test_subtitle_timing_rules.py` | Functional preservation of meaningful overlap, repair of ≤120 ms accidental overlap, SRT parsing, and multi-stage `atempo` chains. | **Passed** |
| `test_edge_tts_resilience.py` | One failed TTS attempt retries, a partial file is replaced, three invalid outputs fail safely, and stale output is removed. | **Passed** |
| `test_four_track_mix.py` | Four synthetic tracks complete through the full FFmpeg graph. Output: **33,069 bytes**. | **Passed** |
| `test_v62_audio_pipeline.py` | Real male/female Khmer Edge TTS, overlapping no-music MP3 generation, stereo output, and real `faster-whisper` transcription. | **Passed** |
| Local Streamlit health probe | The upgraded app starts and returns the Streamlit health response `ok`. | **Passed** |

## 5. Measured performance

Measurements were taken on the deployed development runtime with `faster-whisper` **1.2.1**, `edge-tts` **7.2.8**, `Streamlit` **1.61.1**, FFmpeg 6.1.1, and a cached `base` faster-whisper model. Network timing for Edge TTS can vary with the external service and connection.

| Operation | Workload | Measured time | Derived result |
|---|---|---:|---:|
| **Male Edge TTS** | 4.56-second Khmer reference phrase | 4.988 s | 1.094× real time; 27,360-byte MP3 |
| **Female Edge TTS** | 4.68-second Khmer reference phrase | 4.069 s | 0.870× real time; 28,080-byte MP3 |
| **No-music overlapping MP3** | Two overlapping Khmer SRT cues, including synthesis, PCM conversion, and final FFmpeg master | 4.387 s | 4.872-second stereo MP3; 117,549 bytes |
| **faster-whisper model initialization** | Cached `base` model, CPU `int8` | 1.291 s | Warm local initialization |
| **faster-whisper transcription** | 4.56-second Khmer Edge TTS sample, beam size 3, VAD, word timestamps | 0.864 s | 0.190× real time, approximately **5.26× faster than audio duration**; one non-empty segment |

These figures are integration-test measurements rather than a production service-level agreement. The faster-whisper project notes that inference begins only when its returned segments are iterated; the test materializes the segment generator, so the transcription measurement includes actual inference.[3]

## 6. What is verified and what remains external

The release now has explicit protection against the known MP3 generation failure without background music, subtitle-overlap truncation, stale partial TTS files, unbounded provider calls, conversion hangs, and opaque final-mix failures. The app, all focused regression tests, the real online Khmer TTS sample, the real local transcription sample, and the Streamlit health endpoint passed.

It remains important to recognize external limits: Edge TTS depends on Microsoft’s online service, large or corrupted user media can exceed resource limits, and real-world noisy video may have lower transcription accuracy than the controlled Khmer sample. The app now fails within bounded time and returns more useful error information in these cases; it cannot remove the dependency on those external systems.

## References

[1] [FFmpeg Filters Documentation — filtergraph labels, connected pads, and audio filters](https://ffmpeg.org/ffmpeg-filters.html)

[2] [rany2/edge-tts — online Microsoft Edge TTS client and prosody controls](https://github.com/rany2/edge-tts)

[3] [SYSTRAN/faster-whisper — CPU INT8 usage, word timestamps, VAD, and generator behavior](https://github.com/SYSTRAN/faster-whisper)
