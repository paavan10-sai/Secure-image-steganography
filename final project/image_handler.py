
import hashlib

import numpy as np
from PIL import Image


HEADER_BYTES = 4
HEADER_BITS = HEADER_BYTES * 8


def load_image(image_path):
    image = Image.open(image_path).convert("RGB")
    return image, np.asarray(image, dtype=np.uint8).copy()


def _texture_order(image_array, embedding_key):
    arr = np.asarray(image_array, dtype=np.uint8)

    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError("Expected an RGB image.")

    red_green = arr[:, :, :2].astype(np.float32)
    gray = red_green.mean(axis=2)

    texture = (
        np.abs(np.roll(gray, 1, axis=1) - np.roll(gray, -1, axis=1))
        + np.abs(np.roll(gray, 1, axis=0) - np.roll(gray, -1, axis=0))
    )

    scores = texture.reshape(-1)

    seed = int.from_bytes(
        hashlib.sha256(
            embedding_key + b"texture-order-v1"
        ).digest()[:8],
        "big"
    )

    rng = np.random.default_rng(seed)
    scores = scores + rng.random(
        scores.size, dtype=np.float32
    ) * 1e-4

    order = np.argsort(-scores, kind="stable")
    return order[order >= HEADER_BITS].astype(np.int64)


def _bytes_to_bits(data):
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))


def _bits_to_bytes(bits):
    return np.packbits(np.asarray(bits, dtype=np.uint8)).tobytes()


def embed_payload(cover_path, payload, embedding_key, output_path):
    image, arr = load_image(cover_path)
    blue = arr[:, :, 2].reshape(-1)

    if blue.size < HEADER_BITS:
        raise ValueError("Image is too small.")

    payload = bytes(payload)
    payload_size = len(payload)
    order = _texture_order(arr, embedding_key)

    required_bits = payload_size * 8

    if required_bits > len(order):
        raise ValueError(
            f"Message too large. Maximum payload: "
            f"{len(order) // 8} bytes; required: {payload_size} bytes."
        )

    header_bits = _bytes_to_bits(
        payload_size.to_bytes(HEADER_BYTES, "big")
    )

    blue[:HEADER_BITS] = (
        (blue[:HEADER_BITS] & 0xFE) | header_bits
    )

    payload_bits = _bytes_to_bits(payload)

    blue[order[:required_bits]] = (
        (blue[order[:required_bits]] & 0xFE) | payload_bits
    )

    arr[:, :, 2] = blue.reshape(arr.shape[:2])
    Image.fromarray(arr).save(output_path, format="PNG")

    return {
        "payload_bytes": payload_size,
        "capacity_bytes": len(order) // 8,
        "width": image.width,
        "height": image.height
    }


def extract_payload(stego_path, embedding_key):
    image, arr = load_image(stego_path)
    blue = arr[:, :, 2].reshape(-1)

    if blue.size < HEADER_BITS:
        raise ValueError("Image is too small or contains no payload.")

    header_bits = blue[:HEADER_BITS] & 1
    payload_size = int.from_bytes(
        _bits_to_bytes(header_bits), "big"
    )

    order = _texture_order(arr, embedding_key)

    if payload_size <= 0 or payload_size * 8 > len(order):
        raise ValueError("Invalid payload or incorrect password.")

    payload_bits = blue[order[:payload_size * 8]] & 1
    payload = _bits_to_bytes(payload_bits)

    return payload, {
        "payload_bytes": payload_size,
        "width": image.width,
        "height": image.height
    }


def image_quality_metrics(cover_path, stego_path):
    cover = np.asarray(
        Image.open(cover_path).convert("RGB"),
        dtype=np.float64
    )
    stego = np.asarray(
        Image.open(stego_path).convert("RGB"),
        dtype=np.float64
    )

    if cover.shape != stego.shape:
        raise ValueError("Image dimensions do not match.")

    mse = float(np.mean((cover - stego) ** 2))

    psnr = (
        float("inf")
        if mse == 0
        else float(10 * np.log10((255.0 ** 2) / mse))
    )

    return {"mse": mse, "psnr_db": psnr}