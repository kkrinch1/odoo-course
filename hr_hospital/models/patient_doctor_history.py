# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalPatientDoctorHistory(models.Model):
    _name = "patient.doctor.history"
    _description = "Primary Doctor History"
    _order = "assign_date desc, id desc"

    patient_id = fields.Many2one(
        "hr.hospital.patient",
        string="Patient",
        required=True,
        ondelete="cascade",
        index=True,
    )
    doctor_id = fields.Many2one(
        "hr.hospital.doctor",
        string="Doctor",
        required=True,
        ondelete="restrict",
        index=True,
    )

    assign_date = fields.Date(
        string="Assign Date",
        required=True,
        default=fields.Date.context_today,
        index=True,
    )
    change_date = fields.Date(string="Change Date")
    change_reason = fields.Text(string="Change Reason")

    active = fields.Boolean(default=True, index=True)

    @api.constrains("assign_date", "change_date")
    def _check_dates(self):
        for rec in self:
            if rec.assign_date and rec.change_date and rec.change_date < rec.assign_date:
                raise ValidationError("Change date cannot be earlier than assign date.")

    # -------------------------
    # OVERRIDES (from task)
    # -------------------------
    @api.model_create_multi
    def create(self, vals_list):
        # For each new history line:
        # - deactivate previous active history line for that patient
        # - fill change_date on the previous line
        records = super().create(vals_list)

        for rec in records:
            # previous active record (excluding the newly created one)
            prev = self.search([
                ("patient_id", "=", rec.patient_id.id),
                ("active", "=", True),
                ("id", "!=", rec.id),
            ], order="assign_date desc, id desc", limit=1)

            if prev:
                prev.write({
                    "active": False,
                    "change_date": rec.assign_date,
                })

        return records
