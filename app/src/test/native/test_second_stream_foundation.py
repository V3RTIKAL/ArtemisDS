import pathlib
import unittest


REPO = pathlib.Path(__file__).resolve().parents[4]
NATIVE = REPO / "app/src/main/jni/moonlight-core"
COMMON = NATIVE / "moonlight-common-c/src"


class SecondStreamFoundationTest(unittest.TestCase):
    def test_independent_pipeline_translation_units_exist(self):
        for filename in (
            "SecondStream.c",
            "SecondStream.h",
            "RtpVideoQueue2.c",
            "VideoDepacketizer2.c",
            "VideoStream2.c",
        ):
            self.assertTrue((COMMON / filename).is_file(), filename)

    def test_second_pipeline_uses_isolated_state_and_listener(self):
        video_stream = (COMMON / "VideoStream2.c").read_text(encoding="utf-8")
        self.assertIn("#define StreamConfig       SecondStreamConfig", video_stream)
        self.assertIn("#define VideoCallbacks     VideoCallbacks2", video_stream)
        self.assertIn("#define ListenerCallbacks  SecondStreamListenerCallbacks", video_stream)

        second_stream = (COMMON / "SecondStream.c").read_text(encoding="utf-8")
        self.assertIn("Continuing with one display", second_stream)
        self.assertNotIn("ListenerCallbacks.connectionTerminated", second_stream)
        self.assertNotIn("LiRequestIdrFrame();", second_stream)

        connection = (COMMON / "Connection.c").read_text(encoding="utf-8")
        self.assertIn("LiStopSecondDisplayStream();", connection)
        self.assertIn("LiDestroySecondDisplayState();", connection)

    def test_native_build_registers_every_second_pipeline_unit(self):
        android_mk = (NATIVE / "Android.mk").read_text(encoding="utf-8")
        for filename in (
            "SecondStream.c",
            "RtpVideoQueue2.c",
            "VideoDepacketizer2.c",
            "VideoStream2.c",
        ):
            self.assertIn(f"moonlight-common-c/src/{filename}", android_mk)

    def test_c2_advertises_indexed_second_video_mode(self):
        sdp = (COMMON / "SdpGenerator.c").read_text(encoding="utf-8")
        for attribute in (
            '"x-ml-video[1].enable"',
            '"x-nv-video[1].clientViewportWd"',
            '"x-nv-video[1].clientViewportHt"',
            '"x-nv-video[1].maxFPS"',
            '"x-nv-video[1].initialBitrateKbps"',
        ):
            self.assertIn(attribute, sdp)
        self.assertIn("LiIsSecondDisplayRequested()", sdp)

    def test_c2_negotiates_indexed_rtsp_stream_as_optional(self):
        rtsp = (COMMON / "RtspConnection.c").read_text(encoding="utf-8")
        self.assertIn('setupStream(&response, "streamid=video/1/0"', rtsp)
        self.assertIn('playStream(&response, "streamid=video/1/0"', rtsp)
        self.assertIn("VideoPortNumber2 == 0", rtsp)
        self.assertIn("VideoPortNumber2 == VideoPortNumber", rtsp)
        self.assertIn("LiDisableSecondDisplay();", rtsp)

    def test_c2_lifecycle_keeps_secondary_errors_out_of_primary_result(self):
        connection = (COMMON / "Connection.c").read_text(encoding="utf-8")
        self.assertIn("LiPrepareSecondDisplay();", connection)
        self.assertIn("int secondErr;", connection)
        self.assertIn("LiStartSecondDisplayStream(renderContext, drFlags)", connection)
        self.assertNotIn("err = LiStartSecondDisplayStream", connection)
        self.assertLess(
            connection.index("LiStopSecondDisplayStream();"),
            connection.index("stopInputStream();"),
        )

    def test_c2_native_sources_compile(self):
        import shutil
        import subprocess

        compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        if compiler is None:
            self.skipTest("no host C compiler")

        result = subprocess.run(
            [compiler, "-std=c11", "-fsyntax-only", "-Isrc", "-Ireedsolomon", "-Ienet/include", "src/SdpGenerator.c", "src/RtspConnection.c", "src/Connection.c"],
            cwd=COMMON.parent,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


class C3BridgeContractTest(unittest.TestCase):
    def test_independent_jni_decoder_bridge_is_built_and_initialized(self):
        callbacks2 = (NATIVE / "callbacks2.c").read_text(encoding="utf-8")
        callbacks = (NATIVE / "callbacks.c").read_text(encoding="utf-8")
        android_mk = (NATIVE / "Android.mk").read_text(encoding="utf-8")

        self.assertIn("callbacks2.c", android_mk)
        self.assertIn("initializeSecondDisplayBridge(env, clazz);", callbacks)
        self.assertIn("DecodedFrameBuffer2", callbacks2)
        self.assertIn("BridgeVideoRendererCallbacks2", callbacks2)
        self.assertIn("Java_com_limelight_nvstream_jni_MoonBridge_enableSecondDisplay", callbacks2)
        self.assertIn("Java_com_limelight_nvstream_jni_MoonBridge_detachSecondDisplay", callbacks2)
        self.assertIn("Java_com_limelight_nvstream_jni_MoonBridge_isSecondDisplayActive", callbacks2)

    def test_second_bridge_uses_shared_jvm_without_sharing_decoder_state(self):
        callbacks = (NATIVE / "callbacks.c").read_text(encoding="utf-8")
        callbacks2 = (NATIVE / "callbacks2.c").read_text(encoding="utf-8")

        self.assertIn("JavaVM *JVM;", callbacks)
        self.assertIn("jclass GlobalBridgeClass;", callbacks)
        self.assertIn("extern JavaVM* JVM;", callbacks2)
        self.assertIn("extern jclass GlobalBridgeClass;", callbacks2)
        self.assertNotIn("DecodedFrameBuffer;", callbacks2)

    def test_moon_bridge_exposes_independent_renderer_lifecycle(self):
        moon_bridge = (REPO / "app/src/main/java/com/limelight/nvstream/jni/MoonBridge.java").read_text(encoding="utf-8")
        listener = (REPO / "app/src/main/java/com/limelight/nvstream/NvConnectionListener.java").read_text(encoding="utf-8")

        for method in (
            "bridgeDr2Setup",
            "bridgeDr2Start",
            "bridgeDr2Stop",
            "bridgeDr2Cleanup",
            "bridgeDr2SubmitDecodeUnit",
            "setupSecondDisplayBridge",
            "detachSecondDisplayBridge",
            "isSecondDisplayActive",
        ):
            self.assertIn(method, moon_bridge)
        self.assertIn("bridgeClSecondDisplayStatusChanged", moon_bridge)
        self.assertIn("private static volatile VideoDecoderRenderer videoRenderer2;", moon_bridge)
        self.assertIn("default void secondDisplayStatusChanged", listener)

    def test_primary_connection_remains_single(self):
        connection = (REPO / "app/src/main/java/com/limelight/nvstream/NvConnection.java").read_text(encoding="utf-8")
        self.assertEqual(1, connection.count("MoonBridge.startConnection("))
        self.assertEqual(1, connection.count("MoonBridge.setupBridge("))


class C4IndexedInputContractTest(unittest.TestCase):
    def test_indexed_mouse_and_touch_jni_contract(self):
        moon = (REPO / "app/src/main/java/com/limelight/nvstream/jni/MoonBridge.java").read_text(encoding="utf-8")
        jni = (NATIVE / "simplejni.c").read_text(encoding="utf-8")
        inp = (COMMON / "Input.h").read_text(encoding="utf-8")
        stream = (COMMON / "InputStream.c").read_text(encoding="utf-8")
        for name in ("sendMousePositionForDisplay", "sendMouseMoveAsMousePositionForDisplay", "sendTouchEventForDisplay"):
            self.assertIn(name, moon)
            self.assertIn("Java_com_limelight_nvstream_jni_MoonBridge_" + name, jni)
        self.assertIn("displayIndex", inp)
        self.assertIn("LiSendMousePositionEventForDisplay", stream)
        self.assertIn("LiSendTouchEventForDisplay", stream)
        self.assertIn("currentAbsoluteMouseState[MAX_INPUT_DISPLAYS]", stream)
        self.assertIn("CTRL_CHANNEL_TOUCH_SECONDARY", stream)
        self.assertIn("displayIndex < 0", jni)

    def test_secondary_surface_lifecycle_contract_exists(self):
        listener = (REPO / "app/src/main/java/com/limelight/nvstream/NvConnectionListener.java").read_text(encoding="utf-8")
        presentation_path = REPO / "app/src/main/java/com/limelight/secondary/SecondaryDisplayPresentation.java"
        self.assertIn("secondaryDisplayStatusChanged", listener)
        self.assertIn("detachSecondDisplayBridge", (REPO / "app/src/main/java/com/limelight/nvstream/jni/MoonBridge.java").read_text(encoding="utf-8"))
        self.assertTrue(presentation_path.is_file())
        presentation = presentation_path.read_text(encoding="utf-8")
        for token in ("extends Presentation", "SurfaceHolder.Callback", "surfaceCreated", "surfaceDestroyed"):
            self.assertIn(token, presentation)

    def test_legacy_primary_input_apis_remain_wrappers(self):
        stream = (COMMON / "InputStream.c").read_text(encoding="utf-8")
        self.assertIn("return LiSendMousePositionEventForDisplay(x, y, referenceWidth, referenceHeight, 0);", stream)
        self.assertIn("contactAreaMajor, contactAreaMinor, rotation, 0);", stream)


class C5C6PolicyContractTest(unittest.TestCase):
    def test_deterministic_secondary_display_policy_and_selection(self):
        selector = REPO / "app/src/main/java/com/limelight/secondary/SecondaryDisplayPolicy.java"
        self.assertTrue(selector.is_file())
        text = selector.read_text(encoding="utf-8")
        for token in ("DISABLED", "AUTOMATIC", "FORCED", "select", "displayId"):
            self.assertIn(token, text)

    def test_policy_state_handles_reconnect_and_primary_degradation(self):
        policy = (REPO / "app/src/main/java/com/limelight/secondary/SecondaryDisplayPolicy.java").read_text(encoding="utf-8")
        for token in ("onDisplayAdded", "onDisplayRemoved", "primaryOnly", "reconnect"):
            self.assertIn(token, policy)


if __name__ == "__main__":
    unittest.main()
