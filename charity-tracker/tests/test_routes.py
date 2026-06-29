import os
import tempfile
import unittest

import app.main as main_module
from app.db import init_db
from app import repository as repo


class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.tmp_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.tmp_fd)
        init_db(self.db_path)

        # Point the app's module-level DB_PATH at our temp db for this test
        main_module.DB_PATH = self.db_path
        self.app = main_module.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        os.remove(self.db_path)

    def test_dashboard_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard", response.data)

    def test_people_list_loads(self):
        response = self.client.get("/people")
        self.assertEqual(response.status_code, 200)

    def test_add_person_via_form(self):
        response = self.client.post(
            "/people/add", data={"name": "Form Test Person", "email": "", "notes": ""}
        )
        self.assertEqual(response.status_code, 302)  # redirect after success
        people = repo.list_people(db_path=self.db_path)
        self.assertEqual(len(people), 1)
        self.assertEqual(people[0]["name"], "Form Test Person")

    def test_add_person_with_blank_name_does_not_crash(self):
        response = self.client.post("/people/add", data={"name": "", "email": "", "notes": ""})
        self.assertEqual(response.status_code, 302)
        people = repo.list_people(db_path=self.db_path)
        self.assertEqual(len(people), 0)

    def test_hours_list_loads(self):
        response = self.client.get("/hours")
        self.assertEqual(response.status_code, 200)

    def test_log_hours_via_form(self):
        person_id = repo.add_person("Hour Logger", db_path=self.db_path)
        response = self.client.post(
            "/hours/add",
            data={
                "person_id": str(person_id),
                "activity": "Packed food parcels",
                "hours": "2.5",
                "date_logged": "2026-01-15",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        entries = repo.list_hours(person_id=person_id, db_path=self.db_path)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["hours"], 2.5)

    def test_donations_list_loads(self):
        response = self.client.get("/donations")
        self.assertEqual(response.status_code, 200)

    def test_log_donation_via_form(self):
        person_id = repo.add_person("Donor Test", db_path=self.db_path)
        response = self.client.post(
            "/donations/add",
            data={
                "person_id": str(person_id),
                "amount": "42.50",
                "date_received": "2026-01-15",
                "currency": "GBP",
                "method": "Bank transfer",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        donations = repo.list_donations(person_id=person_id, db_path=self.db_path)
        self.assertEqual(len(donations), 1)
        self.assertEqual(donations[0]["amount"], 42.50)

    def test_person_detail_loads(self):
        person_id = repo.add_person("Detail Test", db_path=self.db_path)
        response = self.client.get(f"/people/{person_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Detail Test", response.data)

    def test_person_detail_for_nonexistent_person_redirects(self):
        response = self.client.get("/people/9999")
        self.assertEqual(response.status_code, 302)

    def test_delete_person_via_form(self):
        person_id = repo.add_person("To Delete", db_path=self.db_path)
        response = self.client.post(f"/people/{person_id}/delete")
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(repo.get_person(person_id, db_path=self.db_path))


if __name__ == "__main__":
    unittest.main()
