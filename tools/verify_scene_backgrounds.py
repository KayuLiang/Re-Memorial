from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ASSETS = [
    "game/images/bg/bg_doctor_office.jpg",
    "game/images/bg/bg_nurse_station.jpg",
    "game/images/bg/bg_bathroom.jpg",
    "game/images/bg/bg_hospital_corridor.png",
    "game/images/bg/bg_hospital_entrance.png",
    "game/images/bg/bg_train_station.jpg",
    "game/images/bg/bg_train_platform.jpg",
    "game/images/bg/bg_train_carriage.png",
]

REQUIRED_LABELS = [
    "image bg doctor_office",
    "image bg nurse_station",
    "image bg bathroom",
    "image bg hospital_corridor",
    "image bg hospital_entrance",
    "image bg train_station",
    "image bg train_platform",
    "image bg train_carriage",
    "image bg mountain_station_placeholder",
    "image bg mountain_inn_placeholder",
    "image bg snow_forest_placeholder",
    "image bg mountain_shrine_placeholder",
]

REQUIRED_SCENES = {
    "game/story/1-1-1.rpy": [
        "scene bg mountain_station_placeholder",
        "scene bg mountain_inn_placeholder",
        "scene bg snow_forest_placeholder",
        "scene bg mountain_shrine_placeholder",
    ],
    "game/story/1-1-2.rpy": [
        "scene bg doctor_office",
        "scene bg nurse_station",
        "scene bg bathroom",
        "scene bg hospital_corridor",
        "scene bg hospital_entrance",
    ],
    "game/story/1-1-3.rpy": [
        "scene bg train_station",
        "scene bg train_platform",
        "scene bg train_carriage",
    ],
}


def main() -> int:
    missing = []

    for asset in REQUIRED_ASSETS:
        if not (ROOT / asset).exists():
            missing.append(f"missing asset: {asset}")

    images = (ROOT / "game/images.rpy").read_text(encoding="utf-8")
    for label in REQUIRED_LABELS:
        if label not in images:
            missing.append(f"missing image label: {label}")

    for relpath, scenes in REQUIRED_SCENES.items():
        content = (ROOT / relpath).read_text(encoding="utf-8")
        for scene in scenes:
            if scene not in content:
                missing.append(f"missing scene in {relpath}: {scene}")

    if missing:
        print("\n".join(missing))
        return 1

    print("scene background verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
