# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalDoctor(models.Model):
    _name = "hr.hospital.doctor"
    _description = "Doctor"
    _inherit = ["abstract.person"]
    _order = "full_name"

    active = fields.Boolean(default=True)

    # system login
    user_id = fields.Many2one("res.users", string="System User")

    # speciality
    speciality_id = fields.Many2one(
        "hr.hospital.doctor.speciality",
        string="Specialty",
        ondelete="restrict",
        index=True,
    )

    # intern / mentor
    is_intern = fields.Boolean(string="Intern")
    mentor_id = fields.Many2one(
        "hr.hospital.doctor",
        string="Mentor Doctor",
        domain=[("is_intern", "=", False), ("active", "=", True)],
        help="Available only for interns.",
    )   

    license_number = fields.Char(string="License Number", required=True, copy=False)
    license_issue_date = fields.Date(string="License Issue Date")

    experience_years = fields.Integer(
        string="Work Experience (years)",
        compute="_compute_experience_years",
        store=True,
    )

    rating = fields.Float(string="Rating", digits=(3, 2), default=0.0)

    schedule_ids = fields.One2many(
        "hr.hospital.doctor.schedule",
        "doctor_id",
        string="Work Schedule",
    )

    study_country_id = fields.Many2one("res.country", string="Country of Study")

    # ------------------------------------------------------------
    # SQL CONSTRAINTS (Odoo 19+)
    # ------------------------------------------------------------
    _license_number_uniq = models.Constraint(
        "UNIQUE(license_number)",
        "License number must be unique.",
    )
    _rating_range_chk = models.Constraint(
        "CHECK(rating >= 0 AND rating <= 5)",
        "Rating must be between 0.00 and 5.00.",
    )

    # -------------------------
    # COMPUTES
    # -------------------------
    @api.depends("license_issue_date")
    def _compute_experience_years(self):
        today = fields.Date.context_today(self)
        for doctor in self:
            if doctor.license_issue_date:
                issue = doctor.license_issue_date
                years = today.year - issue.year - ((today.month, today.day) < (issue.month, issue.day))
                doctor.experience_years = max(years, 0)
            else:
                doctor.experience_years = 0

    # -------------------------
    # CONSTRAINTS
    # -------------------------
    @api.constrains("mentor_id", "is_intern")
    def _check_mentor_rules(self):
        for doc in self:
            if doc.mentor_id:
                if doc.mentor_id.id == doc.id:
                    raise ValidationError("A doctor cannot be their own mentor.")
                if doc.mentor_id.is_intern:
                    raise ValidationError("An intern cannot be selected as a mentor.")
            # mentor only for interns
            if not doc.is_intern and doc.mentor_id:
                raise ValidationError("The 'Mentor Doctor' field is available only for interns.")

    # -------------------------
    # ONCHANGE
    # -------------------------
    @api.onchange("is_intern")
    def _onchange_is_intern(self):
        for doc in self:
            if not doc.is_intern:
                doc.mentor_id = False
            else:
                if not doc.mentor_id:
                    mentor = self.env["hr.hospital.doctor"].search(
                        [("is_intern", "=", False), ("active", "=", True)], limit=1
                    )
                    doc.mentor_id = mentor

    # -------------------------
    # ARCHIVE RULE
    # -------------------------
    def write(self, vals):
        # prevent archiving doctors with active (not finished) visits
        if "active" in vals and vals["active"] is False:
            Visit = self.env["hr.hospital.patient.visit"]
            for doc in self:
                active_visits = Visit.search_count([
                    ("doctor_id", "=", doc.id),
                    ("state", "in", ["planned"]),
                ])
                if active_visits:
                    raise ValidationError("Cannot archive a doctor with active visits.")
        return super().write(vals)

    # -------------------------
    # DISPLAY NAME
    # -------------------------
    def name_get(self):
        res = []
        for doc in self:
            spec = doc.speciality_id.name if doc.speciality_id else ""
            name = doc.full_name or f"{doc.first_name or ''}".strip()
            if spec:
                name = f"{name} ({spec})"
            res.append((doc.id, name))
        return res
