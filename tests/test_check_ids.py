"""check_ids: a replaced layout must keep every upstream view id on the same class."""

from check_ids import check_layouts


def write(root, rel, body, ns):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f'<?xml version="1.0" encoding="utf-8"?>\n<FrameLayout {ns}>{body}</FrameLayout>\n', encoding="utf-8")


def test_same_ids_pass(tmp_path, ns):
    base, skin = tmp_path / "base", tmp_path / "skin"
    write(base, "layout/a.xml", '<TextView android:id="@id/t"/><ImageView android:id="@id/i"/>', ns)
    write(skin, "layout/a.xml", '<ImageView android:id="@id/i"/><TextView android:id="@id/t" android:textSize="1sp"/><View android:id="@id/extra"/>', ns)
    assert check_layouts(skin, base) == []


def test_missing_and_retyped_ids_are_reported(tmp_path, ns):
    base, skin = tmp_path / "base", tmp_path / "skin"
    write(base, "layout/a.xml", '<TextView android:id="@id/t"/><ImageView android:id="@id/i"/>', ns)
    write(skin, "layout/a.xml", '<ImageView android:id="@id/t"/>', ns)
    problems = check_layouts(skin, base)
    assert any("'t' is ImageView, upstream TextView" in p for p in problems)
    assert any("'i' (ImageView) missing" in p for p in problems)


def test_layout_absent_upstream(tmp_path, ns):
    base, skin = tmp_path / "base", tmp_path / "skin"
    (base / "layout").mkdir(parents=True)
    write(skin, "layout/gone.xml", "", ns)
    assert check_layouts(skin, base) == ["layout/gone.xml: no such layout upstream"]


def test_qualified_layout_dirs_are_checked_too(tmp_path, ns):
    base, skin = tmp_path / "base", tmp_path / "skin"
    write(base, "layout-v26/a.xml", '<TextView android:id="@id/t"/>', ns)
    write(skin, "layout-v26/a.xml", "", ns)
    assert check_layouts(skin, base) == ["layout-v26/a.xml: id 't' (TextView) missing"]
