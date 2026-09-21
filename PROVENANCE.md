# ArtemisDS provenance

## Base

ArtemisDS is based on ClassicOldSong/moonlight-android branch `moonlight-noir`, commit `c5cf27f4dc822db0e863c4691e7a70c74bea977a`.

## Dual-screen client donor

- Repository: `https://github.com/JoeCorrell/Loki`
- Commit: `f3a840ab0e8879d7303b09f0b8bef16a872f0204`
- Subject: `feat: add Moonlight DS dual-screen streaming`
- Material semantics selected for adaptation:
  - one native Moonlight session with two video streams
  - `video/1/0` RTSP negotiation and indexed SDP attributes
  - independent RTP queue, depacketizer and video receive state
  - independent second decoder callbacks and MediaCodec renderer
  - Android secondary-display Presentation lifecycle
  - display-indexed absolute input
  - relative trackpad behavior
  - secondary failure isolation

The donor's broader launcher, settings, capture, file-management, theme, tutorial and macro-control work is not transplanted. Current Artemis remains the owner of pairing, launch, audio, controller, settings and Activity behavior.

## Optional Thor donor

Sleqa/ArtemisDualScreen is configured as a reference remote but no code has been selected from it yet. Any future use will be recorded here by repository, revision, file/subsystem and nature of adaptation.

Existing copyright and license notices remain authoritative for base and donor-derived source.
