import os
import tempfile
import unittest

from app.db import init_db
from app import repository as repo


class BaseRepoTest(unittest.TestCase):
    def setUp(self):
        self.tmp_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.tmp_fd)
        init_db(self.db_path)

    def tearDown(self):
        os.remove(self.db_path)


class TestPeople(BaseRepoTest):
    def test_add_and_get_person(self):
        person_id = repo.add_person("Jane Doe", "jane@example.com", db_path=self.db_path)
        person = repo.get_person(person_id, db_path=self.db_path)
        self.assertEqual(person["name"], "Jane Doe")
        self.assertEqual(person["email"], "jane@example.com")

    def test_add_person_requires_name(self):
        with self.assertRaises(ValueError):
            repo.add_person("", db_path=self.db_path)

    def test_add_person_strips_whitespace(self):
        person_id = repo.add_person("  Jane Doe  ", db_path=self.db_path)
        person = repo.get_person(person_id, db_path=self.db_path)
        self.assertEqual(person["name"], "Jane Doe")

    def test_list_people_sorted_by_name(self):
        repo.add_person("Zoe", db_path=self.db_path)
        repo.add_person("Amy", db_path=self.db_path)
        people = repo.list_people(db_path=self.db_path)
        self.assertEqual([p["name"] for p in people], ["Amy", "Zoe"])

    def test_get_nonexistent_person_returns_none(self):
        self.assertIsNone(repo.get_person(999, db_path=self.db_path))

    def test_delete_person(self):
        person_id = repo.add_person("Temp Person", db_path=self.db_path)
        repo.delete_person(person_id, db_path=self.db_path)
        self.assertIsNone(repo.get_person(person_id, db_path=self.db_path))

    def test_deleting_person_cascades_to_hours_and_donations(self):
        person_id = repo.add_person("Cascade Test", db_path=self.db_path)
        repo.log_hours(person_id, "Helping out", 2.0, "2026-01-01", db_path=self.db_path)
        repo.log_donation(person_id, 50.0, "2026-01-01", db_path=self.db_path)

        repo.delete_person(person_id, db_path=self.db_path)

        self.assertEqual(repo.list_hours(person_id=person_id, db_path=self.db_path), [])
        self.assertEqual(repo.list_donations(person_id=person_id, db_path=self.db_path), [])


class TestVolunteerHours(BaseRepoTest):
    def setUp(self):
        super().setUp()
        self.person_id = repo.add_person("Test Volunteer", db_path=self.db_path)

    def test_log_hours(self):
        entry_id = repo.log_hours(
            self.person_id, "Sorting donations", 3.5, "2026-01-15", db_path=self.db_path
        )
        self.assertIsNotNone(entry_id)

    def test_log_hours_rejects_zero_or_negative(self):
        with self.assertRaises(ValueError):
            repo.log_hours(self.person_id, "Test", 0, "2026-01-15", db_path=self.db_path)
        with self.assertRaises(ValueError):
            repo.log_hours(self.person_id, "Test", -1, "2026-01-15", db_path=self.db_path)

    def test_log_hours_requires_activity(self):
        with self.assertRaises(ValueError):
            repo.log_hours(self.person_id, "", 2.0, "2026-01-15", db_path=self.db_path)

    def test_list_hours_for_person(self):
        repo.log_hours(self.person_id, "Activity A", 2.0, "2026-01-15", db_path=self.db_path)
        repo.log_hours(self.person_id, "Activity B", 1.5, "2026-01-16", db_path=self.db_path)
        entries = repo.list_hours(person_id=self.person_id, db_path=self.db_path)
        self.assertEqual(len(entries), 2)

    def test_total_hours(self):
        repo.log_hours(self.person_id, "A", 2.0, "2026-01-15", db_path=self.db_path)
        repo.log_hours(self.person_id, "B", 3.0, "2026-01-16", db_path=self.db_path)
        self.assertEqual(repo.total_hours(db_path=self.db_path), 5.0)

    def test_total_hours_by_person(self):
        other_id = repo.add_person("Other Volunteer", db_path=self.db_path)
        repo.log_hours(self.person_id, "A", 2.0, "2026-01-15", db_path=self.db_path)
        repo.log_hours(other_id, "B", 5.0, "2026-01-16", db_path=self.db_path)

        totals = repo.total_hours_by_person(db_path=self.db_path)
        totals_by_id = {t["person_id"]: t["total_hours"] for t in totals}
        self.assertEqual(totals_by_id[self.person_id], 2.0)
        self.assertEqual(totals_by_id[other_id], 5.0)

    def test_delete_hours_entry(self):
        entry_id = repo.log_hours(self.person_id, "A", 2.0, "2026-01-15", db_path=self.db_path)
        repo.delete_hours_entry(entry_id, db_path=self.db_path)
        entries = repo.list_hours(person_id=self.person_id, db_path=self.db_path)
        self.assertEqual(len(entries), 0)


