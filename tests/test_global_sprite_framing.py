import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_ROOT / "game"
IMAGES_PATH = GAME_DIR / "images.rpy"
STORY_DIR = GAME_DIR / "story"


def block_with_header(source, stripped_header):
    lines = source.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != stripped_header:
            continue

        indent = len(line) - len(line.lstrip(" "))
        block = [line]
        for nested in lines[index + 1:]:
            if nested.strip():
                nested_indent = len(nested) - len(nested.lstrip(" "))
                if nested_indent <= indent:
                    break
            block.append(nested)
        return "\n".join(block)

    raise AssertionError(f"{stripped_header!r} not found")


class GlobalSpriteFramingTests(unittest.TestCase):
    def test_official_sprites_use_shared_reference_midshot_framing(self):
        source = IMAGES_PATH.read_text(encoding="utf-8")

        for transform_name in (
            "fro_left",
            "fro_underwear_left",
            "fro_casual_left",
            "ami_casual_right",
        ):
            with self.subTest(transform_name=transform_name):
                block = block_with_header(source, f"transform {transform_name}:")
                self.assertIn("yalign 1.0", block)
                self.assertIn("yoffset 800", block)
                self.assertIn("zoom 0.56", block)

        self.assertIn("xalign 0.08", block_with_header(source, "transform fro_left:"))
        self.assertIn("xalign 0.08", block_with_header(source, "transform fro_underwear_left:"))
        self.assertIn("xalign 0.08", block_with_header(source, "transform fro_casual_left:"))
        self.assertIn("xalign 0.92", block_with_header(source, "transform ami_casual_right:"))

    def test_pal_placeholder_uses_matching_midshot_intent(self):
        source = IMAGES_PATH.read_text(encoding="utf-8")
        block = block_with_header(source, "transform pal_casual_right:")

        self.assertIn("xalign 0.92", block)
        self.assertIn("yalign 1.0", block)
        self.assertIn("yoffset 653", block)
        self.assertIn("zoom (37.0 / 15.0)", block)

    def test_story_scenes_continue_to_use_named_sprite_transforms(self):
        story_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in STORY_DIR.glob("*.rpy")
        )

        for show_line in (
            "show fro hospital_pajamas default at fro_left",
            "show fro underwear default at fro_underwear_left",
            "show fro casual default at fro_casual_left",
            "show ami casual default at ami_casual_right",
            "show pal casual default at pal_casual_right",
        ):
            with self.subTest(show_line=show_line):
                self.assertIn(show_line, story_source)

        self.assertNotIn("show fro hospital_pajamas default xpos", story_source)
        self.assertNotIn("show fro casual default xpos", story_source)
        self.assertNotIn("show ami casual default xpos", story_source)


if __name__ == "__main__":
    unittest.main()
