from odoo import api, fields, models


class OSLAddReaderWizard(models.TransientModel):
    _name = 'osl.add.reader.wizard'
    _description = 'Add Reader to book'

    book_id = fields.Many2one(
        comodel_name='osl.library.book',
        string='Book',
        required=True,
        readonly=True,
    )

    reader_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Readers',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model == 'osl.library.book' and active_id:
            res['book_id'] = active_id

        return res

    def action_add_readers(self):
        self.ensure_one()

        # добавить выбранных читателей к книге (не стирая существующих)
        if self.reader_ids:
            self.book_id.reader_ids = [(4, p.id, 0) for p in self.reader_ids]

        return {'type': 'ir.actions.act_window_close'}