class TestDonations(BaseRepoTest):
    def setUp(self):
        super().setUp()
        self.person_id = repo.add_person("Test Donor", db_path=self.db_path)

    def test_log_donation(self):
        entry_id = repo.log_donation(self.person_id, 25.50, "2026-01-15", db_path=self.db_path)
        self.assertIsNotNone(entry_id)

    def test_log_donation_rejects_zero_or_negative(self):
        with self.assertRaises(ValueError):
            repo.log_donation(self.person_id, 0, "2026-01-15", db_path=self.db_path)
        with self.assertRaises(ValueError):
            repo.log_donation(self.person_id, -10, "2026-01-15", db_path=self.db_path)

    def test_donation_defaults_to_gbp(self):
        entry_id = repo.log_donation(self.person_id, 10.0, "2026-01-15", db_path=self.db_path)
        donations = repo.list_donations(person_id=self.person_id, db_path=self.db_path)
        self.assertEqual(donations[0]["currency"], "GBP")

    def test_total_donations(self):
        repo.log_donation(self.person_id, 10.0, "2026-01-15", db_path=self.db_path)
        repo.log_donation(self.person_id, 15.50, "2026-01-16", db_path=self.db_path)
        self.assertEqual(repo.total_donations(db_path=self.db_path), 25.50)

    def test_total_donations_by_person(self):
        other_id = repo.add_person("Other Donor", db_path=self.db_path)
        repo.log_donation(self.person_id, 10.0, "2026-01-15", db_path=self.db_path)
        repo.log_donation(other_id, 100.0, "2026-01-16", db_path=self.db_path)

        totals = repo.total_donations_by_person(db_path=self.db_path)
        totals_by_id = {t["person_id"]: t["total_donated"] for t in totals}
        self.assertEqual(totals_by_id[self.person_id], 10.0)
        self.assertEqual(totals_by_id[other_id], 100.0)

    def test_delete_donation_entry(self):
        entry_id = repo.log_donation(self.person_id, 10.0, "2026-01-15", db_path=self.db_path)
        repo.delete_donation_entry(entry_id, db_path=self.db_path)
        donations = repo.list_donations(person_id=self.person_id, db_path=self.db_path)
        self.assertEqual(len(donations), 0)


class TestSummary(BaseRepoTest):
    def test_summary_on_empty_db(self):
        stats = repo.summary(db_path=self.db_path)
        self.assertEqual(stats["people_count"], 0)
        self.assertEqual(stats["total_hours"], 0)
        self.assertEqual(stats["total_donations"], 0)

    def test_summary_with_data(self):
        person_id = repo.add_person("Someone", db_path=self.db_path)
        repo.log_hours(person_id, "Helping", 4.0, "2026-01-15", db_path=self.db_path)
        repo.log_donation(person_id, 20.0, "2026-01-15", db_path=self.db_path)

        stats = repo.summary(db_path=self.db_path)
        self.assertEqual(stats["people_count"], 1)
        self.assertEqual(stats["total_hours"], 4.0)
        self.assertEqual(stats["total_donations"], 20.0)


if __name__ == "__main__":
    unittest.main()
