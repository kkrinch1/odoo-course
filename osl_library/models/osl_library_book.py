from odoo import fields, models


class OSLLibraryBook(models.Model):
    _name = 'osl.library.book'
    _description = 'Library Book'
    _inherit = ['osl.note.mixin']

    name = fields.Char(string='Title', required=True)
    active = fields.Boolean(default=True)

    # главный автор (Many2one)
    res_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Author',
        ondelete='set null',
    )

    # читатели (Many2many) — для визарда
    reader_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Readers',
        relation='osl_book_reader_rel',
        column1='book_id',
        column2='partner_id',
    )
