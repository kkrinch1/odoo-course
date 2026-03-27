from datetime import datetime, time, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestHrHospitalModels(TransactionCase):
    """Basic model tests for hr_hospital business logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.speciality = cls.env["hr.hospital.doctor.speciality"].create(
            {
                "name": "Test Therapy",
                "code": "TEST-THER",
            }
        )

    def _create_doctor(self, **extra_vals):
        """Create a doctor record with valid minimal data for tests."""
        vals = {
            "first_name": "John",
            "last_name": f"Doctor {fields.Datetime.now().timestamp()}",
            "license_number": f"LIC-{fields.Datetime.now().timestamp()}",
            "speciality_id": self.speciality.id,
        }
        vals.update(extra_vals)
        return self.env["hr.hospital.doctor"].create(vals)

    def _create_patient(self, **extra_vals):
        """Create a patient record with valid minimal data for tests."""
        vals = {
            "first_name": "Jane",
            "last_name": f"Patient {fields.Datetime.now().timestamp()}",
        }
        vals.update(extra_vals)
        return self.env["hr.hospital.patient"].create(vals)

    def _create_workday_schedule(self, doctor, planned_dt):
        """Add a workday slot that covers the planned visit datetime."""
        date_local = fields.Datetime.context_timestamp(doctor, planned_dt).date()
        self.env["hr.hospital.doctor.schedule"].create(
            {
                "doctor_id": doctor.id,
                "date": date_local,
                "type": "work_day",
                "start_time": 8.0,
                "end_time": 18.0,
            }
        )

    def test_compute_experience_years(self):
        """Doctor experience should be computed from the license issue date."""
        issue_date = fields.Date.context_today(self.env.user) - relativedelta(years=5)
        doctor = self._create_doctor(
            first_name="Eva",
            last_name="Experience",
            license_number="LIC-EXP-001",
            license_issue_date=issue_date,
        )

        self.assertEqual(doctor.experience_years, 5)

        doctor_without_date = self._create_doctor(
            first_name="NoDate",
            last_name="Doctor",
            license_number="LIC-EXP-002",
        )
        self.assertEqual(doctor_without_date.experience_years, 0)

    def test_check_mentor_rules(self):
        """Mentor validation should reject invalid mentor assignments."""
        doctor = self._create_doctor(
            first_name="Senior",
            last_name="Mentor",
            license_number="LIC-MENT-001",
        )
        another_doctor = self._create_doctor(
            first_name="Second",
            last_name="Doctor",
            license_number="LIC-MENT-003",
        )
        intern = self._create_doctor(
            first_name="Junior",
            last_name="Intern",
            license_number="LIC-MENT-002",
            is_intern=True,
        )

        with self.assertRaises(ValidationError):
            doctor.write({"mentor_id": doctor.id, "is_intern": True})

        with self.assertRaises(ValidationError):
            doctor.write({"mentor_id": intern.id, "is_intern": True})

        with self.assertRaises(ValidationError):
            doctor.write({"mentor_id": another_doctor.id})

    def test_action_set_done(self):
        """Completing a visit should set state to done and fill action_date."""
        doctor = self._create_doctor(
            first_name="Visit",
            last_name="Doctor",
            license_number="LIC-VIS-001",
        )
        patient = self._create_patient(
            first_name="Visit",
            last_name="Patient",
        )

        planned_date = fields.Date.context_today(self.env.user) - timedelta(days=1)
        while planned_date.weekday() >= 5:
            planned_date -= timedelta(days=1)

        planned_dt = fields.Datetime.to_datetime(
            datetime.combine(planned_date, time(hour=10, minute=0))
        )

        self._create_workday_schedule(doctor, planned_dt)

        visit = self.env["hr.hospital.patient.visit"].create(
            {
                "patient_id": patient.id,
                "doctor_id": doctor.id,
                "speciality_id": self.speciality.id,
                "planned_date": planned_dt,
                "visit_type": "initial",
            }
        )

        self.assertEqual(visit.state, "planned")
        self.assertFalse(visit.action_date)

        visit.action_set_done()

        self.assertEqual(visit.state, "done")
        self.assertTrue(visit.action_date)
