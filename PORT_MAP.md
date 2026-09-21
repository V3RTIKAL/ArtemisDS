# ArtemisDS client port map

## Frozen revisions

- Base: ClassicOldSong/moonlight-android `moonlight-noir` at `c5cf27f4dc822db0e863c4691e7a70c74bea977a`
- Canonical donor: JoeCorrell/Loki `f3a840ab0e8879d7303b09f0b8bef16a872f0204`
- Rule: Artemis owns UI/session/audio/controller behavior; port only the donor's independent second-video semantics and minimal Presentation/input integration.

## Integration map

| Milestone | Donor behavior | Artemis target | Action |
|---|---|---|---|
| C1 | Discover secondary Android display and own one Presentation | `Game.java`, new `dualdisplay/SecondaryStreamPresentation.java` | REIMPLEMENT AGAINST CURRENT API |
| C1 | Secondary Surface lifecycle, single-screen fallback | new minimal Presentation layout and Surface callback | ADAPT lifecycle semantics only |
| C2 | `x-ml-video[1].enable`, indexed width/height/FPS/bitrate | in-tree moonlight-common-c `SdpGenerator.c` | ADAPT |
| C2 | RTSP SETUP/PLAY `streamid=video/1/0` | `RtspConnection.c` | ADAPT; reject missing/colliding port and continue stream 0 |
| C3 | Independent stream-1 lifecycle | new `SecondStream.{c,h}` | COPY SMALL LOGIC, forward-ported to current native core |
| C3 | Duplicate file-static RTP/depacketizer/video state | new `RtpVideoQueue2.c`, `VideoDepacketizer2.c`, `VideoStream2.c` | ADAPT donor compile-twice/renamed-symbol pattern |
| C3 | Indexed IDR/RFI and secondary termination isolation | `ControlStream.c`, `Connection.c` | ADAPT without touching one audio/control/input session ownership |
| C3 | Native build registration | `app/src/main/jni/moonlight-core/Android.mk` | ADAPT only selected files |
| C4 | Independent decoder callback table/JNI bridge | new `callbacks2.c`, `MoonBridge.java` | ADAPT |
| C4 | Second MediaCodec decoder instance | `MediaCodecDecoderRenderer.java`, `Game.java` | REUSE existing renderer class; instantiate twice |
| C4 | Surface destruction detaches stream 1 first | Presentation/Game lifecycle | ADAPT synchronously |
| C5 | Indexed absolute mouse/touch wire fields | `Input.h`, `InputStream.c`, `Limelight*.h`, `simplejni.c` | ADAPT with static layout assertions and legacy display-0 wrappers |
| C5 | Java indexed input overloads | `MoonBridge.java`, `NvConnection.java`, `Game.java` | ADAPT |
| C5 | Bottom relative trackpad | existing `TrackpadContext` | ALREADY EXISTS; relative movement remains global |
| C6 | Minimal dual-display preferences | existing Artemis preferences/settings | REIMPLEMENT minimally: enabled, resolution, FPS, bitrate, input mode |

## Explicitly not ported

- Donor launcher, Compose settings, pairing/discovery/repository stack, themes, tutorials, recording, file management, keyboards or macro controls.
- A second `NvConnection`, app launch, audio renderer, controller session or Activity.
- A wholesale copy of donor moonlight-common-c; only the identified dual-stream symbols are forward-ported.

## Test-first slices

1. Indexed input packet layout and legacy display-0 wrappers.
2. Independent native stream-1 symbol/state lifecycle.
3. SDP and RTSP stream-1 negotiation with unsupported-host fallback.
4. JNI routing to separate decoder renderers.
5. Presentation/Surface attach-detach ordering.
6. One-session/one-audio orchestration and secondary-only failure.
7. Direct-touch viewport mapping and relative trackpad behavior.
8. Preference serialization and single-screen regressions.

Hardware-only checks remain: two concurrent MediaCodec decoders, Presentation scanout, Thor display lifecycle, physical touch and target 120/60 performance.
