# Four-voice breath-control validation — 2026-08-17

The four production voice paths were updated with conservative FFmpeg de-essing and lower high-frequency ceilings. The purpose is to reduce audible airy breath and harsh sibilance without making Khmer dialogue dull.

## Objective comparison

High-frequency energy was measured above 5 kHz on the same real Edge TTS reference phrases before and after the update.

| Role | Before | After | Reduction |
|---|---:|---:|---:|
| M | -44.5 dB | -45.6 dB | 1.1 dB |
| F | -46.3 dB | -47.3 dB | 1.0 dB |
| M_THINK | -44.7 dB | -46.0 dB | 1.3 dB |
| F_THINK | -47.2 dB | -48.5 dB | 1.3 dB |

The result is a controlled reduction in the airy upper band while retaining the previously validated role loudness balance. The normal M/F voices remain matched; inner thoughts remain about 1.5 LU softer by design.

## Processing change

Normal dialogue uses a low-pass ceiling of 6.0–6.5 kHz, targeted upper-band EQ cuts, and `deesser=i=0.22:m=0.38:f=0.54:s=o`. Inner thought uses a slightly gentler `deesser=i=0.18:m=0.32:f=0.54:s=o` before its short, low-level reflection. The thought reflection itself remains restrained at 110 ms / 0.18 gain.

## Integration result

A real Edge TTS → FFmpeg → faster-whisper integration test completed successfully after the update. The four-role overlap MP3 was 8.376 seconds, stereo, and passed the transcription check. This confirms the filter update did not break the production audio path.

This is an objective artifact and spectral-energy validation. Listener preference should be confirmed by playing the attached refreshed reference MP3s on the intended Facebook publishing device.
