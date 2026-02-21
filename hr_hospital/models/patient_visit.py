# -*- coding: utf-8 -*-
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalPatientVisit(models.Model):
    _name = "hr.hospital.patient.visit"
    _description = "Patient Visits"
    _rec_name = "name"
    _order = "planned_date desc, id desc"

    name = fields.Char(string="Visit", compute="_compute_name", store=True, readonly=True)

    # ✅ Счетчик для Pivot: каждая запись = 1, а в pivot суммируем => получаем COUNT
    visit_count = fields.Integer(
        string="Visits",
        default=1,
        readonly=True,
        aggregator="sum",  # Odoo 18+
        help="Technical measure field for pivot tables: each visit contributes 1.",
    )

    state = fields.Selection(
        [
            ("planned", "Planned"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
            ("no_show", "No-show"),
        ],
        default="planned",
        required=True,
    )

    planned_date = fields.Datetime(string="Scheduled Date & Time", required=True)
    action_date = fields.Datetime(string="Actual Date & Time", readonly=True)

    speciality_id = fields.Many2one(
        "hr.hospital.doctor.speciality",
        string="Speciality",
        index=True,
    )

    # ✅ 8.2: динамический список доступных врачей (по спец. + расписанию)
    available_doctor_ids = fields.Many2many(
        "hr.hospital.doctor",
        compute="_compute_available_doctor_ids",
        string="Available Doctors",
        store=False,
    )

    doctor_id = fields.Many2one(
        "hr.hospital.doctor",
        string="Doctor",
        required=True,
        # базовый домен (останется как safety-net)
        domain="[('license_number','!=',False), ('active','=',True)]",
    )
    patient_id = fields.Many2one("hr.hospital.patient", string="Patient", required=True)

    visit_type = fields.Selection(
        [
            ("initial", "Initial"),
            ("repeat", "Follow-up"),
            ("preventive", "Preventive"),
            ("emergency", "Emergency"),
        ],
        string="Visit Type",
        default="initial",
        required=True,
    )

    recommendation = fields.Html(string="Recommendations")

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    cost = fields.Monetary(string="Visit Cost", currency_field="currency_id")

    diagnoses_ids = fields.One2many(
        "hr.hospital.medical.diagnosis",
        "visit_id",
        string="Diagnoses",
    )

    diagnosis_count = fields.Integer(
        string="Diagnosis Count",
        compute="_compute_diagnosis_count",
        store=True,
    )

    reschedule_reason = fields.Text(string="Reschedule Reason", readonly=True)

    # -------------------------
    # HELPERS
    # -------------------------
    def _get_local_date_time_float(self, dt_utc):
        """Convert UTC dt to user's local date + float time (e.g. 13.5)."""
        dt_local = fields.Datetime.context_timestamp(self, dt_utc)
        date_local = dt_local.date()
        time_float = dt_local.hour + (dt_local.minute / 60.0) + (dt_local.second / 3600.0)
        return date_local, time_float

    def _schedule_date_domain(self, date_local):
        """
        Schedule can be either:
        - specific date (date = date_local)
        OR
        - generic weekly (date is False + day_of_week matches)
        """
        day_str = str(date_local.weekday())  # Monday=0 .. Sunday=6
        return [
            "|",
            ("date", "=", date_local),
            "&",
            ("date", "=", False),
            ("day_of_week", "=", day_str),
        ]

    # -------------------------
    # COMPUTES
    # -------------------------
    @api.depends("patient_id", "doctor_id", "planned_date")
    def _compute_name(self):
        for rec in self:
            patient = rec.patient_id.display_name or ""
            doctor = rec.doctor_id.display_name or ""
            date_str = ""
            if rec.planned_date:
                day = fields.Date.to_date(rec.planned_date)
                date_str = fields.Date.to_string(day)
            parts = [p for p in [patient, doctor, date_str] if p]
            rec.name = " / ".join(parts) if parts else "Visit"

    @api.depends("diagnoses_ids")
    def _compute_diagnosis_count(self):
        for rec in self:
            rec.diagnosis_count = len(rec.diagnoses_ids)

    @api.depends("speciality_id", "planned_date")
    def _compute_available_doctor_ids(self):
        Doctor = self.env["hr.hospital.doctor"]
        Schedule = self.env["hr.hospital.doctor.schedule"]

        for rec in self:
            # базовые кандидаты
            base_domain = [
                ("active", "=", True),
                ("license_number", "!=", False),
            ]
            if rec.speciality_id:
                base_domain.append(("speciality_id", "=", rec.speciality_id.id))

            candidates = Doctor.search(base_domain)

            # если дата/время не выбраны — просто по спец. (и лицензии)
            if not rec.planned_date:
                rec.available_doctor_ids = candidates
                continue

            date_local, time_float = rec._get_local_date_time_float(rec.planned_date)

            # по ТЗ: исключаем выходные (даже если кто-то расписание поставил)
            if date_local.weekday() >= 5:
                rec.available_doctor_ids = Doctor.browse([])
                continue

            if not candidates:
                rec.available_doctor_ids = Doctor.browse([])
                continue

            # рабочие слоты, покрывающие выбранное время
            work_domain = [
                ("doctor_id", "in", candidates.ids),
                ("type", "=", "work_day"),
                ("start_time", "<=", time_float),
                ("end_time", ">", time_float),
            ] + rec._schedule_date_domain(date_local)

            work_slots = Schedule.search(work_domain)
            available_ids = set(work_slots.mapped("doctor_id").ids)

            if not available_ids:
                rec.available_doctor_ids = Doctor.browse([])
                continue

            # исключаем если на эту дату есть vacation/sick/conference (любой)
            absence_domain = [
                ("doctor_id", "in", list(available_ids)),
                ("type", "in", ["vacation", "sick_leave", "conference"]),
            ] + rec._schedule_date_domain(date_local)

            abs_slots = Schedule.search(absence_domain)
            absent_ids = set(abs_slots.mapped("doctor_id").ids)

            available_ids -= absent_ids
            rec.available_doctor_ids = Doctor.browse(list(available_ids))

    # ------------------------
    # ONCHANGE
    # -------------------------
    @api.onchange("patient_id")
    def _onchange_patient_allergies_warning(self):
        for rec in self:
            if rec.patient_id and rec.patient_id.allergies:
                return {
                    "warning": {
                        "title": "Warning: allergies",
                        "message": rec.patient_id.allergies,
                    }
                }

    @api.onchange("speciality_id", "planned_date")
    def _onchange_availability_reset_doctor(self):
        """
        Если поменяли спец/дату — текущий doctor_id может стать недоступным.
        Тогда сбросим его, чтобы юзер не сохранил “старого” доктора.
        """
        for rec in self:
            if rec.planned_date:
                date_local, _ = rec._get_local_date_time_float(rec.planned_date)
                if date_local.weekday() >= 5:
                    return {
                        "warning": {
                            "title": "Weekend",
                            "message": "Visits cannot be scheduled on weekends. Choose a weekday.",
                        }
                    }

            if rec.doctor_id and rec.available_doctor_ids and rec.doctor_id not in rec.available_doctor_ids:
                rec.doctor_id = False
                return {
                    "warning": {
                        "title": "Doctor not available",
                        "message": "Selected doctor is not available for this speciality/date/time. Please choose another.",
                    }
                }

    # -------------------------
    # BUTTONS
    # -------------------------
    def action_set_planned(self):
        self.write({"state": "planned", "action_date": False})

    def action_set_no_show(self):
        self.write({"state": "no_show", "action_date": False})

    def action_set_cancelled(self):
        self.write({"state": "cancelled", "action_date": False})

    def action_set_done(self):
        for rec in self:
            rec.write({"state": "done", "action_date": fields.Datetime.now()})

    # -------------------------
    # VALIDATION
    # -------------------------
    @api.constrains("doctor_id")
    def _check_doctor_has_license(self):
        for rec in self:
            if rec.doctor_id and not rec.doctor_id.license_number:
                raise ValidationError("You cannot assign a doctor without a license number.")

    @api.constrains("action_date", "state")
    def _check_action_date_done(self):
        for rec in self:
            if rec.action_date and rec.state != "done":
                raise ValidationError("Actual date/time can be set only for a completed visit.")

    # ✅ ТЗ: action_date не раньше planned_date (трактуем “дослідження/візит”)
    @api.constrains("planned_date", "action_date", "state")
    def _check_action_date_not_before_planned_date(self):
        for rec in self:
            if rec.state != "done":
                continue
            if rec.planned_date and rec.action_date and rec.action_date < rec.planned_date:
                raise ValidationError("Actual date/time cannot be earlier than scheduled date/time.")

    # ✅ 8.2 + безопасность: нельзя записать если доктор не работает / выходной / отпуск
    @api.constrains("doctor_id", "planned_date")
    def _check_doctor_available_by_schedule(self):
        Schedule = self.env["hr.hospital.doctor.schedule"]

        for rec in self:
            if not rec.doctor_id or not rec.planned_date:
                continue

            date_local, time_float = rec._get_local_date_time_float(rec.planned_date)

            # выходные запрещены
            if date_local.weekday() >= 5:
                raise ValidationError("Visits cannot be scheduled on weekends.")

            # если есть vacation/sick/conference — запрещаем
            absence_domain = [
                ("doctor_id", "=", rec.doctor_id.id),
                ("type", "in", ["vacation", "sick_leave", "conference"]),
            ] + rec._schedule_date_domain(date_local)

            if Schedule.search_count(absence_domain):
                raise ValidationError("Doctor is not available on this date (vacation/sick leave/conference).")

            # должен быть work_day слот, покрывающий время
            work_domain = [
                ("doctor_id", "=", rec.doctor_id.id),
                ("type", "=", "work_day"),
                ("start_time", "<=", time_float),
                ("end_time", ">", time_float),
            ] + rec._schedule_date_domain(date_local)

            if not Schedule.search_count(work_domain):
                raise ValidationError("Doctor has no working schedule covering this time.")

    @api.constrains("patient_id", "doctor_id", "planned_date", "state")
    def _check_one_visit_per_day(self):
        for rec in self:
            if not rec.patient_id or not rec.doctor_id or not rec.planned_date:
                continue
            if rec.state == "cancelled":
                continue

            day = fields.Date.to_date(rec.planned_date)
            start_dt = fields.Datetime.to_datetime(day)
            end_dt = start_dt + timedelta(days=1)

            cnt = self.search_count(
                [
                    ("id", "!=", rec.id),
                    ("patient_id", "=", rec.patient_id.id),
                    ("doctor_id", "=", rec.doctor_id.id),
                    ("state", "!=", "cancelled"),
                    ("planned_date", ">=", start_dt),
                    ("planned_date", "<", end_dt),
                ]
            )
            if cnt:
                raise ValidationError("The patient cannot be scheduled with this doctor more than once per day.")

    def action_open_pivot_current_month(self):
        today = fields.Date.context_today(self)
        start = today.replace(day=1)
        end = start + relativedelta(months=1)

        pivot_view = self.env.ref("hr_hospital.view_hr_hospital_patient_visit_pivot").id
        search_view = self.env.ref("hr_hospital.view_hr_hospital_patient_visit_search").id

        return {
            "type": "ir.actions.act_window",
            "name": "Visits Pivot (This month)",
            "res_model": "hr.hospital.patient.visit",
            "view_mode": "pivot",
            "views": [(pivot_view, "pivot")],
            "search_view_id": search_view,
            "domain": [("planned_date", ">=", start), ("planned_date", "<", end)],
            "context": {},
        }

    # -------------------------
    # OVERRIDES
    # -------------------------
    def write(self, vals):
        protected = {"doctor_id", "patient_id", "planned_date"}
        if protected.intersection(vals.keys()):
            for rec in self:
                if rec.state in ("done", "no_show") or rec.action_date:
                    raise ValidationError(
                        "You cannot change the doctor/date/time for a visit that has already occurred."
                    )
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.diagnoses_ids:
                raise ValidationError("You cannot delete a visit that has diagnoses.")
        return super().unlink()
