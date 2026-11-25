#!/usr/bin/env python3
"""Compare two clean ESP32 sketch builds byte-for-byte and report useful drift evidence."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import stat
import sys
from pathlib import Path

CHUNK_SIZE = 1024 * 1024

# ESP32 app image: 24-byte esp_image_header_t + 8-byte segment header.
# esp_app_desc_t places app_elf_sha256 after magic, secure_version, reserv1,
# version, project_name, time, date and idf_ver (144 bytes into the descriptor).
ESP_IMAGE_HEADER_MAGIC = 0xE9
ESP_IMAGE_HEADER_SIZE = 24
ESP_IMAGE_SEGMENT_HEADER_SIZE = 8
ESP_APP_DESC_MAGIC_WORD = 0xABCD5432
ESP_APP_DESC_OFFSET = ESP_IMAGE_HEADER_SIZE + ESP_IMAGE_SEGMENT_HEADER_SIZE
ESP_APP_DESC_APP_ELF_SHA256_OFFSET = ESP_APP_DESC_OFFSET + 4 + 4 + 8 + 32 + 32 + 16 + 16 + 32
ESP_APP_DESC_APP_ELF_SHA256_SIZE = 32


def _open_regular_image(path: str | Path, expected_name: str) -> tuple[Path, int, os.stat_result]:
    candidate = Path(path)
    if candidate.name != expected_name:
        raise ValueError(f"application image must be named {expected_name}; found {candidate.name}")

    before_path = candidate.lstat()
    if not stat.S_ISREG(before_path.st_mode):
        raise ValueError("application image must be a regular non-symlink file")
    if before_path.st_nlink != 1:
        raise ValueError("application image must not be hard-linked")
    if before_path.st_size <= 0:
        raise ValueError("application image must not be empty")

    descriptor = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before_open = os.fstat(descriptor)
        if not stat.S_ISREG(before_open.st_mode):
            raise ValueError("opened application image is not a regular file")
        if before_open.st_nlink != 1:
            raise ValueError("opened application image is hard-linked")
        if (before_open.st_dev, before_open.st_ino) != (before_path.st_dev, before_path.st_ino):
            raise ValueError("application image changed between path validation and open")
        if before_open.st_size != before_path.st_size:
            raise ValueError("application image size changed before comparison")
        return candidate, descriptor, before_open
    except BaseException as primary_error:
        try:
            os.close(descriptor)
        except BaseException as cleanup_error:
            try:
                primary_error.add_note(
                    f"additional descriptor cleanup failure: {cleanup_error!r}"
                )
            except AttributeError:
                pass
        raise


def _record_cleanup_failure(primary_error: BaseException, detail: str) -> None:
    """Attach cleanup diagnostics without replacing the error being handled."""
    try:
        add_note = getattr(primary_error, "add_note", None)
        if callable(add_note):
            add_note(detail)
        else:
            sys.stderr.write(detail + "\\n")
    except BaseException:
        # Cleanup diagnostics must never replace the operation or cleanup error.
        pass


def _close_descriptors_preserving_primary(
    descriptors: tuple[int, ...],
    primary_error: BaseException | None,
) -> None:
    """Attempt every owned descriptor once and preserve the primary failure."""
    cleanup_errors: list[BaseException] = []
    for descriptor in descriptors:
        try:
            os.close(descriptor)
        except BaseException as cleanup_error:
            cleanup_errors.append(cleanup_error)

    if not cleanup_errors:
        return

    if primary_error is not None:
        for index, cleanup_error in enumerate(cleanup_errors, start=1):
            _record_cleanup_failure(
                primary_error,
                "ESP32 image descriptor cleanup failure "
                f"{index}: {type(cleanup_error).__name__}: {cleanup_error}",
            )
        return

    first_error = cleanup_errors[0]
    for index, cleanup_error in enumerate(cleanup_errors[1:], start=2):
        _record_cleanup_failure(
            first_error,
            "additional ESP32 image descriptor cleanup failure "
            f"{index}: {type(cleanup_error).__name__}: {cleanup_error}",
        )
    raise first_error


def _verify_stable(path: Path, descriptor: int, before: os.stat_result) -> None:
    after_open = os.fstat(descriptor)
    after_path = path.lstat()
    stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
    if any(getattr(before, field) != getattr(after_open, field) for field in stable_fields):
        raise ValueError("application image changed while being compared")
    if (after_path.st_dev, after_path.st_ino) != (after_open.st_dev, after_open.st_ino):
        raise ValueError("application image path changed while being compared")
    if not stat.S_ISREG(after_path.st_mode) or after_path.st_nlink != 1:
        raise ValueError("application image path is no longer a unique regular file")


def _read_at(descriptor: int, size: int, offset: int) -> bytes:
    """Read from a descriptor without disturbing the streaming comparison cursor."""
    if hasattr(os, "pread"):
        return os.pread(descriptor, size, offset)
    current = os.lseek(descriptor, 0, os.SEEK_CUR)
    try:
        os.lseek(descriptor, offset, os.SEEK_SET)
        return os.read(descriptor, size)
    finally:
        os.lseek(descriptor, current, os.SEEK_SET)


def _read_esp_app_elf_sha256(descriptor: int) -> str | None:
    """Return the ESP32 app descriptor's embedded ELF SHA only for a valid image."""
    image_header = _read_at(descriptor, 2, 0)
    segment_header = _read_at(descriptor, ESP_IMAGE_SEGMENT_HEADER_SIZE, ESP_IMAGE_HEADER_SIZE)
    app_magic = _read_at(descriptor, 4, ESP_APP_DESC_OFFSET)
    app_elf_sha = _read_at(
        descriptor,
        ESP_APP_DESC_APP_ELF_SHA256_SIZE,
        ESP_APP_DESC_APP_ELF_SHA256_OFFSET,
    )
    if (
        len(image_header) != 2
        or image_header[0] != ESP_IMAGE_HEADER_MAGIC
        or image_header[1] < 1
        or len(segment_header) != ESP_IMAGE_SEGMENT_HEADER_SIZE
        or int.from_bytes(segment_header[4:8], "little") < 256
        or len(app_magic) != 4
        or int.from_bytes(app_magic, "little") != ESP_APP_DESC_MAGIC_WORD
        or len(app_elf_sha) != ESP_APP_DESC_APP_ELF_SHA256_SIZE
    ):
        return None
    return app_elf_sha.hex()



