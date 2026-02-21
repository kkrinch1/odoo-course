# -*- coding: utf-8 -*-
from odoo import fields, models


class HrHospitalDoctorSchedule(models.Model):
    _name = "hr.hospital.doctor.schedule"
    _description = "Doctor Schedule"
    _order = "doctor_id, date, day_of_week, start_time"

    doctor_id = fields.Many2one(
        "hr.hospital.doctor",
        string="Doctor",
        required=True,
        ondelete="cascade",
        index=True,
    )

    day_of_week = fields.Selection(
        [
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Day of Week",
    )

    date = fields.Date(string="Specific Date")

    start_time = fields.Float(string="Start Time", required=True)
    end_time = fields.Float(string="End Time", required=True)

    type = fields.Selection(
        [
            ("work_day", "Work Day"),
            ("vacation", "Vacation"),
            ("sick_leave", "Sick Leave"),
            ("conference", "Conference"),
        ],
        string="Type",
        default="work_day",
        required=True,
    )

    notes = fields.Char(string="Notes")

    # ------------------------------------------------------------
    # SQL CONSTRAINTS (Odoo 19+)
    # ------------------------------------------------------------
    _time_order_chk = models.Constraint(
        "CHECK(end_time > start_time)",
        "End time must be greater than start time.",
    )
