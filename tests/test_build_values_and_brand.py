"""build.merge_values / rebrand_manifest / read_properties, without apktool."""

import xml.etree.ElementTree as ET

import pytest

import build


def test_merge_replaces_in_place_and_adds_new(tmp_path):
    target, skin = tmp_path / "values", tmp_path / "skin"
    target.mkdir(), skin.mkdir()
    (target / "styles.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        '    <style name="Theme.Base" parent="@style/X"><item name="a">1</item></style>\n'
        '    <style name="Other"><item name="b">2</item></style>\n</resources>\n', encoding="utf-8")
    (target / "colors.xml").write_text('<resources><color name="white">#fff</color></resources>', encoding="utf-8")
    (skin / "styles_tvos.xml").write_text(
        '<resources><style name="Theme.Base" parent="@style/Y"><item name="c">3</item></style>'
        '<color name="tvos_canvas">#050917</color></resources>', encoding="utf-8")
    replaced, added = build.merge_values(skin, target)
    assert (replaced, added) == (1, 1)
    styles = ET.parse(target / "styles.xml").getroot()
    base = [s for s in styles if s.get("name") == "Theme.Base"][0]
    assert base.get("parent") == "@style/Y"
    assert [i.get("name") for i in base] == ["c"], "old items are dropped, new ones take their place"
    assert [s.get("name") for s in styles] == ["Theme.Base", "Other"], "order and untouched entries kept"
    new = ET.parse(target / "skin_styles_tvos.xml").getroot()
    assert [(e.tag, e.get("name")) for e in new] == [("color", "tvos_canvas")]
    assert "white" in (target / "colors.xml").read_text()


def test_merge_keys_include_item_type(tmp_path):
    target, skin = tmp_path / "values", tmp_path / "skin"
    target.mkdir(), skin.mkdir()
    (target / "ids.xml").write_text('<resources><item type="id" name="x"/><item type="fraction" name="x">1%</item></resources>', encoding="utf-8")
    (skin / "f.xml").write_text('<resources><item type="fraction" name="x">2%</item></resources>', encoding="utf-8")
    assert build.merge_values(skin, target) == (1, 0)
    items = ET.parse(target / "ids.xml").getroot()
    assert [(i.get("type"), i.text) for i in items] == [("id", None), ("fraction", "2%")]


def test_merge_ignores_public_xml(tmp_path):
    target, skin = tmp_path / "values", tmp_path / "skin"
    target.mkdir(), skin.mkdir()
    (target / "public.xml").write_text('<resources><public type="color" name="c" id="0x7f010000"/></resources>', encoding="utf-8")
    (skin / "c.xml").write_text('<resources><color name="c">#000</color></resources>', encoding="utf-8")
    assert build.merge_values(skin, target) == (0, 1)
    assert "0x7f010000" in (target / "public.xml").read_text()


MANIFEST = '''<manifest package="com.fongmi.android.tv">
    <permission android:name="com.fongmi.android.tv.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"/>
    <application>
        <activity android:name="com.fongmi.android.tv.ui.activity.HomeActivity" android:exported="true">
            <intent-filter><action android:name="android.intent.action.MAIN"/></intent-filter>
        </activity>
        <receiver android:name="x"><intent-filter><action android:name="com.fongmi.android.tv.stop"/></intent-filter></receiver>
        <provider android:authorities="com.fongmi.android.tv.provider" android:name="androidx.core.content.FileProvider"/>
        <provider android:authorities="com.fongmi.android.tv.androidx-startup" android:name="androidx.startup.InitializationProvider">
            <meta-data android:name="com.fongmi.android.tv.Startup" android:value="androidx.startup"/>
        </provider>
    </application>
</manifest>'''
CFG = {"package": "local.guangying.tv", "upstream_package": "com.fongmi.android.tv", "label": "光影", "ffalcon_card": "card.png"}


def test_rebrand_manifest():
    out = build.rebrand_manifest(MANIFEST, CFG)
    assert 'package="local.guangying.tv"' in out
    assert 'android:authorities="local.guangying.tv.provider"' in out
    assert 'android:authorities="local.guangying.tv.androidx-startup"' in out
    assert "local.guangying.tv.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION" in out
    assert out.count("local.guangying.tv.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION") == 1
    # code-side constants (BuildConfig.APPLICATION_ID, class names) are not rewritten
    assert 'android:name="com.fongmi.android.tv.ui.activity.HomeActivity"' in out
    assert 'android:name="com.fongmi.android.tv.stop"' in out
    assert 'android:name="com.fongmi.android.tv.Startup"' in out
    # card meta-data sits inside HomeActivity, once
    i = out.index('HomeActivity"')
    assert out.index('beidouui_icon', i) < out.index("</activity>", i)
    assert build.rebrand_manifest(out.replace(CFG["package"], CFG["upstream_package"]), CFG).count("beidouui_icon") == 1


def test_rebrand_rejects_foreign_manifest():
    with pytest.raises(SystemExit, match="manifest package"):
        build.rebrand_manifest('<manifest package="other.app"/>', CFG)
    with pytest.raises(SystemExit, match="HomeActivity"):
        build.rebrand_manifest('<manifest package="com.fongmi.android.tv"/>', CFG)


def test_read_properties_keeps_spaces_and_skips_comments(tmp_path):
    p = tmp_path / "skin.properties"
    p.write_text("# key\nstoreFile = keys/skin.jks\nkeyAlias=skin\nstorePassword=pa ss=word \n", encoding="utf-8")
    assert build.read_properties(p) == {"storeFile": "keys/skin.jks", "keyAlias": "skin", "storePassword": "pa ss=word"}
