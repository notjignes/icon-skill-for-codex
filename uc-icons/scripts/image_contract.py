#!/usr/bin/env python3
"""Memory-bounded helpers for border-connected image background checks."""

from __future__ import annotations

from typing import Callable

from PIL import Image


Pixel = tuple[int, ...]


def scan_border_component(
    image: Image.Image,
    is_candidate: Callable[[Pixel], bool],
    replacement: Pixel | None = None,
    is_exact: Callable[[Pixel], bool] | None = None,
) -> tuple[int, int]:
    """Scan a 4-connected border component using a scanline stack.

    This avoids allocating millions of Python tuple/set entries for a flat 2048x1536
    background. Returns `(component_pixels, exact_pixels)` and optionally replaces the
    component in place.
    """

    pixels = image.load()
    width, height = image.size
    visited = bytearray(width * height)
    stack: list[tuple[int, int]] = []

    for x in range(width):
        if is_candidate(pixels[x, 0]):
            stack.append((x, 0))
        if height > 1 and is_candidate(pixels[x, height - 1]):
            stack.append((x, height - 1))
    for y in range(1, height - 1):
        if is_candidate(pixels[0, y]):
            stack.append((0, y))
        if width > 1 and is_candidate(pixels[width - 1, y]):
            stack.append((width - 1, y))

    component_count = 0
    exact_count = 0
    while stack:
        x, y = stack.pop()
        index = y * width + x
        if visited[index] or not is_candidate(pixels[x, y]):
            continue

        left = x
        while left > 0:
            candidate_index = y * width + left - 1
            if visited[candidate_index] or not is_candidate(pixels[left - 1, y]):
                break
            left -= 1
        right = x
        while right + 1 < width:
            candidate_index = y * width + right + 1
            if visited[candidate_index] or not is_candidate(pixels[right + 1, y]):
                break
            right += 1

        for scan_x in range(left, right + 1):
            scan_index = y * width + scan_x
            if visited[scan_index]:
                continue
            pixel = pixels[scan_x, y]
            if not is_candidate(pixel):
                continue
            visited[scan_index] = 1
            component_count += 1
            if is_exact and is_exact(pixel):
                exact_count += 1
            if replacement is not None:
                pixels[scan_x, y] = replacement

        for adjacent_y in (y - 1, y + 1):
            if not 0 <= adjacent_y < height:
                continue
            in_unvisited_run = False
            for scan_x in range(left, right + 1):
                adjacent_index = adjacent_y * width + scan_x
                eligible = not visited[adjacent_index] and is_candidate(pixels[scan_x, adjacent_y])
                if eligible and not in_unvisited_run:
                    stack.append((scan_x, adjacent_y))
                in_unvisited_run = eligible

    return component_count, exact_count
