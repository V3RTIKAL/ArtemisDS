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
            [compiler, "-std=c11", "-fsyntax-only", "-Isrc", "src/SdpGenerator.c", "src/RtspConnection.c", "src/Connection.c"],
            cwd=COMMON.parent,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


class C3BridgeContractTest(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
