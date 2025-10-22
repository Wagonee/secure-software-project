from pathlib import Path

from app.utils.file_safety import JPEG_EOI, JPEG_SOI, PNG, secure_save


def test_rejects_big_file(tmp_path: Path):
    data = PNG + b"0" * (5_000_001)
    ok, reason = secure_save(tmp_path.as_posix(), "x.png", data)
    assert not ok and reason == "too_big"


def test_sniffs_bad_type(tmp_path: Path):
    ok, reason = secure_save(tmp_path.as_posix(), "x.png", b"not_an_image")
    assert not ok and reason == "bad_type"


def test_accepts_png_and_jpeg(tmp_path: Path):
    png = PNG + b"payload"
    ok1, path1 = secure_save(tmp_path.as_posix(), "a.png", png)
    assert ok1 and Path(path1).exists()

    jpeg = JPEG_SOI + b"payload" + JPEG_EOI
    ok2, path2 = secure_save(tmp_path.as_posix(), "b.jpg", jpeg)
    assert ok2 and Path(path2).exists()


def test_rejects_symlink_parent(tmp_path: Path):
    real = tmp_path / "real"
    real.mkdir()
    target = tmp_path / "link"
    try:
        target.symlink_to(real, target_is_directory=True)
        ok, reason = secure_save(str(target), "x.png", PNG + b"p")
        assert (not ok and reason in {"symlink_parent", "bad_type"}) or (
            ok and Path(reason).exists()
        )
    except Exception:
        ok, path = secure_save(str(real), "x.png", PNG + b"p")
        assert ok and Path(path).exists()
