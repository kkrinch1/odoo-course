from odoo import fields, models


class HrHospitalDoctor(models.Model):
    _name = "hr.hospital.doctor"
    _description = "Doctor"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    specialty = fields.Char(string="Specialty")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    active = fields.Boolean(default=True)

    supervising_doctor_id = fields.Many2one(
        comodel_name="hr.hospital.doctor",
        string="Supervising Doctor",
        ondelete="set null",
    )
