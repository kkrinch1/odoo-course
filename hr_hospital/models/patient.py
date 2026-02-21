# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrHospitalPatient(models.Model):
    _name = "hr.hospital.patient"
    _description = "Patient"
    _inherit = ["abstract.person"]

    personal_doctor_id = fields.Many2one(
        "hr.hospital.doctor",
        string="Primary Doctor",
        ondelete="set null",
    )

    passport_data = fields.Char(string="Passport Details", size=10)

    contact_person_id = fields.Many2one(
        "hr.hospital.contact.person",
        string="Contact Person",
        ondelete="set null",
    )

    blood_group = fields.Selection(
        selection=[
            ("o_pos", "O(I) Rh+"),
            ("o_neg", "O(I) Rh-"),
            ("a_pos", "A(II) Rh+"),
            ("a_neg", "A(II) Rh-"),
            ("b_pos", "B(III) Rh+"),
            ("b_neg", "B(III) Rh-"),
            ("ab_pos", "AB(IV) Rh+"),
            ("ab_neg", "AB(IV) Rh-"),
        ],
        string="Blood Type",
    )

    allergies = fields.Text(string="Allergies")

    insurance_company_id = fields.Many2one(
        "res.partner",
        string="Insurance Company",
        domain=[("is_company", "=", True)],
    )
    policy_number = fields.Char(string="Insurance Policy Number")

    doctor_history_ids = fields.One2many(
        "patient.doctor.history",
        "patient_id",
        string="Primary Doctor History",
    )



    # -------------------------
    # OVERRIDES
    # -------------------------
    @api.model_create_multi
    def create(self, vals_list):
        patients = super().create(vals_list)
        for patient, vals in zip(patients, vals_list):
            doctor_id = vals.get("personal_doctor_id")
            if doctor_id:
                patient._create_doctor_history(
                    new_doctor_id=doctor_id,
                    reason=self.env.context.get("doctor_change_reason"),
                    change_date=self.env.context.get("doctor_change_date"),
                )
        return patients

    def write(self, vals):
        # detect changes before write
        to_track = {}
        if "personal_doctor_id" in vals:
            for rec in self:
                to_track[rec.id] = rec.personal_doctor_id.id

        res = super().write(vals)

        if "personal_doctor_id" in vals:
            for rec in self:
                old_id = to_track.get(rec.id)
                new_id = rec.personal_doctor_id.id  # may be False
                if old_id != new_id and new_id:
                    rec._create_doctor_history(
                        new_doctor_id=new_id,
                        reason=self.env.context.get("doctor_change_reason"),
                        change_date=self.env.context.get("doctor_change_date"),
                    )
        return res

    # HELPERS
    def _create_doctor_history(self, new_doctor_id, reason=None, change_date=None):
        self.ensure_one()
        self.env["patient.doctor.history"].create({
            "patient_id": self.id,
            "doctor_id": new_doctor_id,
            "assign_date": change_date or fields.Date.context_today(self),
            "change_reason": reason or "",
        })

    def action_open_export_card_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Export Patient Card",
            "res_model": "hr.hospital.patient.card.export.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_patient_id": self.id,
            },
        }
