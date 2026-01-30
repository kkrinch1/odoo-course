from odoo import fields, models


class HrHospitalPatient(models.Model):
    _name = "hr.hospital.patient"
    _description = "Patient"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    birth_date = fields.Date(string="Birth Date")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    active = fields.Boolean(default=True)

    doctor_id = fields.Many2one(
        comodel_name="hr.hospital.doctor",
        string="Observing Doctor",
        ondelete="set null",
    )

    disease_ids = fields.Many2many(
        comodel_name="hr.hospital.disease",
        relation="hr_hospital_patient_disease_rel",
        column1="patient_id",
        column2="disease_id",
        string="Diseases",
    )
