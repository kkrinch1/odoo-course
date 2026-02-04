{
    'name': 'OSL Library',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Simple library module with books + wizard',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/osl_add_reader_wizard_views.xml',
        'views/osl_library_book_views.xml'
    ],
    'demo': [
        'demo/res_partner_demo.xml',
        'demo/osl.library.book.csv',
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
