# -*- coding: utf-8 -*-
{
    'name': 'Filter by payment order in bank statements and change to number of invoice in communication field in sepa',
    'version': '10.0.1.1.0',
    'category': 'Accounting & Finance',
    'summary': 'Filter by payment order in bank statements and change to number of invoice in communication field in sepa',
    'author': 'Infobit Informatica',
    'license': 'AGPL-3',
    'website': 'www.infobit.es',
    'depends': ['account_bank_statement_import_move_line', 'account_payment_order'],
    'data': [
        'wizard/payment_bank_statement_line_create.xml'],
    'installable': True,
}
