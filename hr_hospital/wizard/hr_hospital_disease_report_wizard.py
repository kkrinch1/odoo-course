# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DiseaseReportWizard(models.TransientModel):
    _name = "disease.report.wizard"
    _description = "Disease Report for a Period"

    doctor_ids = fields.Many2many("hr.hospital.doctor", string="Doctors")
    disease_ids = fields.Many2many("hr.hospital.disease", string="Diseases")
    country_ids = fields.Many2many("res.country", string="Countries (patient citizenship)")

    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)

    report_type = fields.Selection(
        [("detailed", "Detailed"), ("summary", "Summary")],
        string="Report Type",
        default="detailed",
        required=True,
    )

    group_by = fields.Selection(
        [
            ("doctor", "By Doctor"),
            ("disease", "By Disease"),
            ("month", "By Month"),
            ("country", "By Country"),
        ],
        string="Group By",
        default="disease",
        required=True,
    )

    only_approved = fields.Boolean(string="Only approved diagnoses", default=False)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for w in self:
            if w.date_from and w.date_to and w.date_from > w.date_to:
                raise ValidationError("Start date must be <= end date.")

    def _build_domain(self):
        self.ensure_one()
        domain = []
        # date range based on visit planned_date
        domain += [("visit_id.planned_date", ">=", fields.Datetime.to_datetime(self.date_from))]
        domain += [("visit_id.planned_date", "<", fields.Datetime.to_datetime(self.date_to) + timedelta(days=1))]

        if self.doctor_ids:
            domain += [("visit_id.doctor_id", "in", self.doctor_ids.ids)]
        if self.disease_ids:
            domain += [("disease_id", "in", self.disease_ids.ids)]
        if self.country_ids:
            domain += [("visit_id.patient_id.citizenship_country_id", "in", self.country_ids.ids)]
        if self.only_approved:
            domain += [("approved", "=", True)]

        return domain

    def get_diagnoses(self):
        self.ensure_one()
        return self.env["hr.hospital.medical.diagnosis"].search(self._build_domain())

    def action_open_results(self):
        self.ensure_one()
        diagnoses = self.get_diagnoses()
        return {
            "type": "ir.actions.act_window",
            "name": "Diagnoses report",
            "res_model": "hr.hospital.medical.diagnosis",
            "view_mode": "list,form",
            "domain": [("id", "in", diagnoses.ids)],
            "context": {"search_default_group_by_%s" % self.group_by: 1} if self.report_type == "summary" else {},
        }
