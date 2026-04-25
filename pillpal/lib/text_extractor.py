from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image


def _timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _open_capture(source: str) -> cv2.VideoCapture:
    """
    Open a camera/stream source.

    - "0", "1", ...: local camera index
    - URL: phone/IP camera stream URL (recommended for phone camera)
    - File path: video file
    """
    try:
        return cv2.VideoCapture(int(source))
    except ValueError:
        return cv2.VideoCapture(source)


def _preprocess_for_ocr(bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2,
    )


def _ocr_text(binary_or_gray: np.ndarray, *, lang: str) -> str:
    pil_img = Image.fromarray(binary_or_gray)
    # psm 6: assume a block of text
    return pytesseract.image_to_string(pil_img, lang=lang, config="--oem 3 --psm 6").strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan camera frames (phone stream or webcam) and extract text."
    )
    parser.add_argument(
        "--source",
        default="0",
        help='Camera index like "0" or a phone stream URL.',
    )
    parser.add_argument(
        "--lang",
        default="eng",
        help="Tesseract language code (default: eng).",
    )
    parser.add_argument(
        "--out-dir",
        default=str(Path.cwd() / "ocr_outputs"),
        help="Directory to write captures + extracted text.",
    )
    parser.add_argument(
        "--scan-every-n-frames",
        type=int,
        default=10,
        help="Run OCR every N frames (lower = more responsive, higher = faster).",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=6,
        help="Only treat OCR as 'found text' if it has at least this many chars.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    _ensure_dir(out_dir)

    cap = _open_capture(args.source)
    if not cap.isOpened():
        raise SystemExit(
            f"Could not open source '{args.source}'. "
            "For a phone camera, pass the stream URL via --source."
        )

    window = "Text Scanner (q=quit)"
    frame_i = 0

    # This is the variable you asked for: it will hold the most recently detected text.
    found_text: str = ""

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break

            frame_i += 1
            do_scan = (frame_i % max(1, args.scan_every_n_frames)) == 0

            if do_scan:
                pre = _preprocess_for_ocr(frame)
                text = _ocr_text(pre, lang=args.lang)

                if len(text) >= args.min_chars and text != found_text:
                    found_text = text  # <-- saved as a variable

                    ts = _timestamp()
                    (out_dir / f"{ts}.txt").write_text(found_text + "\n", encoding="utf-8")
                    cv2.imwrite(str(out_dir / f"{ts}_raw.jpg"), frame)

            overlay = frame.copy()
            cv2.putText(
                overlay,
                f"found_text: {(found_text.replace(chr(10), ' ')[:80] + ('...' if len(found_text) > 80 else ''))}",
                (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(window, overlay)

            if (cv2.waitKey(1) & 0xFF) == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image



