# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DoctorScheduleWizard(models.TransientModel):
    _name = "doctor.schedule.wizard"
    _description = "Fill Doctor Schedule"

    doctor_id = fields.Many2one("hr.hospital.doctor", string="Doctor", required=True, domain="[('speciality_id','!=',False)]")
    week_start = fields.Date(string="Week Start", required=True, default=fields.Date.context_today)
    weeks_count = fields.Integer(string="Number of Weeks", default=1, required=True)

    schedule_type = fields.Selection(
        [
            ("standard", "Standard"),
            ("even_week", "Even week"),
            ("odd_week", "Odd week"),
        ],
        string="Schedule Type",
        default="standard",
        required=True,
    )

    mon = fields.Boolean("Monday", default=True)
    tue = fields.Boolean("Tuesday", default=True)
    wed = fields.Boolean("Wednesday", default=True)
    thu = fields.Boolean("Thursday", default=True)
    fri = fields.Boolean("Friday", default=True)
    sat = fields.Boolean("Saturday", default=False)
    sun = fields.Boolean("Sunday", default=False)

    start_time = fields.Float(string="Start Time", default=9.0)
    end_time = fields.Float(string="End Time", default=18.0)
    break_from = fields.Float(string="Break from", default=13.0)
    break_to = fields.Float(string="Break to", default=14.0)

    @api.constrains("weeks_count", "start_time", "end_time")
    def _check_values(self):
        for w in self:
            if w.weeks_count <= 0:
                raise ValidationError("Number of weeks must be > 0.")
            if w.end_time <= w.start_time:
                raise ValidationError("End time must be greater than start time.")

    def _week_parity_ok(self, date_):
        if self.schedule_type == "standard":
            return True
        week = date_.isocalendar()[1]
        if self.schedule_type == "even_week":
            return week % 2 == 0
        return week % 2 == 1

    def action_generate(self):
        self.ensure_one()
        Schedule = self.env["hr.hospital.doctor.schedule"]

        day_flags = {
            0: self.mon,
            1: self.tue,
            2: self.wed,
            3: self.thu,
            4: self.fri,
            5: self.sat,
            6: self.sun,
        }

        start = self.week_start
        if not start:
            raise ValidationError("You must specify the week start date.")

        # normalize to Monday of that week
        start_dt = fields.Date.to_date(start)
        start_dt = start_dt - timedelta(days=start_dt.weekday())

        to_create = []
        for w in range(self.weeks_count):
            week_base = start_dt + timedelta(days=7 * w)
            for weekday, enabled in day_flags.items():
                if not enabled:
                    continue
                day = week_base + timedelta(days=weekday)
                if not self._week_parity_ok(day):
                    continue

                # two slots if break is inside working hours
                if self.break_from and self.break_to and self.start_time < self.break_from < self.break_to < self.end_time:
                    to_create.append({
                        "doctor_id": self.doctor_id.id,
                        "date": day,
                        "day_of_week": str(weekday),
                        "type": "work_day",
                        "start_time": self.start_time,
                        "end_time": self.break_from,
                        "notes": "Auto schedule (before break)",
                    })
                    to_create.append({
                        "doctor_id": self.doctor_id.id,
                        "date": day,
                        "day_of_week": str(weekday),
                        "type": "work_day",
                        "start_time": self.break_to,
                        "end_time": self.end_time,
                        "notes": "Auto schedule (after break)",
                    })
                else:
                    to_create.append({
                        "doctor_id": self.doctor_id.id,
                        "date": day,
                        "day_of_week": str(weekday),
                        "type": "work_day",
                        "start_time": self.start_time,
                        "end_time": self.end_time,
                        "notes": "Auto schedule",
                    })

        if to_create:
            Schedule.create(to_create)

        return {"type": "ir.actions.act_window_close"}
