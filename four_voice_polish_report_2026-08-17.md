# Four-voice polish validation — 2026-08-17

The production four-role paths were refined to prevent abrupt perceived loudness changes when speakers alternate. Each clip receives an EBU R128 loudness target before it reaches the mix bus, while the final MP3 receives a Facebook-oriented speech master.

| Role | Delivery profile | Measured reference loudness | Intended relationship |
|---|---|---:|---|
| M | Dry, centered natural male dialogue | -15.8 LUFS | Normal dialogue reference |
| F | Dry, centered natural female dialogue | -15.5 LUFS | Matched to M; 0.3 LU spread |
| M_THINK | Soft, close male inner thought | -17.2 LUFS | 1.4 LU below M; deliberately softer |
| F_THINK | Soft, close female inner thought | -17.0 LUFS | 1.5 LU below F; deliberately softer |

The normal-dialogue pair differs by 0.3 LU, and the inner-thought pair differs by 0.2 LU. The intentional normal-to-thought offset is approximately 1.5 LU, so thoughts sit slightly behind speech without sounding as if the volume has dropped abruptly.

## Applied processing

Normal M/F voices retain dry centered dialogue, anti-boxiness EQ, light compression, per-clip `loudnorm`, gentle fades, and final limiting. M_THINK/F_THINK retain a close stereo thought treatment with reduced echo (`110 ms`, reduced decay), a smaller Haas width, matching loudness normalization, and a controlled `-1.5 dB` artistic offset.

The final SRT-to-MP3 master uses `loudnorm=I=-16:TP=-1.5:LRA=7`, a conservative speech-oriented level designed to retain headroom after platform processing. This report documents generated artifacts and objective measurements; subjective listener preference should be confirmed by listening to the attached four MP3 files on the target Facebook playback device.
