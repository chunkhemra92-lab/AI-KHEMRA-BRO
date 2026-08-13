# v6.4.9 Audio and UI Tuning Notes

The audio pipeline uses shorter click-protection fades of 18 ms in and 30 ms out. The previous longer fades created audible dips when adjacent subtitle cues appeared quickly. The forced inter-cue gap is now zero milliseconds, so the original subtitle timing supplies normal breathing space without an artificial silent cut.

TTS timing permits a maximum 1.10× tempo adjustment. This makes the translation prompt and cue length responsible for fitting spoken Khmer instead of forcing a noticeably rushed voice. The per-clip compressor and master compressor use slower attack/release settings with low ratios to reduce abrupt loudness changes without flattening normal human intonation. Echo is not used.

The interface gives translation and voice functions distinct visual identities. The translation action has an animated brain icon, while all voice-generation sections display four animated microphone cards for `[M]`, `[F]`, `[M_THINK]`, and `[F_THINK]`.