ESP_IMAGE_MAX_SEGMENTS = 16


def _read_esp_image_layout(descriptor: int, image_size: int) -> dict | None:
    """Parse ESP image segment boundaries and optional checksum/SHA trailer."""
    header = _read_at(descriptor, ESP_IMAGE_HEADER_SIZE, 0)
    if (
        len(header) != ESP_IMAGE_HEADER_SIZE
        or header[0] != ESP_IMAGE_HEADER_MAGIC
        or not 1 <= header[1] <= ESP_IMAGE_MAX_SEGMENTS
        or header[23] not in (0, 1)
    ):
        return None

    segment_count = header[1]
    hash_appended = header[23]
    cursor = ESP_IMAGE_HEADER_SIZE
    segments: list[dict[str, int]] = []
    for index in range(segment_count):
        segment_header = _read_at(descriptor, ESP_IMAGE_SEGMENT_HEADER_SIZE, cursor)
        if len(segment_header) != ESP_IMAGE_SEGMENT_HEADER_SIZE:
            return None
        load_addr = int.from_bytes(segment_header[0:4], "little")
        data_len = int.from_bytes(segment_header[4:8], "little")
        data_start = cursor + ESP_IMAGE_SEGMENT_HEADER_SIZE
        data_end = data_start + data_len
        if data_end > image_size:
            return None
        segments.append(
            {
                "index": index,
                "header_start": cursor,
                "header_end": cursor + ESP_IMAGE_SEGMENT_HEADER_SIZE - 1,
                "data_start": data_start,
                "data_end": data_end,
                "load_addr": load_addr,
                "data_len": data_len,
            }
        )
        cursor = data_end

    # ESP image checksum occupies the last byte of the next 16-byte block.
    # If segment data ends on a 16-byte boundary, a full padding block is used.
    checksum_offset = ((cursor // 16) + 1) * 16 - 1
    if checksum_offset >= image_size:
        return None

    appended_sha256: tuple[int, int] | None = None
    trailer_start = checksum_offset + 1
    if hash_appended:
        sha_end_exclusive = trailer_start + 32
        if sha_end_exclusive > image_size:
            return None
        appended_sha256 = (trailer_start, sha_end_exclusive - 1)
        trailer_start = sha_end_exclusive

    return {
        "segments": segments,
        "segments_end": cursor,
        "checksum_offset": checksum_offset,
        "hash_appended": hash_appended,
        "appended_sha256": appended_sha256,
        "trailer_start": trailer_start,
        "image_size": image_size,
    }


def _format_esp_image_layout(layout: dict | None) -> str:
    if layout is None:
        return "unparsed"
    segments = []
    for segment in layout["segments"]:
        if segment["data_len"]:
            data_range = f'{segment["data_start"]}-{segment["data_end"] - 1}'
        else:
            data_range = "empty"
        segments.append(
            f'{segment["index"]}:header={segment["header_start"]}-{segment["header_end"]},'
            f'data={data_range},load_addr=0x{segment["load_addr"]:08x},'
            f'size={segment["data_len"]}'
        )
    appended = layout["appended_sha256"]
    appended_range = "none" if appended is None else f"{appended[0]}-{appended[1]}"
    trailing_bytes = layout["image_size"] - layout["trailer_start"]
    return (
        f'segments=[{";".join(segments)}] '
        f'checksum_offset={layout["checksum_offset"]} '
        f'hash_appended={layout["hash_appended"]} '
        f'appended_sha256={appended_range} trailing_bytes={trailing_bytes}'
    )


def _format_difference_regions(
    ranges: list[tuple[int, int]],
    layout: dict | None,
) -> list[str]:
    if layout is None:
        return ["unparsed"]

    described: list[str] = []
    for start, end in ranges:
        labels: list[str] = []

        def add_overlap(label: str, region_start: int, region_end: int) -> None:
            overlap_start = max(start, region_start)
            overlap_end = min(end, region_end)
            if overlap_start <= overlap_end:
                labels.append(label)

        add_overlap("image_header", 0, ESP_IMAGE_HEADER_SIZE - 1)
        for segment in layout["segments"]:
            add_overlap(
                f'segment[{segment["index"]}]_header',
                segment["header_start"],
                segment["header_end"],
            )
            if segment["data_len"]:
                overlap_start = max(start, segment["data_start"])
                overlap_end = min(end, segment["data_end"] - 1)
                if overlap_start <= overlap_end:
                    offset_start = overlap_start - segment["data_start"]
                    offset_end = overlap_end - segment["data_start"]
                    segment_offset = (
                        str(offset_start)
                        if offset_start == offset_end
                        else f"{offset_start}-{offset_end}"
                    )
                    labels.append(
                        f'segment[{segment["index"]}]_data('
                        f'load_addr=0x{segment["load_addr"]:08x},'
                        f'segment_offset={segment_offset})'
                    )

        if start <= ESP_APP_DESC_APP_ELF_SHA256_OFFSET + ESP_APP_DESC_APP_ELF_SHA256_SIZE - 1:
            if end >= ESP_APP_DESC_APP_ELF_SHA256_OFFSET:
                labels.append("app_desc.app_elf_sha256")

        padding_start = layout["segments_end"]
        padding_end = layout["checksum_offset"] - 1
        if padding_start <= padding_end:
            add_overlap("segment_padding", padding_start, padding_end)
        add_overlap("image_checksum", layout["checksum_offset"], layout["checksum_offset"])

        appended = layout["appended_sha256"]
        if appended is not None:
            add_overlap("appended_sha256", appended[0], appended[1])

        trailer_start = layout["trailer_start"]
        if trailer_start < layout["image_size"]:
            add_overlap("signature_or_unknown_trailer", trailer_start, layout["image_size"] - 1)

        if not labels:
            labels.append("unmapped")
        described.append(f"{start}-{end}:{'|'.join(labels)}")
    return described


def compare_application_images(
    first_image: str | Path,
    second_image: str | Path,
    sketch_name: str,
) -> tuple[str, int, str]:
    """Return (filename, byte_length, sha256) only when two independent images match."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", sketch_name):
        raise ValueError("sketch name must be a simple filename stem")
    expected_name = f"{sketch_name}.ino.bin"

    first_path, first_fd, first_before = _open_regular_image(first_image, expected_name)
    primary_error: BaseException | None = None
    try:
        second_path, second_fd, second_before = _open_regular_image(second_image, expected_name)
        try:
            if (first_before.st_dev, first_before.st_ino) == (second_before.st_dev, second_before.st_ino):
                raise ValueError("two builds must produce distinct application-image files")

            first_digest = hashlib.sha256()
            second_digest = hashlib.sha256()
            first_size = 0
            second_size = 0
            offset = 0
            first_differences: list[str] = []
            difference_ranges: list[tuple[int, int]] = []
            difference_range_count = 0
            differing_bytes = 0
            active_range_start: int | None = None
            active_range_end: int | None = None

            while True:
                first_chunk = os.read(first_fd, CHUNK_SIZE)
                second_chunk = os.read(second_fd, CHUNK_SIZE)
                first_digest.update(first_chunk)
                second_digest.update(second_chunk)
                first_size += len(first_chunk)
                second_size += len(second_chunk)

                if first_chunk != second_chunk:
                    for index in range(max(len(first_chunk), len(second_chunk))):
                        first_value = first_chunk[index] if index < len(first_chunk) else None
                        second_value = second_chunk[index] if index < len(second_chunk) else None
                        if first_value != second_value:
                            absolute_offset = offset + index
                            differing_bytes += 1
                            if active_range_start is None:
                                active_range_start = absolute_offset
                            active_range_end = absolute_offset
                            if len(first_differences) < 16:
                                left = "missing" if first_value is None else f"0x{first_value:02x}"
                                right = "missing" if second_value is None else f"0x{second_value:02x}"
                                first_differences.append(f"{absolute_offset}:{left}/{right}")
                        elif active_range_start is not None and active_range_end is not None:
                            difference_range_count += 1
                            if len(difference_ranges) < 32:
                                difference_ranges.append((active_range_start, active_range_end))
                            active_range_start = None
                            active_range_end = None

                if not first_chunk and not second_chunk:
                    break
                offset += max(len(first_chunk), len(second_chunk))

            if active_range_start is not None and active_range_end is not None:
                difference_range_count += 1
                if len(difference_ranges) < 32:
                    difference_ranges.append((active_range_start, active_range_end))

            first_app_elf_sha = _read_esp_app_elf_sha256(first_fd)
            second_app_elf_sha = _read_esp_app_elf_sha256(second_fd)
            first_layout = _read_esp_image_layout(first_fd, first_size)
            second_layout = _read_esp_image_layout(second_fd, second_size)
            first_layout_summary = _format_esp_image_layout(first_layout)
            second_layout_summary = _format_esp_image_layout(second_layout)
            first_difference_regions = _format_difference_regions(difference_ranges, first_layout)
            second_difference_regions = _format_difference_regions(difference_ranges, second_layout)
            _verify_stable(first_path, first_fd, first_before)
            _verify_stable(second_path, second_fd, second_before)

            first_sha256 = first_digest.hexdigest()
            second_sha256 = second_digest.hexdigest()
            if first_size != second_size or first_sha256 != second_sha256:
                if first_app_elf_sha is None or second_app_elf_sha is None:
                    classification = "UNCLASSIFIED_IMAGE_DIFF"
                elif (
                    differing_bytes == ESP_APP_DESC_APP_ELF_SHA256_SIZE
                    and difference_range_count == 1
                    and difference_ranges == [
                        (
                            ESP_APP_DESC_APP_ELF_SHA256_OFFSET,
                            ESP_APP_DESC_APP_ELF_SHA256_OFFSET
                            + ESP_APP_DESC_APP_ELF_SHA256_SIZE
                            - 1,
                        )
                    ]
                ):
                    classification = "ESP_APP_DESC_APP_ELF_SHA256_ONLY"
                else:
                    classification = "OTHER_IMAGE_CONTENT_DIFF"

                formatted_ranges = [f"{start}-{end}" for start, end in difference_ranges]
                app_sha_detail = ""
                if first_app_elf_sha is not None and second_app_elf_sha is not None:
                    app_sha_detail = (
                        f" app_elf_sha256_first={first_app_elf_sha}"
                        f" app_elf_sha256_second={second_app_elf_sha}"
                    )
                raise ValueError(
                    "non-reproducible ESP32 application image: "
                    f"classification={classification} "
                    f"first_size={first_size} second_size={second_size} "
                    f"first_sha256={first_sha256} second_sha256={second_sha256} "
                    f"differing_bytes={differing_bytes} "
                    f"difference_range_count={difference_range_count} "
                    f"difference_ranges={formatted_ranges} "
                    f"first_differences={first_differences[:16]} "
                    f"image_layout_first={first_layout_summary} "
                    f"image_layout_second={second_layout_summary} "
                    f"difference_regions_first={first_difference_regions} "
                    f"difference_regions_second={second_difference_regions}"
                    f"{app_sha_detail}"
                )

            return expected_name, first_size, first_sha256
        except BaseException as exc:
            primary_error = exc
            raise
        finally:
            _close_descriptors_preserving_primary((second_fd,), primary_error)
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        _close_descriptors_preserving_primary((first_fd,), primary_error)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", required=True, type=Path)
    parser.add_argument("--second", required=True, type=Path)
    parser.add_argument("--sketch-name", required=True)
    args = parser.parse_args()

    try:
        filename, size, sha256 = compare_application_images(
            args.first, args.second, args.sketch_name
        )
    except (OSError, ValueError) as exc:
        print(f"PHX-ESP32-REPRODUCIBILITY-RED: {exc}", file=sys.stderr)
        return 1

    print(
        "PHX-ESP32-REPRODUCIBILITY-PASS: "
        f"filename={filename} size_bytes={size} sha256={sha256} builds=2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
