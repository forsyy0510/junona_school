"""
Cleanup script:
- For section 'food': remove dish-related content_blocks (dishes, daily-dish, and text titled 'Ежедневное меню')
- For section 'nutrition-dishes-archive': remove empty dishes block, and clear "digits-only" content in the text block

Run:
  .venv/Scripts/python.exe scripts/cleanup_nutrition_blocks.py
"""

import os
import re
import sys

# Ensure project root is on sys.path so `import app` works when running from /scripts
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app
from database import db
from info.models import InfoSection


def _is_digits_only(text: str) -> bool:
    if text is None:
        return False
    s = str(text).strip()
    if not s:
        return False
    # allow digits, dots, commas and spaces (e.g. "123123...", "123 123")
    return re.fullmatch(r"[\d\s\.,…]+", s) is not None


def cleanup():
    changed = []
    with app.app_context():
        # --- food ---
        food = InfoSection.query.filter_by(endpoint="food").first()
        if food:
            blocks = food.get_content_blocks() or []
            new_blocks = []
            for b in blocks:
                if not isinstance(b, dict):
                    new_blocks.append(b)
                    continue
                b_type = b.get("type")
                b_title = b.get("title")
                if b_type in {"dishes", "daily-dish"}:
                    continue
                if b_type == "text" and b_title == "Ежедневное меню":
                    continue
                new_blocks.append(b)
            if new_blocks != blocks:
                food.set_content_blocks(new_blocks)
                changed.append("food.content_blocks")

        # --- nutrition-dishes-archive ---
        archive = InfoSection.query.filter_by(endpoint="nutrition-dishes-archive").first()
        if archive:
            blocks = archive.get_content_blocks() or []
            new_blocks = []
            for b in blocks:
                if not isinstance(b, dict):
                    new_blocks.append(b)
                    continue

                b_type = b.get("type")
                b_title = b.get("title")

                # Remove the whole "Ежедневное меню" text block (documents/photos on the page)
                if b_type == "text" and b_title == "Ежедневное меню":
                    continue

                # Remove empty dishes block
                if b_type == "dishes" and b_title == "Ежедневное меню":
                    dishes = b.get("dishes") or []
                    if not dishes:
                        continue

                # Clear "digits only" text content but keep photos/documents
                if b_type == "text" and b_title == "Ежедневное меню":
                    content = b.get("content")
                    if isinstance(content, str) and _is_digits_only(content):
                        b = {**b, "content": ""}

                new_blocks.append(b)

            if new_blocks != blocks:
                archive.set_content_blocks(new_blocks)
                changed.append("nutrition-dishes-archive.content_blocks")

        if changed:
            db.session.commit()
        return changed


if __name__ == "__main__":
    changed = cleanup()
    if changed:
        print("Updated:", ", ".join(changed))
    else:
        print("No changes needed.")

