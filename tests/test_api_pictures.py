"""Picture storage service and API tests (tasks 2.1-2.2, 3.1)."""

import io
from datetime import UTC, datetime
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage

from app.models import GasCylinder, Picture, Repairs
from app.services import pictures as pictures_service
from app.services.errors import BadRequest, Conflict


def _file(name, data=b"img"):
    return FileStorage(stream=io.BytesIO(data), filename=name)


def _make_repair(db, **kwargs):
    repair = Repairs(customer=1, vehicle=1, **kwargs)
    db.session.add(repair)
    db.session.commit()
    return repair


def _make_cylinder(db):
    cylinder = GasCylinder(full_weight=1.0, remaining_weight=1.0)
    db.session.add(cylinder)
    db.session.commit()
    return cylinder


def _upload_file(
    client,
    *,
    owner_type="repair",
    owner_id=1,
    name="photo.jpg",
    data=b"\xff\xd8\xffJFIF",
    uploaded_by="tester",
):
    return client.post(
        "/api/v1/pictures",
        data={
            "file": (io.BytesIO(data), name),
            "owner_type": owner_type,
            "owner_id": str(owner_id),
            "uploaded_by": uploaded_by,
        },
        content_type="multipart/form-data",
    )


def _raw_multipart(file_disposition, *, owner_type="repair", owner_id="1"):
    """A hand-built multipart body, so the file part's filename can be controlled."""
    boundary = "----TestBoundary"
    body = b"".join(
        [
            f"--{boundary}\r\n{file_disposition}\r\nContent-Type: image/jpeg\r\n\r\n".encode(),
            b"JPEGBYTES\r\n",
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="owner_type"'
                f"\r\n\r\n{owner_type}\r\n"
            ).encode(),
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="owner_id"'
                f"\r\n\r\n{owner_id}\r\n"
            ).encode(),
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return body, boundary


class TestStorageService:
    def test_name_and_folder_follow_owner_type_and_day(self, app, db):
        _make_repair(db)
        picture = pictures_service.store_upload(_file("photo.jpg"), "repair", 1, "tester")
        db.session.commit()

        today = datetime.now(UTC).date().isoformat()
        assert picture.path == f"repair/{today}-0001.jpg"
        assert (Path(app.config["UPLOAD_DIR"]) / picture.path).is_file()

    def test_sequence_increments_per_type_and_day(self, app, db):
        _make_repair(db)
        first = pictures_service.store_upload(_file("a.jpg"), "repair", 1)
        db.session.commit()
        second = pictures_service.store_upload(_file("b.jpg"), "repair", 1)
        db.session.commit()

        assert Path(first.path).name.endswith("-0001.jpg")
        assert Path(second.path).name.endswith("-0002.jpg")

    def test_each_owner_type_has_its_own_sequence(self, app, db):
        _make_repair(db)
        cylinder = _make_cylinder(db)

        repair_picture = pictures_service.store_upload(_file("r.jpg"), "repair", 1)
        db.session.commit()
        cylinder_picture = pictures_service.store_upload(
            _file("c.jpg"), "cylinder", cylinder.id
        )
        db.session.commit()

        assert Path(repair_picture.path).name.endswith("-0001.jpg")
        assert cylinder_picture.path.startswith("cylinder/")
        assert Path(cylinder_picture.path).name.endswith("-0001.jpg")

    def test_extension_is_preserved(self, app, db):
        _make_repair(db)
        picture = pictures_service.store_upload(_file("shot.PNG"), "repair", 1)
        db.session.commit()
        assert picture.path.endswith(".PNG")

    def test_delete_removes_file(self, app, db):
        _make_repair(db)
        picture = pictures_service.store_upload(_file("gone.jpg"), "repair", 1)
        db.session.commit()
        file_path = Path(app.config["UPLOAD_DIR"]) / picture.path
        assert file_path.is_file()

        db.session.delete(picture)
        db.session.commit()
        pictures_service.remove_file(picture)
        assert not file_path.is_file()


class TestOwnerValidation:
    def test_unknown_owner_type_rejected(self, app, db):
        with pytest.raises(BadRequest):
            pictures_service.store_upload(_file("a.jpg"), "bogus", 1)

    def test_missing_owner_id_rejected(self, app, db):
        with pytest.raises(BadRequest):
            pictures_service.store_upload(_file("a.jpg"), "repair", None)

    def test_unknown_owner_id_rejected(self, app, db):
        with pytest.raises(Conflict):
            pictures_service.store_upload(_file("a.jpg"), "repair", 99999)
        assert db.session.execute(db.select(Picture.id)).scalars().first() is None


