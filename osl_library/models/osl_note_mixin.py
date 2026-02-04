from odoo import fields, models


class OSLNoteMixin(models.AbstractModel):
    _name = 'osl.note.mixin'
    _description = 'OSL Note Mixin'

    note = fields.Text(string='Note')
