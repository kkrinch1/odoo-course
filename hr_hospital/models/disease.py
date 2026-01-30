from odoo import fields, models


class HrHospitalDisease(models.Model):
    _name = "hr.hospital.disease"
    _description = "Disease Type"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code")
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("disease_name_uniq", "unique(name)", "Disease name must be unique."),
    ]
