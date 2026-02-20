# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrHospitalDoctorSpeciality(models.Model):
    _name = "hr.hospital.doctor.speciality"
    _description = "Doctor Speciality"
    _order = "name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(string="Code", required=True, size=10, index=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)

    doctor_ids = fields.One2many(
        comodel_name="hr.hospital.doctor",
        inverse_name="speciality_id",
        string="Doctors",
    )

    doctor_count = fields.Integer(
        compute="_compute_doctor_count",
        store=True,
    )

    _speciality_name_uniq = models.Constraint(
        "UNIQUE(name)",
        "Speciality name must be unique.",
    )
    _speciality_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Speciality code must be unique.",
    )

    @api.depends("doctor_ids")
    def _compute_doctor_count(self):
        for rec in self:
            rec.doctor_count = len(rec.doctor_ids)
