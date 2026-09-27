"""Update the backend and frontend image tags in the dev Helm values."""

import re
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: update-gitops-image-tags.py <40-character-image-tag> <values-file>"
        )

    image_tag, values_path = sys.argv[1:]
    if not re.fullmatch(r"[0-9a-f]{40}", image_tag):
        raise SystemExit("Image tag must be a 40-character lowercase Git commit SHA.")

    path = Path(values_path)
    content = path.read_text(encoding="utf-8")
    patterns = (
        re.compile(
            r"(?m)(^image:\r?\n  repository:[^\r\n]*\r?\n  tag:\s*)[^\r\n]+"
        ),
        re.compile(
            r"(?m)(^frontend:\r?\n  image:\r?\n"
            r"    repository:[^\r\n]*\r?\n    tag:\s*)[^\r\n]+"
        ),
    )

    for pattern, service in zip(patterns, ("backend", "frontend")):
        content, replacements = pattern.subn(rf"\g<1>{image_tag}", content)
        if replacements != 1:
            raise SystemExit(
                f"Expected exactly one {service} image tag in {path}; "
                f"found {replacements}."
            )

    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
