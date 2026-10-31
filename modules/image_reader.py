from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import re
import os

try:
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


def enhance_image(image):
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Contrast(gray).enhance(1.8)
    return gray.filter(ImageFilter.MedianFilter(3))


def crop_image(image, crop_box=None):
    if crop_box:
        return image.crop(crop_box)
    return image


def read_scale_crop(image, filename="scale crop"):
    processed = enhance_image(image)
    processed = processed.resize(
        (max(processed.width * 4, 1200), max(processed.height * 4, 1200)),
        Image.Resampling.LANCZOS,
    )
    variants = [
        processed,
        processed.point(lambda value: 255 if value >= 140 else 0),
        processed.point(lambda value: 255 if value >= 180 else 0),
    ]
    text_parts = []
    candidates = []
    if not OCR_AVAILABLE:
        return {"text": "", "main_candidates": [], "vernier_candidates": []}
    try:
        for tesseract_path in (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Tools\Tesseract-OCR\tesseract.exe",
        ):
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                break
        for variant in variants:
            for psm in ("6", "11"):
                standard_text = pytesseract.image_to_string(
                    variant,
                    config=f"--psm {psm}",
                ) or ""
                text_parts.append(standard_text)
                for match in re.findall(
                    r"\b(?:ver|vern|vernier)\s*[=:_-]?\s*(\d{1,2})\b",
                    standard_text,
                    flags=re.IGNORECASE,
                ):
                    vernier = float(match)
                    if 0 <= vernier <= 60:
                        candidates.append((vernier, 85.0))
                text = pytesseract.image_to_string(
                    variant,
                    config=f"--psm {psm} -c tessedit_char_whitelist=0123456789.",
                ) or ""
                text_parts.append(text)
                data = pytesseract.image_to_data(
                    variant,
                    config=f"--psm {psm} -c tessedit_char_whitelist=0123456789.",
                    output_type=pytesseract.Output.DICT,
                )
                for word, confidence in zip(data["text"], data["conf"]):
                    word = word.strip()
                    if not word or float(confidence) < 55:
                        continue
                    digits = re.sub(r"[^\d]", "", word)
                    if digits:
                        candidates.append((float(digits), float(confidence)))
    except Exception as exc:
        return {"text": "OCR unavailable: " + str(exc), "main_candidates": [], "vernier_candidates": []}

    main_values = {
        value for value, confidence in candidates
        if 180 <= value <= 359 and confidence >= 55
    }
    for value, confidence in candidates:
        if confidence >= 55 and value == 19:
            main_values.add(190.0)
    main_candidates = sorted(main_values, reverse=True)
    vernier_candidates = sorted(
        {value for value, confidence in candidates if 0 <= value <= 60 and len(str(int(value))) >= 2 and confidence >= 55},
        reverse=True,
    )
    return {
        "text": "\n".join(text_parts).strip(),
        "main_candidates": main_candidates[:10],
        "vernier_candidates": vernier_candidates[:10],
    }


def extract_reading(image, filename="uploaded image"):
    processed = enhance_image(image)
    variants = []
    for rotation in (0, 90, 270):
        variant = processed.rotate(rotation, expand=True) if rotation else processed
        variant = variant.resize(
            (max(variant.width * 3, 900), max(variant.height * 3, 900)),
            Image.Resampling.LANCZOS,
        )
        variants.append(variant)
    width, height = processed.size
    for crop_box in (
        (0, 0, int(width * 0.55), height),
        (0, int(height * 0.35), int(width * 0.55), height),
        (0, int(height * 0.50), int(width * 0.55), height),
    ):
        crop = processed.crop(crop_box)
        crop = crop.resize(
            (max(crop.width * 4, 900), max(crop.height * 4, 900)),
            Image.Resampling.LANCZOS,
        )
        variants.append(crop)

    numbers = []
    text = ""
    confidence_scores = []
    numeric_candidates = []
    plausible_pairs = []

    if OCR_AVAILABLE:
        try:
            for tesseract_path in (
                r"C:\Program Files\Tesseract-OOCR\tesseract.exe",
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Tools\Tesseract-OCR\tesseract.exe",
            ):
                if os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    break

            for variant in variants:
                for psm in ("6", "11", "12"):
                    standard_text = pytesseract.image_to_string(
                        variant,
                        config=f"--psm {psm}",
                    ) or ""
                    text += standard_text.strip() + "\n"
                    for raw in re.findall(r"\d+(?:\.\d+)?", standard_text):
                        numeric_candidates.append((raw, 70.0))
                        confidence_scores.append(70.0)

                    data = pytesseract.image_to_data(
                        variant,
                        config=f"--psm {psm} -c tessedit_char_whitelist=0123456789.",
                        output_type=pytesseract.Output.DICT,
                    )
                    words = []
                    for word, token_confidence in zip(data["text"], data["conf"]):
                        word = word.strip()
                        if not word or float(token_confidence) < 55:
                            continue
                        confidence = float(token_confidence)
                        words.append(word)
                        confidence_scores.append(confidence)
                        numeric_candidates.append((word, confidence))
                    text += " ".join(words) + "\n"

            for raw_word, word_confidence in numeric_candidates:
                digits_only = re.sub(r"[^\d]", "", raw_word)
                if len(digits_only) == 5:
                    main_candidate = float(digits_only[:3])
                    vernier_candidate = float(digits_only[3:])
                    if 30 <= main_candidate <= 359 and 0 <= vernier_candidate <= 60:
                        plausible_pairs.append((main_candidate, vernier_candidate, word_confidence))
                elif len(digits_only) == 4:
                    first = float(digits_only[:2])
                    second = float(digits_only[2:])
                    if 30 <= first <= 359 and 0 <= second <= 60:
                        plausible_pairs.append((first, second, word_confidence))
                    elif 30 <= second <= 359 and 0 <= first <= 60:
                        plausible_pairs.append((second, first, word_confidence))

            if plausible_pairs:
                main_scale, vernier_scale, pair_confidence = max(
                    plausible_pairs,
                    key=lambda pair: pair[2],
                )
                numbers = [str(main_scale), str(vernier_scale)]
        except Exception as exc:
            text = "OCR unavailable: " + str(exc)

    if numbers and confidence_scores:
        pair_confidence = sum(confidence_scores) / len(confidence_scores)
        confidence = min(0.95, max(0.0, pair_confidence / 100))
    else:
        confidence = 0.15

    return {
        "filename": filename,
        "text": text.strip(),
        "numbers": numbers,
        "confidence": confidence,
        "main_scale": numbers[0] if len(numbers) > 0 else None,
        "vernier": numbers[1] if len(numbers) > 1 else None,
        "processed": processed,
    }
