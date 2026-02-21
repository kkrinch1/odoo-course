# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MassReassignDoctorWizard(models.TransientModel):
    """Bulk reassignment of Primary Doctor for multiple patients."""

    _name = "mass.reassign.doctor.wizard"
    _description = "Bulk Doctor Reassignment"

    old_doctor_id = fields.Many2one(
        "hr.hospital.doctor",
        string="Old Doctor",
        domain=[("active", "=", True)],
    )
    new_doctor_id = fields.Many2one(
        "hr.hospital.doctor",
        string="New Doctor",
        required=True,
        domain=[("active", "=", True)],
    )

    # ✅ ТЗ: Date default=today (и делаем required чтобы не было пусто)
    change_date = fields.Date(
        string="Change Date",
        default=fields.Date.context_today,
        required=True,
    )

    # ✅ ТЗ: Text + required=True
    reason = fields.Text(string="Reason", required=True)

    patient_ids = fields.Many2many(
        "hr.hospital.patient",
        string="Patients",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        # Prefer explicit defaults (e.g., from a server action), fall back to list selection.
        default_patient_ids = self.env.context.get("default_patient_ids")
        if default_patient_ids and "patient_ids" in fields_list:
            # can be either a raw list of ids or an M2M command list
            if (
                isinstance(default_patient_ids, list)
                and default_patient_ids
                and isinstance(default_patient_ids[0], (list, tuple))
            ):
                res["patient_ids"] = default_patient_ids
            else:
                res["patient_ids"] = [(6, 0, list(default_patient_ids))]
            return res

        active_ids = self.env.context.get("active_ids") or []
        if active_ids and "patient_ids" in fields_list:
            res["patient_ids"] = [(6, 0, active_ids)]

        return res

    @api.onchange("old_doctor_id")
    def _onchange_old_doctor_id(self):
        """Удобство: если выбрали старого врача и пациентов еще не выбрали — подставим всех его пациентов."""
        if not self.old_doctor_id:
            return
        if self.patient_ids:
            return

        patients = self.env["hr.hospital.patient"].search(
            [("personal_doctor_id", "=", self.old_doctor_id.id)]
        )
        self.patient_ids = [(6, 0, patients.ids)]

    def action_apply(self):
        self.ensure_one()

        if self.old_doctor_id and self.old_doctor_id == self.new_doctor_id:
            raise ValidationError(_("Old doctor and new doctor cannot be the same."))

        patients = self.patient_ids
        if not patients:
            active_ids = self.env.context.get("active_ids") or []
            patients = self.env["hr.hospital.patient"].browse(active_ids)

        if not patients:
            raise UserError(_("Select at least one patient."))

        # Optional: only change for patients currently assigned to old_doctor_id.
        if self.old_doctor_id:
            patients = patients.filtered(lambda p: p.personal_doctor_id == self.old_doctor_id)

        if not patients:
            raise UserError(_("No patients match the selected Old Doctor."))

        # Patient model tracks history using these context keys.
        patients.with_context(
            doctor_change_reason=self.reason,
            doctor_change_date=self.change_date,
        ).write({
            "personal_doctor_id": self.new_doctor_id.id,
        })

        return {"type": "ir.actions.act_window_close"}
