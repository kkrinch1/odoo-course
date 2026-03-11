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

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        today = fields.Date.context_today(self)
        first_day = today.replace(day=1)

        if "date_from" in fields_list and not res.get("date_from"):
            res["date_from"] = first_day
        if "date_to" in fields_list and not res.get("date_to"):
            res["date_to"] = today

        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids", [])

        if active_model == "hr.hospital.doctor" and active_ids and "doctor_ids" in fields_list:
            res["doctor_ids"] = [(6, 0, active_ids)]

        return res

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for w in self:
            if w.date_from and w.date_to and w.date_from > w.date_to:
                raise ValidationError("Start date must be <= end date.")

    def _build_domain(self):
        self.ensure_one()
        domain = []

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

        ctx = {}
        if self.report_type == "summary":
            group_map = {
                "doctor": "doctor_id",
                "disease": "disease_id",
                "month": "visit_planned_date:month",
                "country": "patient_country_id",
            }
            group_by_value = group_map.get(self.group_by)
            if group_by_value:
                ctx["group_by"] = group_by_value

        return {
            "type": "ir.actions.act_window",
            "name": "Diagnoses report",
            "res_model": "hr.hospital.medical.diagnosis",
            "view_mode": "list,form",
            "domain": [("id", "in", diagnoses.ids)],
            "context": ctx,
        }