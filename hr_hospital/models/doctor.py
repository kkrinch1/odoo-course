# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalDoctor(models.Model):
    """Doctor profile with speciality, mentoring, schedule, and report helpers."""

    _name = "hr.hospital.doctor"
    _description = "Doctor"
    _inherit = ["abstract.person"]
    _order = "full_name"

    active = fields.Boolean(default=True)

    user_id = fields.Many2one("res.users", string="System User")

    speciality_id = fields.Many2one(
        "hr.hospital.doctor.speciality",
        string="Specialty",
        ondelete="restrict",
        index=True,
    )

    is_intern = fields.Boolean(string="Intern")
    mentor_id = fields.Many2one(
        "hr.hospital.doctor",
        string="Mentor Doctor",
        domain=[("is_intern", "=", False), ("active", "=", True)],
        help="Available only for interns.",
    )
    intern_ids = fields.One2many(
        "hr.hospital.doctor",
        "mentor_id",
        string="Interns",
    )
    intern_names = fields.Char(
        string="Intern Names",
        compute="_compute_intern_names",
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
    visit_ids = fields.One2many(
        "hr.hospital.patient.visit",
        "doctor_id",
        string="Visits",
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
        """Compute the work experience from the license issue date."""
        today = fields.Date.context_today(self)
        for doctor in self:
            if doctor.license_issue_date:
                issue = doctor.license_issue_date
                years = today.year - issue.year - (
                    (today.month, today.day) < (issue.month, issue.day)
                )
                doctor.experience_years = max(years, 0)
            else:
                doctor.experience_years = 0

    @api.depends("intern_ids.full_name")
    def _compute_intern_names(self):
        """Expose intern names as a comma-separated helper for kanban/report usage."""
        for doctor in self:
            doctor.intern_names = ", ".join(doctor.intern_ids.mapped("full_name"))

    # -------------------------
    # CONSTRAINTS
    # -------------------------
    @api.constrains("mentor_id", "is_intern")
    def _check_mentor_rules(self):
        """Validate mentor and intern relationships."""
        for doc in self:
            if doc.mentor_id:
                if doc.mentor_id.id == doc.id:
                    raise ValidationError("A doctor cannot be their own mentor.")
                if doc.mentor_id.is_intern:
                    raise ValidationError("An intern cannot be selected as a mentor.")
            if not doc.is_intern and doc.mentor_id:
                raise ValidationError(
                    "The 'Mentor Doctor' field is available only for interns."
                )

    # -------------------------
    # ONCHANGE
    # -------------------------
    @api.onchange("is_intern")
    def _onchange_is_intern(self):
        """Clear or suggest a mentor when the intern flag changes."""
        for doc in self:
            if not doc.is_intern:
                doc.mentor_id = False
            elif not doc.mentor_id:
                mentor = self.env["hr.hospital.doctor"].search(
                    [("is_intern", "=", False), ("active", "=", True)],
                    limit=1,
                )
                doc.mentor_id = mentor

    # -------------------------
    # ARCHIVE RULE
    # -------------------------
    def write(self, vals):
        """Prevent archiving doctors that still have planned visits."""
        if vals.get("active") is False:
            Visit = self.env["hr.hospital.patient.visit"]
            for doc in self:
                active_visits = Visit.search_count(
                    [
                        ("doctor_id", "=", doc.id),
                        ("state", "in", ["planned"]),
                    ]
                )
                if active_visits:
                    raise ValidationError("Cannot archive a doctor with active visits.")
        return super().write(vals)

    # -------------------------
    # ACTIONS
    # -------------------------
    def action_create_visit(self):
        """Open a prefilled visit form for the current doctor."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "New Visit",
            "res_model": "hr.hospital.patient.visit",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_doctor_id": self.id,
                "default_speciality_id": self.speciality_id.id or False,
            },
        }

    def _get_report_base_filename(self):
        """Return a stable base filename for the doctor PDF report."""
        self.ensure_one()
        return f"doctor_report_{self.id}"

    def _get_report_visits(self):
        """Return doctor visits sorted in reverse chronological order."""
        self.ensure_one()
        return self.visit_ids.sorted(
            key=lambda visit: (visit.planned_date or fields.Datetime.now(), visit.id),
            reverse=True,
        )

    def _get_report_print_datetime(self):
        """Provide the current timestamp for report footer output."""
        self.ensure_one()
        return fields.Datetime.now()

    def _format_report_datetime(self, value):
        """Format a datetime value in the user's timezone for report output."""
        self.ensure_one()
        if not value:
            return ""
        dt_local = fields.Datetime.context_timestamp(self, value)
        return dt_local.strftime("%Y-%m-%d %H:%M")

    def _format_report_date(self, value):
        """Format a date value for report output."""
        self.ensure_one()
        if not value:
            return ""
        return fields.Date.to_string(value)

    def _get_visit_type_label(self, visit):
        """Resolve a visit type selection value to its display label."""
        self.ensure_one()
        return dict(visit._fields["visit_type"].selection).get(
            visit.visit_type, visit.visit_type
        )

    def _get_visit_state_label(self, visit):
        """Resolve a visit state selection value to its display label."""
        self.ensure_one()
        return dict(visit._fields["state"].selection).get(visit.state, visit.state)

    def _get_report_patient_rows(self):
        """Build unique patient rows with the latest status for the report table."""
        self.ensure_one()
        rows = []
        seen_patient_ids = set()
        state_labels = dict(
            self.env["hr.hospital.patient.visit"]._fields["state"].selection
        )
        sex_labels = dict(self.env["hr.hospital.patient"]._fields["sex"].selection)

        for visit in self._get_report_visits():
            patient = visit.patient_id
            if not patient or patient.id in seen_patient_ids:
                continue
            seen_patient_ids.add(patient.id)
            rows.append(
                {
                    "patient_name": patient.full_name or patient.display_name,
                    "sex_label": sex_labels.get(patient.sex, ""),
                    "birth_date": patient.birth_date,
                    "phone": patient.phone,
                    "state": visit.state,
                    "state_label": state_labels.get(visit.state, visit.state),
                }
            )
        return rows

    # -------------------------
    # DISPLAY NAME
    # -------------------------
    def name_get(self):
        """Include the speciality in the display name when it is available."""
        res = []
        for doc in self:
            spec = doc.speciality_id.name if doc.speciality_id else ""
            name = doc.full_name or f"{doc.first_name or ''}".strip()
            if spec:
                name = f"{name} ({spec})"
            res.append((doc.id, name))
        return res
