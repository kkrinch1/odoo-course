# -*- coding: utf-8 -*-
from odoo import fields, models


class HrHospitalContactPerson(models.Model):
    _name = "hr.hospital.contact.person"
    _description = "Contact Person"
    _inherit = ["abstract.person"]

    relation = fields.Selection(
        selection=[
            ("parent", "Parent"),
            ("spouse", "Spouse"),
            ("child", "Child"),
            ("other", "Other"),
        ],
        string="Relationship",
        default="other",
    )

    # optional link to patient to satisfy domain requirement in task
    patient_id = fields.Many2one(
        "hr.hospital.patient",
        string="Patient",
        domain=[("allergies", "!=", False)],
        help="Domain shows only patients with allergies filled in.",
    )
