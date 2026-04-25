from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image



"""
def _timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _preprocess_for_ocr(bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    thr = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2,
    )
    return thr


def _ocr_image(image: np.ndarray, *, lang: str) -> str:
    pil_img = Image.fromarray(image)
    config = "--oem 3 --psm 6"
    return pytesseract.image_to_string(pil_img, lang=lang, config=config).strip()


def _open_capture(source: str) -> cv2.VideoCapture:
    """
    source can be:
    - a camera index like "0"
    - a URL (e.g., phone/IP camera stream)
    - a file path
    """
    try:
        idx = int(source)
        return cv2.VideoCapture(idx)
    except ValueError:
        return cv2.VideoCapture(source)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Live camera OCR: capture frame, extract text, save results."
    )
    parser.add_argument(
        "--source",
        default="0",
        help='Camera index (e.g. "0") or stream URL / video file path',
    )
    parser.add_argument(
        "--out-dir",
        default=str(Path.cwd() / "ocr_outputs"),
        help="Directory to write captured images + extracted text",
    )
    parser.add_argument(
        "--lang",
        default="eng",
        help="Tesseract language code (default: eng). Requires language data installed.",
    )
    parser.add_argument(
        "--save-every-capture",
        action="store_true",
        help="Always save both raw frame and preprocessed image.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    _ensure_dir(out_dir)

    cap = _open_capture(args.source)
    if not cap.isOpened():
        raise SystemExit(
            f"Could not open camera/stream '{args.source}'. "
            "If using a phone, pass a stream URL via --source."
        )

    window_name = "PillPal Text Extractor (q=quit, c=capture)"
    last_text: str | None = None

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                print("No frame received (stream ended?)")
                break

            overlay = frame.copy()
            cv2.putText(
                overlay,
                "q: quit | c: capture+OCR",
                (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 0),
                4,
                cv2.LINE_AA,
            )
            cv2.putText(
                overlay,
                "q: quit | c: capture+OCR",
                (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            if last_text:
                preview = last_text.replace("\n", " ")
                if len(preview) > 80:
                    preview = preview[:77] + "..."
                cv2.putText(
                    overlay,
                    f"OCR: {preview}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 0, 0),
                    4,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    overlay,
                    f"OCR: {preview}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

            cv2.imshow(window_name, overlay)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("c"):
                ts = _timestamp()
                raw_path = out_dir / f"{ts}_raw.jpg"
                pre_path = out_dir / f"{ts}_pre.png"
                txt_path = out_dir / f"{ts}.txt"

                cv2.imwrite(str(raw_path), frame)

                pre = _preprocess_for_ocr(frame)
                if args.save_every_capture:
                    cv2.imwrite(str(pre_path), pre)

                text = _ocr_image(pre, lang=args.lang)
                last_text = text

                txt_path.write_text(text + "\n", encoding="utf-8")
                print(f"Saved: {txt_path}")

    finally:
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""