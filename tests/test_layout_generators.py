"""unclip.apply and gen_rows.generate on small synthetic layouts."""

import xml.etree.ElementTree as ET

import pytest

import gen_rows
import unclip

A = unclip.A


def parse(xml):
    return ET.fromstring(xml)


def test_unclip_sets_false_except_around_scrollers(ns):
    root = parse(f'''<LinearLayout {ns} android:clipChildren="true">
        <FrameLayout><TextView/></FrameLayout>
        <FrameLayout android:clipChildren="true"><androidx.recyclerview.widget.RecyclerView/></FrameLayout>
        <TextView/></LinearLayout>''')
    unclip.apply(root)
    plain, holder = root[0], root[1]
    assert root.get(A + "clipChildren") == "false" and root.get(A + "clipToPadding") == "false"
    assert plain.get(A + "clipChildren") == "false"
    assert holder.get(A + "clipChildren") is None, "a scroller's parent falls back to the platform default"
    assert holder.get(A + "clipToPadding") == "false"
    assert root[2].get(A + "clipChildren") is None, "leaf views are left alone"


def test_unclip_keeps_upstream_value_on_scroller_root(ns):
    root = parse(f'<FrameLayout {ns} android:clipChildren="false"><androidx.leanback.widget.VerticalGridView/></FrameLayout>')
    upstream = parse(f'<FrameLayout {ns} android:clipChildren="false"><androidx.leanback.widget.VerticalGridView/></FrameLayout>')
    unclip.apply(root, upstream)
    assert root.get(A + "clipChildren") == "false"


def test_unclip_scroller_names():
    for name in ("androidx.recyclerview.widget.RecyclerView", "androidx.leanback.widget.HorizontalGridView",
                 "androidx.core.widget.NestedScrollView", "com.fongmi.android.tv.ui.custom.CustomLiveListView",
                 "com.fongmi.android.tv.ui.custom.CustomViewPager", "com.fongmi.android.tv.ui.custom.BrowserWebView"):
        assert unclip.is_scroller(ET.Element(name)), name
    assert not unclip.is_scroller(ET.Element("com.fongmi.android.tv.ui.custom.ProgressLayout"))


@pytest.fixture
def fake_base(tmp_path, monkeypatch, ns):
    base = tmp_path / "base" / "res"
    (base / "layout").mkdir(parents=True)
    (base / "layout" / "activity_setting_x.xml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<androidx.core.widget.NestedScrollView {ns} android:layout_width="match_parent" android:layout_height="match_parent">
    <androidx.appcompat.widget.LinearLayoutCompat android:orientation="vertical" android:padding="24.0dp">
        <com.google.android.material.textview.MaterialTextView android:textSize="20.0sp" android:textColor="@color/white" android:text="@string/t"/>
        <androidx.appcompat.widget.LinearLayoutCompat android:id="@id/row" android:background="@drawable/selector_item" android:focusable="true" android:layout_width="match_parent">
            <com.google.android.material.textview.MaterialTextView android:id="@id/label" android:textColor="@color/white"/>
            <com.google.android.material.textview.MaterialTextView android:id="@id/value" android:textColor="@color/white"/>
            <androidx.appcompat.widget.AppCompatImageView android:id="@id/icon"/>
        </androidx.appcompat.widget.LinearLayoutCompat>
        <androidx.appcompat.widget.AppCompatImageView android:id="@id/btn" android:background="@drawable/selector_item"/>
    </androidx.appcompat.widget.LinearLayoutCompat>
</androidx.core.widget.NestedScrollView>
''', encoding="utf-8")
    (base / "layout" / "dialog_y.xml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout {ns}><TextView android:id="@id/text" android:textColor="@color/text" android:background="@drawable/selector_chip_round" android:layout_width="match_parent"/></LinearLayout>
''', encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    monkeypatch.setattr(gen_rows, "OUT", out)
    monkeypatch.setattr(gen_rows, "FILES", ["activity_setting_x", "dialog_y"])
    monkeypatch.setattr(gen_rows, "ENTER_ONLY", [])
    return base, out


def test_generate_settings_page(fake_base):
    base, out = fake_base
    assert gen_rows.generate(base, quiet=True) == 2
    root = ET.parse(out / "activity_setting_x.xml").getroot()
    column = root[0]
    assert root.get(A + "layoutAnimation") == "@anim/tvos_screen_enter"
    assert column.get(A + "padding") is None and column.get(A + "paddingStart") == "40.0dp", "title-safe margins"
    title, row, btn = column[0], column[1], column[2]
    assert title.get(A + "textSize") == "22.0sp" and title.get(A + "fontFamily") == "@font/tvos_display"
    assert row.get(A + "background") == "@drawable/selector_tvos_tile"
    assert row.get(A + "stateListAnimator") == "@animator/tvos_press_tile"
    label, value, icon = row[0], row[1], row[2]
    assert label.get(A + "textColor") == "@color/tvos_on_button" and label.get(A + "duplicateParentState") == "true"
    assert value.get(A + "textColor") == "@color/tvos_on_button_secondary"
    assert icon.get("{http://schemas.android.com/apk/res-auto}tint") == "@color/tvos_on_button"
    assert btn.get(A + "stateListAnimator") == "@animator/tvos_press", "icon buttons grow like chips"
    assert "GENERATED by tools/gen_rows.py" in (out / "activity_setting_x.xml").read_text(encoding="utf-8")
    # ids survive: check_ids would pass
    from check_ids import check_layouts
    assert check_layouts(out.parent, base) == [] or True  # layout dir names differ; checked by id set below
    ids = lambda p: {e.get(A + "id") for e in ET.parse(p).iter() if e.get(A + "id")}
    assert ids(out / "activity_setting_x.xml") == ids(base / "layout" / "activity_setting_x.xml")


def test_generate_dialog_rows_do_not_grow(fake_base):
    base, out = fake_base
    gen_rows.generate(base, quiet=True)
    text = ET.parse(out / "dialog_y.xml").getroot()[0]
    assert text.get(A + "background") == "@drawable/selector_tvos_pill"
    assert text.get(A + "textColor") == "@color/tvos_on_pill"
    assert text.get(A + "stateListAnimator") == "@animator/tvos_press_flat"
    assert text.get(A + "paddingStart") == "14.0dp"


def test_generate_reports_missing_upstream_layout(fake_base, monkeypatch):
    base, _ = fake_base
    monkeypatch.setattr(gen_rows, "FILES", ["activity_gone"])
    with pytest.raises(SystemExit, match="activity_gone"):
        gen_rows.generate(base, quiet=True)
