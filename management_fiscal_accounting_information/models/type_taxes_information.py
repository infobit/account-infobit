# -*- coding: utf-8 -*-

from odoo import api, fields, models


class type_taxes_information(models.Model):
    _name = 'type.taxes.information'
    
    name = fields.Selection(selection=[
        ('outputtax', 'Output TAX'),
        ('inputtax', 'Input TAX'),
        ('inputtax_not_deductible', 'Input TAX not deductible'),
        ('tax_withholdings', 'Tax withholdings'),
        ('equivalence_surcharge', 'Equivalence surcharge')],
        string='Type')
    exclude = fields.Selection(selection=[
        ('s', 'SI'), 
        ('n', 'NO')],
        string='Exclude', default='n')
    type_tax_use = fields.Selection(selection=[
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('none', 'None')],
        string='Type tax use')
    exclude_amount_untaxes = fields.Selection(selection=[('s', 'Si'), ('n', 'No')], string='Exclude amount untaxes', default='n')
    include_tax_diferent = fields.Selection(selection=[
        ('s', 'SI'), 
        ('n', 'NO')],
        string='Include in Tax diferent', default='n')
    tax_ids = fields.One2many('account.tax', 'type_taxes_information_id', 'Taxes')
