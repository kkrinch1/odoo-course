# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RescheduleVisitWizard(models.TransientModel):
    _name = "reschedule.visit.wizard"
    _description = "Reschedule Visit"

    visit_id = fields.Many2one(
        "hr.hospital.patient.visit",
        string="Current Visit",
        readonly=True,
        required=True,
    )
    new_doctor_id = fields.Many2one(
        "hr.hospital.doctor",
        string="New Doctor",
        domain="[('license_number','!=',False)]",
    )
    new_date = fields.Date(string="New Date", required=True)
    new_time = fields.Float(string="New Time", required=True)
    reason = fields.Text(string="Reschedule Reason", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = dict(self.env.context or {})
        visit_id = ctx.get("default_visit_id") or ctx.get("active_id")
        if visit_id:
            visit = self.env["hr.hospital.patient.visit"].browse(visit_id).exists()
            if visit:
                res.setdefault("visit_id", visit.id)
                # sensible defaults
                if "new_doctor_id" in fields_list and not res.get("new_doctor_id"):
                    res["new_doctor_id"] = visit.doctor_id.id
                if visit.planned_date:
                    planned_dt = fields.Datetime.context_timestamp(self, visit.planned_date)
                    if "new_date" in fields_list and not res.get("new_date"):
                        res["new_date"] = planned_dt.date()
                    if "new_time" in fields_list and not res.get("new_time"):
                        res["new_time"] = planned_dt.hour + planned_dt.minute / 60.0
        return res

    @api.constrains("new_time")
    def _check_new_time(self):
        for w in self:
            if w.new_time is not False and (w.new_time < 0.0 or w.new_time >= 24.0):
                raise ValidationError("New time must be in range [0, 24).")

    def _compose_planned_datetime(self):
        """Combine new_date + new_time (float hours) into a Datetime."""
        self.ensure_one()
        if not self.new_date:
            raise ValidationError("New date is required.")
        base_dt = fields.Datetime.to_datetime(self.new_date)  # midnight
        hours = int(self.new_time)
        minutes = int(round((self.new_time - hours) * 60))
        if minutes == 60:
            hours += 1
            minutes = 0
        if hours >= 24:
            raise ValidationError("New time must be < 24.0")
        return base_dt + timedelta(hours=hours, minutes=minutes)

    def action_reschedule(self):
        self.ensure_one()
        old_visit = self.visit_id

        # Cancel old visit to avoid hitting the "once per day" constraint
        old_visit.write({
            "state": "cancelled",
            "reschedule_reason": self.reason,
        })

        planned_dt = self._compose_planned_datetime()
        doctor_id = self.new_doctor_id.id or old_visit.doctor_id.id

        new_visit = self.env["hr.hospital.patient.visit"].create({
            "patient_id": old_visit.patient_id.id,
            "doctor_id": doctor_id,
            "planned_date": planned_dt,
            "visit_type": old_visit.visit_type,
            "reschedule_reason": self.reason,
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.hospital.patient.visit",
            "view_mode": "form",
            "res_id": new_visit.id,
            "target": "current",
        }
