# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrHospitalDisease(models.Model):
    """Hierarchical disease classifier with ICD-10 normalization and validation."""

    _name = "hr.hospital.disease"
    _description = "Disease"
    _order = "name"
    _parent_store = True

    name = fields.Char(required=True)

    parent_id = fields.Many2one(
        "hr.hospital.disease",
        string="Parent Disease",
        ondelete="set null",
        index=True,
    )
    child_ids = fields.One2many(
        "hr.hospital.disease",
        "parent_id",
        string="Child Diseases",
    )
    parent_path = fields.Char(index=True)

    disease_type = fields.Selection(
        selection=[
            ("infectious", "Infectious"),
            ("chronic", "Chronic"),
            ("acute", "Acute"),
            ("genetic", "Genetic"),
            ("other", "Other"),
        ],
        string="Disease Type",
        default="other",
        required=True,
        index=True,
    )

    icd10_code = fields.Char(string="ICD-10 Code", size=10, index=True)

    danger_level = fields.Selection(
        selection=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        default="low",
        required=True,
    )

    contagious = fields.Boolean(string="Contagious")
    symptoms = fields.Text(string="Symptoms")

    region_country_ids = fields.Many2many(
        comodel_name="res.country",
        string="Regions (Countries)",
    )

    # ------------------------------------------------------------
    # SQL CONSTRAINTS (Odoo 19+)
    # ------------------------------------------------------------
    _icd10_code_uniq = models.Constraint(
        "UNIQUE(icd10_code)",
        "ICD-10 Code must be unique.",
    )

    # ------------------------------------------------------------
    # NORMALIZATION
    # ------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Normalize ICD-10 codes before creating disease records."""
        for vals in vals_list:
            if "icd10_code" in vals:
                vals["icd10_code"] = self._normalize_icd10(vals.get("icd10_code"))
        return super().create(vals_list)

    def write(self, vals):
        """Normalize ICD-10 codes before updating disease records."""
        if "icd10_code" in vals:
            vals["icd10_code"] = self._normalize_icd10(vals.get("icd10_code"))
        return super().write(vals)

    def _normalize_icd10(self, code):
        """Trim + UPPER + convert empty to False (NULL in DB)."""
        code = (code or "").strip().upper()
        return code or False

    # ------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------
    @api.constrains("icd10_code")
    def _check_icd10_code(self):
        """Validate the ICD-10 code format."""
        pattern = re.compile(r"^[A-Z0-9.\-]{1,10}$")
        for rec in self:
            if not rec.icd10_code:
                continue
            if not pattern.match(rec.icd10_code):
                raise ValidationError(
                    "ICD-10 Code format is invalid (use A-Z, 0-9, '.', '-')."
                )
