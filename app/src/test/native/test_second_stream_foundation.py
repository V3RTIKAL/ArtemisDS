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


if __name__ == "__main__":
    unittest.main()
