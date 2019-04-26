# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'
    
    type_taxes_information_id = fields.Many2one('type.taxes.information', 'Type tax information')
    exclude = fields.Boolean('exclude')  #fields.Selection(selection=[('s', 'Si'), ('n', 'No')], string='Exclude', default='n')
    generate_sale_intra = fields.Selection(selection=[('s', 'Si'), ('n', 'No')], string='Generate Sale Intra.', default='n')