class TestPicturesApi:
    def test_upload_with_owner_201_and_file_on_disk(self, client, app, db):
        _make_repair(db)
        response = _upload_file(client, owner_id=1)
        assert response.status_code == 201

        payload = response.get_json()
        assert payload["owner_type"] == "repair"
        assert payload["owner_id"] == 1
        assert payload["uploaded_by"] == "tester"
        assert payload["path"].startswith("repair/")
        assert payload["uploaded_date"] is not None
        assert (Path(app.config["UPLOAD_DIR"]) / payload["path"]).is_file()

    def test_upload_without_file_400(self, client, db):
        response = client.post(
            "/api/v1/pictures",
            data={"owner_type": "repair", "owner_id": "1"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert db.session.execute(db.select(Picture.id)).scalars().first() is None

    def test_upload_missing_owner_400(self, client, db):
        response = client.post(
            "/api/v1/pictures",
            data={"file": (io.BytesIO(b"x"), "a.jpg")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_upload_with_empty_filename_uses_mime_extension(self, client, app, db):
        _make_repair(db)
        body, boundary = _raw_multipart(
            'Content-Disposition: form-data; name="file"; filename=""'
        )
        response = client.post(
            "/api/v1/pictures",
            data=body,
            content_type=f"multipart/form-data; boundary={boundary}",
        )
        assert response.status_code == 201

        payload = response.get_json()
        assert payload["path"].startswith("repair/")
        assert payload["path"].endswith(".jpg")
        assert (Path(app.config["UPLOAD_DIR"]) / payload["path"]).is_file()

    def test_upload_without_filename_parameter_400(self, client, db):
        _make_repair(db)
        body, boundary = _raw_multipart(
            'Content-Disposition: form-data; name="file"'
        )
        response = client.post(
            "/api/v1/pictures",
            data=body,
            content_type=f"multipart/form-data; boundary={boundary}",
        )
        assert response.status_code == 400
        assert db.session.execute(db.select(Picture.id)).scalars().first() is None

    def test_upload_unknown_owner_409(self, client, db):
        response = _upload_file(client, owner_id=99999)
        assert response.status_code == 409
        assert db.session.execute(db.select(Picture.id)).scalars().first() is None

    def test_list_by_owner(self, client, db):
        _make_repair(db)
        cylinder = _make_cylinder(db)
        repair_picture = _upload_file(client, owner_type="repair", owner_id=1).get_json()
        cylinder_picture = _upload_file(
            client, owner_type="cylinder", owner_id=cylinder.id
        ).get_json()

        filtered = client.get("/api/v1/pictures?owner_type=repair&owner_id=1").get_json()
        assert [item["id"] for item in filtered] == [repair_picture["id"]]

        everything = client.get("/api/v1/pictures").get_json()
        assert {item["id"] for item in everything} == {
            repair_picture["id"],
            cylinder_picture["id"],
        }

    def test_incomplete_filter_400(self, client, db):
        assert client.get("/api/v1/pictures?owner_type=repair").status_code == 400
        assert client.get("/api/v1/pictures?owner_id=1").status_code == 400

    def test_list_and_detail(self, client, db):
        _make_repair(db)
        created = _upload_file(client).get_json()
        detail = client.get(f"/api/v1/pictures/{created['id']}").get_json()
        assert detail["path"] == created["path"]

    def test_unknown_picture_404(self, client, db):
        assert client.get("/api/v1/pictures/99999").status_code == 404
        assert client.get("/api/v1/pictures/99999/file").status_code == 404

    def test_download_returns_bytes_and_content_type(self, client, db):
        _make_repair(db)
        data = b"\x89PNG fake bytes"
        created = _upload_file(client, name="pic.png", data=data).get_json()
        response = client.get(f"/api/v1/pictures/{created['id']}/file")
        assert response.status_code == 200
        assert response.data == data
        assert response.content_type == "image/png"

    def test_download_missing_file_on_disk_404(self, client, app, db):
        _make_repair(db)
        created = _upload_file(client).get_json()
        (Path(app.config["UPLOAD_DIR"]) / created["path"]).unlink()
        assert client.get(f"/api/v1/pictures/{created['id']}/file").status_code == 404

    def test_delete_owned_picture_removes_record_and_file(self, client, app, db):
        _make_repair(db)
        created = _upload_file(client).get_json()
        file_path = Path(app.config["UPLOAD_DIR"]) / created["path"]
        assert file_path.is_file()

        response = client.delete(f"/api/v1/pictures/{created['id']}")
        assert response.status_code == 204
        assert not file_path.is_file()
        assert client.get(f"/api/v1/pictures/{created['id']}").status_code == 404
