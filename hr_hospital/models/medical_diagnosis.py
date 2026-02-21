# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrHospitalMedicalDiagnosis(models.Model):
    _name = "hr.hospital.medical.diagnosis"
    _description = "Diagnosis"
    _order = "id desc"

    visit_id = fields.Many2one(
        "hr.hospital.patient.visit",
        string="Visit",
        required=True,
        ondelete="cascade",
        # Only completed visits from the last 30 days.
        # Use a *callable* domain so the window stays dynamic.
        domain=lambda self: [
            ("state", "=", "done"),
            ("planned_date", ">=", fields.Datetime.now() - relativedelta(days=30)),
        ],
    )

    disease_id = fields.Many2one(
        "hr.hospital.disease",
        string="Disease",
        required=True,
        # safer / standard: list for 'in'
        domain="[('contagious','=',True), ('danger_level','in',['high','critical'])]",
    )

    description = fields.Text(string="Diagnosis Description")
    treatment = fields.Html(string="Prescribed Treatment")

    severity = fields.Selection(
        [
            ("light", "Mild"),
            ("medium", "Moderate"),
            ("hard", "Severe"),
            ("critical", "Critical"),
        ],
        string="Severity",
        default="medium",
        required=True,
    )

    approved = fields.Boolean(string="Approved", default=False)
    approved_by_doctor_id = fields.Many2one(
        "hr.hospital.doctor",
        string="Approving Doctor",
        readonly=True,
        copy=False,
    )
    approved_date = fields.Datetime(
        string="Approval Date",
        readonly=True,
        copy=False,
    )

    # ==========================================================
    # RELATED (store=True) fields for GROUP BY in search view
    # ==========================================================
    doctor_id = fields.Many2one(
        "hr.hospital.doctor",
        string="Doctor",
        related="visit_id.doctor_id",
        store=True,
        readonly=True,
    )

    patient_country_id = fields.Many2one(
        "res.country",
        string="Patient Country",
        related="visit_id.patient_id.citizenship_country_id",
        store=True,
        readonly=True,
    )

    visit_planned_date = fields.Datetime(
        string="Visit Planned Date",
        related="visit_id.planned_date",
        store=True,
        readonly=True,
    )

    # -------------------------
    # CONSTRAINTS
    # -------------------------
    @api.constrains("visit_id")
    def _check_visit_is_recent_and_done(self):
        # during module install/demo load we don't want hard blocks
        if self.env.context.get("install_mode"):
            return

        now = fields.Datetime.now()
        min_dt = now - relativedelta(days=30)

        for rec in self:
            if not rec.visit_id:
                continue

            if rec.visit_id.state != "done":
                raise ValidationError("A diagnosis can be created only for completed visits.")

            if rec.visit_id.planned_date and rec.visit_id.planned_date < min_dt:
                raise ValidationError("A diagnosis can be created only for visits from the last 30 days.")

    # -------------------------
    # HELPERS
    # -------------------------
    def _current_doctor(self):
        return self.env["hr.hospital.doctor"].search(
            [("user_id", "=", self.env.user.id)],
            limit=1,
        )

    # -------------------------
    # ACTIONS
    # -------------------------
    def action_approve(self):
        """
        Approve diagnosis:
        - If visit doctor is an intern: only mentor can approve.
        - If visit doctor is NOT an intern: only the visit doctor can approve.
        """
        now = fields.Datetime.now()
        cur_doc = self._current_doctor()

        if not cur_doc:
            raise UserError("Only a doctor (linked to a system user) can approve diagnoses.")

        for rec in self:
            if rec.approved:
                continue  # already approved, don't rewrite timestamps

            if not rec.visit_id or not rec.visit_id.doctor_id:
                raise UserError("Diagnosis must be linked to a visit with a doctor.")

            visit_doc = rec.visit_id.doctor_id

            if visit_doc.is_intern:
                if not visit_doc.mentor_id:
                    raise UserError("This intern has no mentor assigned; approval is impossible.")
                if visit_doc.mentor_id != cur_doc:
                    raise UserError("Only the intern's mentor can approve the intern's diagnosis.")
            else:
                if visit_doc != cur_doc:
                    raise UserError("Only the visit doctor can approve this diagnosis.")

            rec.write({
                "approved": True,
                "approved_by_doctor_id": cur_doc.id,
                "approved_date": now,
            })

    def action_unapprove(self):
        cur_doc = self._current_doctor()
        if not cur_doc:
            raise UserError("Only a doctor (linked to a system user) can unapprove diagnoses.")

        for rec in self:
            if not rec.approved:
                continue

            rec.write({
                "approved": False,
                "approved_by_doctor_id": False,
                "approved_date": False,
            })
