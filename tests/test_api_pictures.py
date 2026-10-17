"""Picture storage service and API tests (tasks 4.1-4.2)."""

import io
from pathlib import Path

from app.models import GasCylinder, Picture, ServicePart
from app.services import pictures as pictures_service


def _upload_file(client, name="photo.jpg", data=b"\xff\xd8\xffJFIF", content_type="image/jpeg"):
    return client.post(
        "/api/v1/pictures",
        data={"file": (io.BytesIO(data), name), "uploaded_by": "tester"},
        content_type="multipart/form-data",
    )


class TestStorageService:
    def test_store_generates_unique_name_and_preserves_extension(self, app, db):
        first = pictures_service.store_upload(
            _file("photo.jpg"), "tester"
        )
        db.session.add(first)
        db.session.commit()
        second = pictures_service.store_upload(_file("photo.jpg"), "tester")
        db.session.add(second)
        db.session.commit()

        base = Path(app.config["UPLOAD_DIR"]) / "pictures"
        names = {Path(p.path).name for p in (first, second)}
        assert len(names) == 2, "stored names must be unique"
        assert all(name.endswith(".jpg") for name in names), "extension preserved"
        assert (base / Path(first.path).name).is_file()

    def test_stored_path_is_relative(self, app, db):
        first = pictures_service.store_upload(_file("a.png"), "tester")
        db.session.add(first)
        db.session.commit()
        assert first.path.startswith("pictures/")
        assert not Path(first.path).is_absolute()

    def test_delete_removes_file(self, app, db):
        first = pictures_service.store_upload(_file("gone.jpg"), "tester")
        db.session.add(first)
        db.session.commit()
        file_path = Path(app.config["UPLOAD_DIR"]) / first.path
        assert file_path.is_file()

        # Mimic the endpoint: delete the record, commit, then remove the file.
        from app.extensions import db as dbext

        dbext.session.delete(first)
        dbext.session.commit()
        pictures_service.remove_file(first)
        assert not file_path.is_file()


def _file(name, data=b"img"):
    from werkzeug.datastructures import FileStorage

    return FileStorage(stream=io.BytesIO(data), filename=name)


class TestPicturesApi:
    def test_upload_201_and_file_on_disk(self, client, app, db):
        response = _upload_file(client)
        assert response.status_code == 201
        payload = response.get_json()
        assert payload["id"] is not None
        assert payload["path"].startswith("pictures/")
        assert payload["uploaded_by"] == "tester"
        assert payload["uploaded_date"] is not None
        assert (Path(app.config["UPLOAD_DIR"]) / payload["path"]).is_file()

    def test_upload_without_file_400(self, client, db):
        response = client.post("/api/v1/pictures", data={}, content_type="multipart/form-data")
        assert response.status_code == 400
        assert db.session.execute(db.select(Picture.id)).scalars().first() is None

    def test_list_and_detail(self, client, db):
        created = _upload_file(client).get_json()
        listing = client.get("/api/v1/pictures").get_json()
        assert any(item["id"] == created["id"] for item in listing)
        detail = client.get(f"/api/v1/pictures/{created['id']}").get_json()
        assert detail["path"] == created["path"]

    def test_unknown_picture_404(self, client, db):
        assert client.get("/api/v1/pictures/99999").status_code == 404
        assert client.get("/api/v1/pictures/99999/file").status_code == 404

    def test_download_returns_bytes_and_content_type(self, client, db):
        data = b"\x89PNG fake bytes"
        created = _upload_file(client, name="pic.png", data=data, content_type="image/png")
        assert created.status_code == 201
        picture_id = created.get_json()["id"]
        response = client.get(f"/api/v1/pictures/{picture_id}/file")
        assert response.status_code == 200
        assert response.data == data
        assert response.content_type == "image/png"

    def test_download_missing_file_on_disk_404(self, client, app, db):
        created = _upload_file(client).get_json()
        # Remove the stored file behind the app's back.
        (Path(app.config["UPLOAD_DIR"]) / created["path"]).unlink()
        assert client.get(f"/api/v1/pictures/{created['id']}/file").status_code == 404

    def test_delete_referenced_conflict_cylinder(self, client, app, db):
        created = _upload_file(client).get_json()
        file_path = Path(app.config["UPLOAD_DIR"]) / created["path"]
        db.session.add(
            GasCylinder(picture_ref=created["id"], full_weight=1.0, remaining_weight=1.0)
        )
        db.session.commit()
        response = client.delete(f"/api/v1/pictures/{created['id']}")
        assert response.status_code == 409
        # The record survives AND its file must still be on disk.
        assert client.get(f"/api/v1/pictures/{created['id']}").status_code == 200
        assert file_path.is_file()

    def test_delete_referenced_conflict_part(self, client, db):
        created = _upload_file(client).get_json()
        db.session.add(ServicePart(name="P", picture_ref=created["id"]))
        db.session.commit()
        response = client.delete(f"/api/v1/pictures/{created['id']}")
        assert response.status_code == 409

    def test_delete_unreferenced_removes_record_and_file(self, client, app, db):
        created = _upload_file(client).get_json()
        file_path = Path(app.config["UPLOAD_DIR"]) / created["path"]
        assert file_path.is_file()
        response = client.delete(f"/api/v1/pictures/{created['id']}")
        assert response.status_code == 204
        assert not file_path.is_file()
        assert client.get(f"/api/v1/pictures/{created['id']}").status_code == 404
