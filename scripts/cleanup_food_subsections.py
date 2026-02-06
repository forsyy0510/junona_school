import json
import os
import sys

# Allow running as a script from /scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app  # noqa: E402
from database import db  # noqa: E402
from info.models import InfoSection  # noqa: E402
from sidebar.routes import _clean_sidebar_content_blocks_files, _clean_sidebar_form_data_files  # noqa: E402


def _get_parent(section: InfoSection) -> str:
    try:
        if not section or not section.text:
            return ''
        td = json.loads(section.text)
        if not isinstance(td, dict):
            return ''
        form_data = td.get('form_data', {})
        if not isinstance(form_data, dict):
            return ''
        parent_val = form_data.get('parent') or ''
        if isinstance(parent_val, str) and parent_val.startswith('/sidebar/'):
            parent_val = parent_val.replace('/sidebar/', '')
        return str(parent_val).strip()
    except Exception:
        return ''


def main() -> None:
    app = create_app()
    with app.app_context():
        client = app.test_client()
        all_sections = InfoSection.query.all()

        # Строим граф родителей и находим все разделы, которые находятся внутри "Питание"
        # (т.е. имеют родителя food/nutrition напрямую или через цепочку).
        parent_map = {}
        by_endpoint = {}
        for s in all_sections:
            by_endpoint[s.endpoint] = s
            parent_map[s.endpoint] = _get_parent(s)

        roots = {'food', 'nutrition'}
        nutrition_tree = set(roots)
        changed = True
        while changed:
            changed = False
            for ep, parent in parent_map.items():
                if parent and parent in nutrition_tree and ep not in nutrition_tree:
                    nutrition_tree.add(ep)
                    changed = True

        targets = []
        for ep in sorted(nutrition_tree):
            if ep in roots:
                continue
            if ep == 'nutrition-dishes-archive':
                continue
            s = by_endpoint.get(ep)
            if s:
                targets.append(s)

        print(f"Found {len(targets)} nutrition-related subsections in the tree (excluding nutrition-dishes-archive).")

        total_removed_blocks = 0
        total_removed_form = 0
        changed_sections = 0

        for s in targets:
            removed_blocks = 0
            removed_form = 0
            changed = False

            try:
                blocks = s.get_content_blocks()
                cleaned, removed_blocks = _clean_sidebar_content_blocks_files(blocks)
                if removed_blocks > 0:
                    s.set_content_blocks(cleaned)
                    changed = True
            except Exception:
                pass

            try:
                removed_form = _clean_sidebar_form_data_files(s)
                if removed_form > 0:
                    changed = True
            except Exception:
                pass

            # Доп. проверка: реально ли URL отдается как image/* (а не 302/HTML).
            # Если нет — удаляем URL из блоков (и form_data, если это поле images).
            removed_by_http = 0
            try:
                blocks = s.get_content_blocks()
                if isinstance(blocks, list):
                    for b in blocks:
                        if not isinstance(b, dict):
                            continue
                        if b.get('type') in ('text', 'photos') and isinstance(b.get('photos'), list):
                            good = []
                            for u in b.get('photos', []):
                                if not isinstance(u, str) or not u.strip():
                                    continue
                                r = client.get(u.split('|')[0].strip(), follow_redirects=False)
                                ctype = (r.headers.get('Content-Type') or '').lower()
                                if r.status_code == 200 and ctype.startswith('image/'):
                                    good.append(u)
                                else:
                                    removed_by_http += 1
                            if good != b.get('photos', []):
                                b['photos'] = good
                                changed = True
                    if removed_by_http > 0:
                        s.set_content_blocks(blocks)
            except Exception:
                pass

            if removed_by_http:
                print(f"  {s.endpoint}: additionally removed by HTTP check = {removed_by_http}")

            if changed:
                changed_sections += 1
                total_removed_blocks += removed_blocks
                total_removed_form += removed_form
                print(f"- {s.endpoint}: removed blocks={removed_blocks}, removed form_data={removed_form}")

        if changed_sections > 0:
            db.session.commit()

        print(
            f"Done. Updated {changed_sections} sections. "
            f"Removed links: blocks={total_removed_blocks}, form_data={total_removed_form}."
        )


if __name__ == '__main__':
    main()

