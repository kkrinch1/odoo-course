from odoo import fields, models


class HrHospitalVisit(models.Model):
    _name = "hr.hospital.visit"
    _description = "Patient Visit"
    _order = "visit_datetime desc"

    patient_id = fields.Many2one(
        comodel_name="hr.hospital.patient",
        string="Patient",
        required=True,
        ondelete="cascade",
    )
    doctor_id = fields.Many2one(
        comodel_name="hr.hospital.doctor",
        string="Doctor",
        required=True,
        ondelete="restrict",
    )
    disease_id = fields.Many2one(
        comodel_name="hr.hospital.disease",
        string="Disease",
        ondelete="set null",
    )
    visit_datetime = fields.Datetime(
        string="Visit Date/Time",
        default=fields.Datetime.now,
        required=True,
    )
    notes = fields.Text(string="Notes")
