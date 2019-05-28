# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import Warning as UserError
import re
from calendar import monthrange
from odoo.tools import config
from datetime import datetime

class ManagementFiscalAccountingInformation(models.Model):
    _name = 'management.fiscal.accounting.information'
    _period_yearly = True
    _period_quarterly = True
    _period_monthly = True

    def _default_company_id(self):
        company_obj = self.env['res.company']
        return company_obj._company_default_get('l10n.es.aeat.report')

    def _default_journal(self):
        return self.env['account.journal'].search(
            [('type', '=', 'general')])[:1]

    def get_period_type_selection(self):
        period_types = []
        if self._period_yearly or config['test_enable']:
            period_types += [('0A', '0A - Anual')]
        if self._period_quarterly:
            period_types += [('1T', '1T - Primer trimestre'),
                             ('2T', '2T - Segundo trimestre'),
                             ('3T', '3T - Tercer trimestre'),
                             ('4T', '4T - Cuarto trimestre')]
        if self._period_monthly or config['test_enable']:
            period_types += [('01', '01 - Enero'),
                             ('02', '02 - Febrero'),
                             ('03', '03 - Marzo'),
                             ('04', '04 - Abril'),
                             ('05', '05 - Mayo'),
                             ('06', '06 - Junio'),
                             ('07', '07 - Julio'),
                             ('08', '08 - Agosto'),
                             ('09', '09 - Septiembre'),
                             ('10', '10 - Octubre'),
                             ('11', '11 - Noviembre'),
                             ('12', '12 - Diciembre')]
        return period_types

    def _default_period_type(self):
        selection = self.get_period_type_selection()
        return selection and selection[0][0] or False

    def _default_year(self):
        return fields.Date.from_string(fields.Date.today()).year


    company_id = fields.Many2one(
        comodel_name='res.company', string="Company", required=True,
        readonly=True, default=_default_company_id,
        states={'draft': [('readonly', False)]})
    year = fields.Integer(string="Year", default=_default_year, required=True, readonly=True, states={'draft': [('readonly', False)]})
    calculation_date = fields.Datetime(string="Calculation date", readonly=True, states={'draft': [('readonly', False)]})
    name = fields.Char(string="Identificador")
    period_type = fields.Selection(
        selection='get_period_type_selection', string="Period type",
        required=True, default=_default_period_type,
        readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date(
        string="Starting date", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    date_end = fields.Date(
        string="Ending date", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    journal_ids = fields.Many2many('account.journal', 'journal_rel_information', 'journal_rel_id', 'journal_id', string="Journals", readonly=True,
        states={'draft': [('readonly', False)]})
    account_group_ids = fields.Many2many('account.group', 'group_rel_account', 'group_id', 'account_id', string="Account Groups", readonly=True,
        states={'draft': [('readonly', False)]})
    tax_ids = fields.Many2many('account.tax', 'tax_rel_information', 'tax_rel_id', 'tax_id', string="Taxes", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    partner_ids = fields.Many2many('res.partner', 'partner_rel_information', 'partner_rel_id', 'partner_id', string="Partners", readonly=True,
        states={'draft': [('readonly', False)]})
    estructure_tax_line_ids = fields.One2many('estructure.tax.line', 'management_id', 'Lines of Taxes')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('calculated', 'Processed'),
            ('done', 'Done'),
            ('posted', 'Posted'),
            ('cancelled', 'Cancelled'),
        ], string='State', default='draft', readonly=True)
    type = fields.Selection(
        selection=[
            ('s', 'summary'),
            ('d', 'detail'),
            ('b', 'summarybook'),
            ('b4', 'balance4'),
            ('bd', 'detailbook'),
        ], string='Type',  readonly=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name, calculation_date, company_id)',
         'Identification and calculation date must be unique'),
    ]

    @api.onchange('year', 'period_type')
    def onchange_period_type(self):
        if not self.year or not self.period_type:
            self.date_start = False
            self.date_end = False
        else:
            if self.period_type == '0A':
                # Anual
                self.date_start = fields.Date.from_string(
                    '%s-01-01' % self.year)
                self.date_end = fields.Date.from_string(
                    '%s-12-31' % self.year)
            elif self.period_type in ('1T', '2T', '3T', '4T'):
                # Trimestral
                starting_month = 1 + (int(self.period_type[0]) - 1) * 3
                ending_month = starting_month + 2
                self.date_start = fields.Date.from_string(
                    '%s-%s-01' % (self.year, starting_month))
                self.date_end = fields.Date.from_string(
                    '%s-%s-%s' % (
                        self.year, ending_month,
                        monthrange(self.year, ending_month)[1]))
            elif self.period_type in ('01', '02', '03', '04', '05', '06',
                                      '07', '08', '09', '10', '11', '12'):
                # Mensual
                month = int(self.period_type)
                self.date_start = fields.Date.from_string(
                    '%s-%s-01' % (self.year, month))
                self.date_end = fields.Date.from_string('%s-%s-%s' % (
                    self.year, month, monthrange(self.year, month)[1]))
            #self.export_config_id = self._get_export_config(self.date_start).id

    #resumen de IVA
    @api.multi
    def calculate_taxes_iva_summary(self):
      if self.state == 'draft':
        if self.tax_ids:
         for rec in self:
          tax_model = self.env['account.tax']
          taxes = [x.id for x in self.tax_ids]
          journals = [x.id for x in self.journal_ids]
          partners = [x.id for x in self.partner_ids]
          #GRABAR LINEA CON PERIODO Y FILTROS APLICADOS
          if not partners:
             filtros = {
                   'management_id': self.id,
                   'ref': 'Resumen de iva desde ' + str(self.date_start)[8:10] + '-' + str(self.date_start)[5:7] + '-' + str(self.date_start)[0:4] + ' hasta ' + str(self.date_end)[8:10] + '-' + str(self.date_end)[5:7] + '-' + str(self.date_end)[0:4],
             }
          else:
             filtros = {
                   'management_id': self.id,
                   'ref': 'Resumen de iva de ' + str(self.partner_ids[0].name) + ' desde ' + str(self.date_start)[8:10] + '-' + str(self.date_start)[5:7] + '-' + str(self.date_start)[0:4] + ' hasta ' + str(self.date_end)[8:10] + '-' + str(self.date_end)[5:7] + '-' + str(self.date_end)[0:4],
             }
          self.env['estructure.tax.line'].create(filtros)
          #BUSCAR APLICACIONES IMPUESTOS
          self._cr.execute("SELECT t.type_tax_use as type, sum(it.base) as base, sum(it.amount) as cuota FROM account_tax t inner join account_invoice_tax it on t.id = it.tax_id inner join account_invoice i on it.invoice_id = i.id and " +
"(i.date_invoice between %s and %s) inner join type_taxes_information tti on t.type_taxes_information_id = tti.id and tti.exclude = 'n'  where t.id in %s group by t.type_tax_use", (self.date_start, self.date_end, tuple(taxes),))
          types = self._cr.dictfetchall()
          for type in types:
           #BUSCAR ACCOUNT.TAX.GROUPS DE LOS IMPUESTOS.
           self._cr.execute("SELECT tax.type_taxes_information_id as group, sum(it.base) as base, sum(it.amount) as cuota FROM account_invoice_tax it inner join account_invoice i on it.invoice_id = i.id inner join account_tax tax " +
"on it.tax_id = tax.id inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id and tti.exclude = 'n' where i.state in ('open','paid') and it.tax_id in %s and (i.date_invoice between %s and %s) and tti.type_tax_use = %s and " +
"tti.exclude = 'n'" +
"group by tax.type_taxes_information_id", (tuple(taxes), self.date_start, self.date_end, type['type'], ))
           groups = self._cr.dictfetchall()
           sumbase = 0.0
           sumcuota = 0.0
           for group in groups:
            if journals:
              if partners:
               self._cr.execute("SELECT it.tax_id as impuesto, min(tax.name) as nombre, i.type as type, tti.id as group, sum(it.base) as base, sum(it.amount) as cuota, tti.exclude_amount_untaxes as exclude_base FROM account_invoice_tax " +
"it inner join account_invoice i on it.invoice_id = i.id inner join account_tax tax on it.tax_id = tax.id and tax.type_taxes_information_id = %s inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id where " +
"i.state in ('open','paid') and it.tax_id in %s and (i.date_invoice between %s and %s) and i.partner_id in %s and i.journal_id in %s" +
"group by it.tax_id, tti.exclude_amount_untaxes, i.type order by it.tax_id, i.type", (group['group'], tuple(taxes), self.date_start, self.date_end, tuple(partners), tuple(journals), ))
              else:
               self._cr.execute("SELECT it.tax_id as impuesto, min(tax.name) as nombre, i.type as type, tt.id as group, sum(it.base) as base, sum(it.amount) as cuota, tti.exclude_amount_untaxes as exclude_base FROM account_invoice_tax " +
"it inner join account_invoice i on it.invoice_id = i.id inner join account_tax tax on it.tax_id = tax.id and tax.type_taxes_information_id = %s inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id where " +
"i.state in ('open','paid') and it.tax_id in %s and (i.date_invoice between %s and %s) and i.journal_id in %s" +
"group by it.tax_id, tti.exclude_amount_untaxes, tti.id, i.type order by it.tax_id, i.type", (group['group'], tuple(taxes), self.date_start, self.date_end, tuple(journals), ))
            else:
              if partners:
               self._cr.execute("SELECT it.tax_id as impuesto, min(tax.name) as nombre, i.type as type, tti.id as group, sum(it.base) as base, sum(it.amount) as cuota, tti.exclude_amount_untaxes as exclude_base FROM account_invoice_tax " +
"it inner join account_invoice i on it.invoice_id = i.id inner join account_tax tax on it.tax_id = tax.id and tax.type_taxes_information_id = %s inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id where " +
"i.state in ('open','paid') and it.tax_id in %s and (i.date_invoice between %s and %s) and i.partner_id in %s" +
"group by it.tax_id, tti.exclude_amount_untaxes, tti.id, i.type order by it.tax_id, i.type", (group['group'], tuple(taxes), self.date_start, self.date_end, tuple(partners), ))

              else:
               self._cr.execute("SELECT it.tax_id as impuesto, min(tax.name) as nombre, i.type as type, tti.id as group, sum(it.base) as base, sum(it.amount) as cuota, tti.exclude_amount_untaxes as exclude_base FROM account_invoice_tax " +
"it inner join account_invoice i on it.invoice_id = i.id inner join account_tax tax on it.tax_id = tax.id and tax.type_taxes_information_id = %s inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id where " +
"i.state in ('open','paid') and it.tax_id in %s and (i.date_invoice between %s and %s)" +
"group by it.tax_id, tti.exclude_amount_untaxes, i.type, tti.id order by it.tax_id, i.type", (group['group'], tuple(taxes), self.date_start, self.date_end,))
            data3 = self._cr.dictfetchall()
            regr = False
            for rimpfac in data3:
                 amounttotal = 0.0
                 if rimpfac['exclude_base'] == 'n':
                    amounttotal = rimpfac['base']
                 if rimpfac['type'] == 'out_invoice' or rimpfac['type'] == 'in_invoice':
                  #crear registro factura
                  rimpfact = {
                   'management_id': self.id,
                   'ref': rimpfac['nombre'],
                   'tax_id': rimpfac['impuesto'], 
                   'amount_untaxed': amounttotal,
                   'amount_tax': rimpfac['cuota'],
                   'amount_total_untaxed': amounttotal or 0.0,
                   'amount_total_tax': rimpfac['cuota'] or 0.0,
                   'group_id': rimpfac['group'],
                  }
                  if amounttotal < 0:
                     sumbase = sumbase - amounttotal
                  else:
                     sumbase = sumbase + amounttotal
                  if rimpfac['cuota'] < 0:
                     sumcuota = sumcuota - rimpfac['cuota'] or 0.0
                  else:
                     sumcuota = sumcuota + rimpfac['cuota'] or 0.0
                  regr = self.env['estructure.tax.line'].create(rimpfact)
                 else:
                  if regr and rimpfac['type'] != 'proforma':
                   #modificar registro factura
                   mimpfact = {
                   'amount_refund_untaxed': amounttotal,
                   'amount_refund_tax': rimpfac['cuota'],
                   'amount_total_untaxed': regr.amount_untaxed -  amounttotal or 0.0,
                   'amount_total_tax': regr.amount_tax - rimpfac['cuota'] or 0.0,
                  }
                  if amounttotal < 0:
                     sumbase = sumbase + amounttotal
                  else:
                     sumbase = sumbase - amounttotal
                  #sumbase = sumbase - amounttotal
                  if rimpfac['cuota'] < 0:
                     sumcuota = sumcuota + rimpfac['cuota']
                  else:
                     sumcuota = sumcuota - rimpfac['cuota'] or 0.0
                  #sumcuota = sumcuota - rimpfac['cuota'] or 0.0
                  regr.write(mimpfact)
            #buscar nombre del tipo de grupo informativo
            tipos = {'outputtax': 'Repercutido', 'inputtax':'Soportado', 'inputtax_not_deductible':'Soportado no deducible', 'tax_witholdings':'Retenciones fiscales', 'equivalence_surcharge':'Recargo Equivalencia'}
            namegroup = self.env['type.taxes.information'].browse(group['group']).name #with_context({'lang':'es_ES'})
            rgroup = {
                   'management_id': self.id,
                   'ref': tipos.get(namegroup),
                   'amount_total_untaxed': sumbase or 0.0,
                   'amount_total_tax': sumcuota or 0.0,
                   'group_id': group['group'],
            }
            reggroup = self.env['estructure.tax.line'].create(rgroup)
            sumbase = 0
            sumcuota = 0
         self._cr.execute("SELECT t.type_tax_use as type, sum(e.amount_total_untaxed) as amount_untaxed, sum(e.amount_total_tax) as tax FROM estructure_tax_line e inner join type_taxes_information t " +
"on e.group_id = t.id and t.include_tax_diferent = 's' where e.tax_id is null and e.amount_total_untaxed is not null and e.amount_total_tax is not null and e.management_id = %s group by t.type_tax_use order by t.type_tax_use desc", (self.id, ))
         diferentsgroups = self._cr.dictfetchall()
         diferentsb = 0.0
         diferentsc = 0.0
         for dgroup in diferentsgroups:
             tpe = 'Ninguno'
             if dgroup['type'] == 'sale':
                tpe = 'Repercutido'
             if dgroup['type'] == 'purchase':
                tpe = 'Soportado'
             rimpfactx = {
               'management_id': self.id,
               'ref': 'TOTAL ' + tpe,
               'amount_total_untaxed':  dgroup['amount_untaxed'] or 0.0,
               'amount_total_tax': dgroup['tax'] or 0.0,
             }
             regr = self.env['estructure.tax.line'].create(rimpfactx)

             if diferentsb == 0.0:
                diferentsb = dgroup['amount_untaxed']
             else:
                diferentsb = diferentsb - dgroup['amount_untaxed']
             if diferentsc == 0.0:
                diferentsc = dgroup['tax']
             else:
                diferentsc = diferentsc - dgroup['tax']
         rimpfact = {
               'management_id': self.id,
               'ref': 'Diferencia',
               'amount_total_untaxed': diferentsb or 0.0,
               'amount_total_tax': diferentsc or 0.0,
         }
         regr = self.env['estructure.tax.line'].create(rimpfact)
         self.write({'name': 'Resumen iva', 'type': 's'})
        else:
         raise UserError(_('Rellene los impuestos a consultar'))

    #detalle de iva
    def calculate_details_taxes_iva(self):
        for rec in self:
            tax_model = self.env['account.tax']
            taxes = [x.id for x in self.tax_ids]
            journals = [x.id for x in self.journal_ids]
            partners = [x.id for x in self.partner_ids]
            #GRABAR LINEA CON PERIODO Y FILTROS APLICADOS
            if not partners:
               filtros = {
                   'management_id': self.id,
                   'ref': "Libro registro de iva desde " +  str(self.date_start)[8:10] + '-' + str(self.date_start)[5:7] + '-' + str(self.date_start)[0:4] + ' hasta ' + str(self.date_end)[8:10] + '-' + str(self.date_end)[5:7] + '-' + str(self.date_end)[0:4],
               }
            else:
               filtros = {
                   'management_id': self.id,
                   'ref': 'Libro registro de iva de '  + str(self.partner_ids[0].name) + ' desde ' +  str(self.date_start)[8:10] + '-' + str(self.date_start)[5:7] + '-' + str(self.date_start)[0:4] + ' hasta ' + str(self.date_end)[8:10] + '-' + str(self.date_end)[5:7] + '-' + str(self.date_end)[0:4],
               }

            self.env['estructure.tax.line'].create(filtros)
            if taxes and journals:
              if partners:
                self._cr.execute("SELECT i.id, i.number as numero, i.type as tipo, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id as partner, " +
"i.amount_untaxed as base, rp.name as empresa, rp.vat as cif, i.amount_total as total FROM account_invoice_line_tax lt left outer join account_invoice_line l " + 
"on lt.invoice_line_id = l.id left outer join account_invoice i on l.invoice_id = i.id inner join account_invoice_tax it on i.id = it.invoice_id inner join " +
"res_partner rp on i.partner_id = rp.id inner join account_tax tax on lt.tax_id = tax.id where i.state in ('open','paid') and tax.id in %s and (i.date_invoice between %s " + 
"and %s) and i.journal_id in %s and i.partner_id in %s group by i.id, i.number, " +
"i.type, i.date_invoice, i.partner_id, rp.name, rp.vat, i.amount_untaxed, i.amount_total order by i.type, i.number", (tuple(taxes), self.date_start, self.date_end, tuple(journals), tuple(partners), ))  
              else:
                self._cr.execute("SELECT i.id, i.number as numero, i.type as tipo, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id as partner, " +
"i.amount_untaxed as base, rp.name as empresa, rp.vat as cif, i.amount_total as total FROM account_invoice_line_tax lt left outer join account_invoice_line l " + 
"on lt.invoice_line_id = l.id left outer join account_invoice i on l.invoice_id = i.id inner join account_invoice_tax it on i.id = it.invoice_id inner join " +
"res_partner rp on i.partner_id = rp.id inner join account_tax tax on lt.tax_id = tax.id where i.state in ('open', 'paid') and tax.id in %s and (i.date_invoice between %s " + 
"and %s) and i.journal_id in %s group by i.id, i.number, " +
"i.type, i.date_invoice, i.partner_id, rp.name, rp.vat, i.amount_untaxed, i.amount_total order by i.type, i.number", (tuple(taxes), self.date_start, self.date_end, tuple(journals), ))  
            else:
               if taxes and not journals:
                 if partners:
                  self._cr.execute("SELECT i.id, i.number as numero, i.type as tipo, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id as partner, " +
"i.amount_untaxed as base, rp.name as empresa, rp.vat as cif, i.amount_total as total FROM account_invoice_line_tax lt left outer join account_invoice_line l on " +
"lt.invoice_line_id = l.id left outer join account_invoice i on l.invoice_id = i.id inner join account_invoice_tax it on i.id = it.invoice_id inner join res_partner " + 
"rp on i.partner_id = rp.id inner join account_tax tax on lt.tax_id = tax.id where i.state in ('open', 'paid') and tax.id in %s and (i.date_invoice between %s and %s) and i.partner_id in %s " + 
"group by i.id, i.number, i.type, i.partner_id, i.date_invoice, rp.name, rp.vat, " + 
"i.amount_untaxed, i.amount_total order by i.type, i.number", (tuple(taxes), self.date_start, self.date_end, tuple(partners),))  
                 else:
                  self._cr.execute("SELECT i.id, i.number as numero, i.type as tipo, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id as partner, " +
"i.amount_untaxed as base, rp.name as empresa, rp.vat as cif, i.amount_total as total FROM account_invoice_line_tax lt left outer join account_invoice_line l on " +
"lt.invoice_line_id = l.id left outer join account_invoice i on l.invoice_id = i.id inner join account_invoice_tax it on i.id = it.invoice_id inner join res_partner " + 
"rp on i.partner_id = rp.id inner join account_tax tax on lt.tax_id = tax.id where i.state in ('open','paid') and tax.id in %s and (i.date_invoice between %s and %s) " + 
"group by i.id, i.number, i.type, i.partner_id, i.date_invoice, rp.name, rp.vat, " + 
"i.amount_untaxed, i.amount_total order by i.type, i.number", (tuple(taxes), self.date_start, self.date_end,))  
               else:
                 raise UserError(_('Rellene los impuestos a consultar'))
            data = self._cr.dictfetchall()
            for ele in data:
                #crear registro factura
                if ele['tipo'] == 'out_refund' or ele['tipo'] == 'in_refund':
                 if ele['tipo'] == 'out_refund':
                    tipoo = 'Abono venta'
                 if ele['tipo'] == 'in_refund':
                    tipoo = 'Abono compra'
                 factura = {
                   'management_id': self.id,
                   'ref': ele['numero'],
                   'type': tipoo, #ele['tipo'],
                   'invoice_date': ele['fecha'],
                   'partner_id': ele['partner'],
                   'vat_number': ele['cif'],
                   'invoice_id': ele['id'],
                   'amount_refund_untaxed': -ele['base'],
                   #'amount_tax': ele[''],
                   'amount_total': -ele['total'],
                 }
                else:
                 if ele['tipo'] == 'out_invoice':
                    tip = 'Venta'
                 else:
                    tip = 'Compra'
                 factura = {
                   'management_id': self.id,
                   'ref': ele['numero'],
                   'type': tip, #ele['tipo'],
                   #'comment': ele[''],
                   #'line_type': ,
                   'invoice_date': ele['fecha'],
                   'partner_id': ele['partner'],
                   'vat_number': ele['cif'],
                   'invoice_id': ele['id'],
                   #'move_id': ,
                   #'tax_id': ,
                   'amount_untaxed': ele['base'],
                   #'amount_tax': ele[''],
                   'amount_total': ele['total'],
                 }
                #raise Warning(factura)
                reg = self.env['estructure.tax.line'].create(factura)
                if reg:
                 #buscar las lineas de impuestos de esa factura
                 idfactura = ele['id']
                 if reg.type == 'Venta' or reg.type == 'Abono venta':
                  self._cr.execute("SELECT ti.tax_id as impuesto, t.name as nombreimpuesto, ti.base as base, ti.amount as cuota, ty.type_tax_use as type_tax_use from account_invoice_tax ti "+
"inner join account_tax t on ti.tax_id = t.id inner join type_taxes_information ty on t.type_taxes_information_id = ty.id and ty.type_tax_use = 'sale' where invoice_id =  %s", (idfactura,))
                 if reg.type == 'Compra' or reg.type == 'Abono compra':
                  self._cr.execute("SELECT ti.tax_id as impuesto, t.name as nombreimpuesto, ti.base as base, ti.amount as cuota, ty.type_tax_use as type_tax_use from account_invoice_tax ti " +
"inner join account_tax t on ti.tax_id = t.id inner join type_taxes_information ty on t.type_taxes_information_id = ty.id and ty.type_tax_use = 'purchase' where invoice_id =  %s", (idfactura,))
                 data2 = self._cr.dictfetchall()
                 #raise Warning(data2)
                 i = 0
                 for impfac in data2:
                   if ele['tipo'] == 'out_refund' or ele['tipo'] == 'in_refund':
                    impfact = {
                     'management_id': self.id,
                     'invoice_id': idfactura,
                     'tax_id': impfac['impuesto'], 
                     'amount_untaxed': -impfac['base'],
                     'amount_tax': -impfac['cuota'],
                    }
                   else:
                    #crear registro factura
                    cta = impfac['cuota']
                    if impfac['cuota'] and impfac['cuota'] < 0:
                       cta = -impfac['cuota']
                    impfact = {
                     'management_id': self.id,
                     'invoice_id': idfactura,
                     'tax_id': impfac['impuesto'], 
                     'amount_untaxed': impfac['base'],
                     'amount_tax': cta,
                    }
                   if i == 0:
                      reg.write(impfact)
                   else:
                      regd = self.env['estructure.tax.line'].create(impfact)
                   i+=1
            #BUSCAR FACTURAS DE COMPRA QUE TENGAN IVAS EN SU TIPO DE INFORMACION DE TIPO VENTA -INTRA
            if taxes and journals:
              if partners:
                 self._cr.execute("SELECT i.id as id, i.number as numero, ti.tax_id as impuesto, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id " +
"as partner, i.amount_untaxed as baseinvoice, rp.name as empresa, rp.vat as cif, i.amount_total as total, t.name as nombreimpuesto, ti.base as base, ti.amount as " +
"cuota, ty.type_tax_use as type_tax_use, i.type as tipo from account_invoice_tax ti inner join account_tax t on ti.tax_id = t.id and t.id in %s and " +
"t.generate_sale_intra = 's' inner join type_taxes_information ty on t.type_taxes_information_id = ty.id and ty.type_tax_use = 'sale' inner join account_invoice " +
"i on ti.invoice_id = i.id and i.type in ('in_refund', 'in_invoice') and i.partner_id in %s and i.journal_id in %s and (i.date_invoice between %s and %s) inner " +
"join res_partner rp on i.partner_id = rp.id order by i.number", (tuple(taxes), tuple(partners), tuple(journals), self.date_start, self.date_end))
              else:
                 self._cr.execute("SELECT i.id as id, i.number as numero, ti.tax_id as impuesto, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id " +
"as partner, i.amount_untaxed as baseinvoice, rp.name as empresa, rp.vat as cif, i.amount_total as total, t.name as nombreimpuesto, ti.base as base, ti.amount as " +
"cuota, ty.type_tax_use as type_tax_use, i.type as tipo from account_invoice_tax ti inner join account_tax t on ti.tax_id = t.id and t.id in %s and " +
"t.generate_sale_intra = 's' inner join type_taxes_information ty on t.type_taxes_information_id = ty.id and ty.type_tax_use = 'sale' inner join account_invoice " +
"i on ti.invoice_id = i.id and i.type in ('in_refund', 'in_invoice') and i.journal_id in %s and (i.date_invoice between %s and %s) inner join res_partner rp on " +
"i.partner_id = rp.id order by i.number", (tuple(taxes), tuple(journals), self.date_start, self.date_end))
            else:
              if partners:
                 self._cr.execute("SELECT i.id as id, i.number as numero, ti.tax_id as impuesto, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id " +
"as partner, i.amount_untaxed as baseinvoice, rp.name as empresa, rp.vat as cif, i.amount_total as total, t.name as nombreimpuesto, ti.base as base, ti.amount as " +
"cuota, ty.type_tax_use as type_tax_use, i.type as tipo from account_invoice_tax ti inner join account_tax t on ti.tax_id = t.id and " +
"t.generate_sale_intra = 's' inner join type_taxes_information ty on t.type_taxes_information_id = ty.id and ty.type_tax_use = 'sale' inner join account_invoice " +
"i on ti.invoice_id = i.id and i.type in ('in_refund', 'in_invoice') and i.partner_id in %s and (i.date_invoice between %s and %s) inner join res_partner rp " +
"on i.partner_id = rp.id order by i.number", (tuple(partners), self.date_start, self.date_end))
              else:
                 self._cr.execute("SELECT i.id as id, i.number as numero, ti.tax_id as impuesto, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id " +
"as partner, i.amount_untaxed as baseinvoice, rp.name as empresa, rp.vat as cif, i.amount_total as total, t.name as nombreimpuesto, ti.base as base, ti.amount as " +
"cuota, ty.type_tax_use as type_tax_use, i.type as tipo from account_invoice_tax ti inner join account_tax t on ti.tax_id = t.id and " +
"t.generate_sale_intra = 's' inner join type_taxes_information ty on t.type_taxes_information_id = ty.id and ty.type_tax_use = 'sale' inner join account_invoice " +
"i on ti.invoice_id = i.id and i.type in ('in_refund', 'in_invoice') and (i.date_invoice between %s and %s) inner join res_partner rp on i.partner_id = rp.id order " +
"by i.number", (self.date_start, self.date_end, ))
            dataintra = self._cr.dictfetchall()
            it = 1
            regd = False
            invoicereg = False
            for intra in dataintra:
                if invoicereg != intra['id']:
                   if intra['tipo'] == 'in_refund':
                    impfacti = {
                     'management_id': self.id,
                     'ref': 'INT' + str(it),
                     'type': 'Venta',
                     'invoice_date': intra['fecha'],
                     'partner_id': intra['partner'],
                     'vat_number': intra['cif'],
                     'invoice_id': intra['id'],
                     'tax_id': intra['impuesto'], 
                     'amount_untaxed': -intra['base'],
                     'amount_tax': -intra['cuota'],
                     'amount_total': intra['total'],
                    }
                   else:
                    #crear registro factura
                    cta = intra['cuota']
                    if intra['cuota'] < 0:
                       cta = -intra['cuota']
                    impfacti = {
                     'management_id': self.id,
                     'ref': 'INT' + str(it),
                     'type': 'Venta',
                     'invoice_date': intra['fecha'],
                     'partner_id': intra['partner'],
                     'vat_number': intra['cif'],
                     'invoice_id': intra['id'],
                     'tax_id': intra['impuesto'], 
                     'amount_untaxed': intra['base'],
                     'amount_tax': cta,
                     'amount_total': intra['total'],
                    }
                    regd = self.env['estructure.tax.line'].create(impfacti)
                else:
                    #modificar registro
                    if intra['tipo'] == 'in_refund':
                     impfacti = {
                      'management_id': self.id,
                      'invoice_id': intra['id'],
                      'tax_id': intra['impuesto'], 
                      'amount_untaxed': -intra['base'],
                      'amount_tax': -intra['cuota'],
                     }
                    else:
                     cta = intra['cuota']
                     if intra['cuota'] < 0:
                       cta = -intra['cuota']
                     impfacti = {
                      'management_id': self.id,
                      'invoice_id': intra['id'],
                      'tax_id': intra['impuesto'], 
                      'amount_untaxed': intra['base'],
                      'amount_tax': cta,
                     }
                     if regd:
                        regd2 = regd.write(impfacti)
                invoicereg = intra['id']
                it+=1

            #BUSCAR EL RESUMEN DE IVAS
            self.calculate_taxes_iva_summary()
            self.write({'name': 'Detalle de IVAS - Libro registro IVA', 'type': 'd'})
            """raise UserError(_('No EAT Tax Mapping was found'))"""

    def calculate_total_book(self):
      if self.state == 'draft':
        groups = [x.id for x in self.account_group_ids]
        journals = [x.id for x in self.journal_ids]
        partners = [x.id for x in self.partner_ids]
        for rec in self:
          if journals:
           if partners:
             self._cr.execute("SELECT sum(l.debit) as debe, sum(l.credit) as haber " +
"FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE l.journal_id IN %s and " +
"(m.date between %s and %s) and l.partner_id in %s", (tuple(journals), self.date_start, self.date_end, tuple(partners), ))
           else:
             self._cr.execute("SELECT sum(l.debit) as debe, sum(l.credit) as haber " +
"FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE l.journal_id IN %s and " +
"(m.date between %s and %s)", (tuple(journals), self.date_start, self.date_end, ))
          else:
           if partners:
             self._cr.execute("SELECT sum(l.debit) as debe, sum(l.credit) as haber " +
"FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE l.partner_id IN %s and " +
"(m.date between %s and %s)", (tuple(partners), self.date_start, self.date_end, ))
           else:
             self._cr.execute("SELECT sum(l.debit) as debe, sum(l.credit) as haber " +
"FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE (m.date between %s and %s)", (self.date_start, self.date_end, ))
          datagroupaccount = self._cr.dictfetchall()
          for groupa in datagroupaccount:
            rimpfact = {
                   'management_id': self.id,
                   'ref': 'TOTAL',
                   'amount_untaxed': groupa['debe'],
                   'amount_tax': groupa['haber'],
            }
            regr = self.env['estructure.tax.line'].create(rimpfact)


    def calculate_total_book_group(self):
      if self.state == 'draft':
        groups = [x.id for x in self.account_group_ids]
        journals = [x.id for x in self.journal_ids]
        partners = [x.id for x in self.partner_ids]
        for rec in self:
          if journals:
           if partners:
             self._cr.execute("SELECT sum(l.debit) as debe, sum(l.credit) as haber " +
"FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE l.journal_id IN %s and " +
"(m.date between %s and %s) and l.partner_id in %s and a.group_id in %s", (tuple(journals), self.date_start, self.date_end, tuple(partners), tuple(groups),))
           else:
             self._cr.execute("SELECT sum(l.debit) as debe, sum(l.credit) as haber " +
"FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE l.journal_id IN %s and " +
"(m.date between %s and %s) and a.group_id in %s", (tuple(journals), self.date_start, self.date_end, tuple(groups),))
          else:
           if partners:
             self._cr.execute("SELECT sum(l.debit) as debe, sum(l.credit) as haber " +
"FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE l.partner_id IN %s and " +
"(m.date between %s and %s) and a.group_id in %s", (tuple(partners), self.date_start, self.date_end, tuple(groups),))
           else:
             self._cr.execute("SELECT sum(l.debit) as debe, sum(l.credit) as haber " +
"FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE (m.date between %s and %s)" +
" and a.group_id in %s", (self.date_start, self.date_end, tuple(groups),))
          datagroupaccount = self._cr.dictfetchall()
          for groupa in datagroupaccount:
            rimpfact = {
                   'management_id': self.id,
                   'ref': 'TOTAL',
                   'amount_untaxed': groupa['debe'],
                   'amount_tax': groupa['haber'],
            }
            regr = self.env['estructure.tax.line'].create(rimpfact)


    def calculate_summary_book_balance4(self):
      if self.state == 'draft':
       if self.account_group_ids:
        groups = [x.id for x in self.account_group_ids]
        journals = [x.id for x in self.journal_ids]
        partners = [x.id for x in self.partner_ids]
        #GRABAR LINEA CON PERIODO Y FILTROS APLICADOS
        filtros = {
                   'management_id': self.id,
                   'ref': "Balance SyS 4 digitos desde " +  str(self.date_start)[8:10] + '-' + str(self.date_start)[5:7] + '-' + str(self.date_start)[0:4] + ' hasta ' + str(self.date_end)[8:10] + '-' + str(self.date_end)[5:7] + '-' + str(self.date_end)[0:4],
        }
        self.env['estructure.tax.line'].create(filtros)
        for rec in self:
           tax_model = self.env['account.tax']
           if journals and partners:
             self._cr.execute("SELECT sum(l.debit) as debe, sum(l.credit) as haber, ag.code_prefix as codigo, a.group_id as cuenta, ag.name as ncuenta FROM account_move_line l left join account_move m on l.move_id = m.id inner join account_account a on " +
"l.account_id = a.id inner join account_group ag on a.group_id = ag.id WHERE l.journal_id IN %s " +
"and (m.date between %s and %s) and l.partner_id in %s and a.group_id in %s group by a.group_id, ag.code_prefix, ag.name order by ag.code_prefix", (tuple(journals), self.date_start, self.date_end, tuple(partners), tuple(groups), ))
           else:
             if partners:
                self._cr.execute("SELECT sum(l.debit) as debe, sum(l.credit) as haber, ag.code_prefix as codigo, a.group_id as cuenta, ag.name as ncuenta FROM account_move_line l left join account_move m on l.move_id = m.id inner join account_account a on " +
"l.account_id = a.id inner join account_group ag on a.group_id = ag.id WHERE " +
"(m.date between %s and %s) and l.partner_id in %s and a.group_id in %s group by a.group_id, ag.code_prefix, ag.name order by ag.code_prefix", (self.date_start, self.date_end, tuple(partners), tuple(groups), ))
             else:
                self._cr.execute("SELECT sum(l.debit) as debe, sum(l.credit) as haber, a.group_id as cuenta, ag.code_prefix as codigo, ag.name as ncuenta FROM account_move_line l left join account_move m on l.move_id = m.id inner join account_account a on " +
"l.account_id = a.id inner join account_group ag on a.group_id = ag.id WHERE (m.date between %s and %s) and a.group_id in %s group by a.group_id, ag.code_prefix, ag.name order by ag.code_prefix", (self.date_start, self.date_end, tuple(groups), ))
           datagroupaccount = self._cr.dictfetchall()
           for groupa in datagroupaccount:
            #crear registro libro resumen
            rimpfact = {
                   'management_id': self.id,
                   'ref': groupa['codigo'] + " - " + groupa['ncuenta'],
                   'account_group_id': groupa['cuenta'], 
                   #'year': groupa['ejercicio'],
                   'amount_refund_untaxed': groupa['debe'] - groupa['haber'],
                   'amount_untaxed': groupa['debe'],
                   'amount_tax': groupa['haber'],
            }
            regr = self.env['estructure.tax.line'].create(rimpfact)
            #raise Warning(regr)
        self.calculate_total_book_group()
        self.write({'name': 'Balance SyS 4 digits', 'type': 'b4'})         
       else:
         raise UserError(_('Rellene los grupos de cuentas a consultar'))



    def calculate_summary_book(self):
      if self.state == 'draft':
       if self.account_group_ids:
        groups = [x.id for x in self.account_group_ids]
        journals = [x.id for x in self.journal_ids]
        partners = [x.id for x in self.partner_ids]
        #GRABAR LINEA CON PERIODO Y FILTROS APLICADOS
        filtros = {
                   'management_id': self.id,
                   'ref': "Libro resumen contable desde " +  str(self.date_start)[8:10] + '-' + str(self.date_start)[5:7] + '-' + str(self.date_start)[0:4] + ' hasta ' + str(self.date_end)[8:10] + '-' + str(self.date_end)[5:7] + '-' + str(self.date_end)[0:4],
        }
        self.env['estructure.tax.line'].create(filtros)
        if journals and partners:
           self._cr.execute("SELECT to_char(m.date, 'YYYY') as ejercicio, to_char(m.date, 'MM') as mes, sum(l.debit) as debe, sum(l.credit) as haber FROM account_move_line " +
"l left join account_move m on l.move_id = m.id inner join accoun_account a on " +
"l.account_id = a.id inner join account_group ag on a.group_id = ag.id WHERE l.journal_id IN %s " +
"and (m.date between %s and %s) and l.partner_id in %s and a.group_id in %s group by to_char(m.date, 'YYYY'), to_char(m.date, 'MM') order by to_char(m.date, 'YYYY'), " + 
"to_char(m.date, 'MM')", (tuple(journals), self.date_start, self.date_end, tuple(partners), tuple(groups), ))
        else:
           if partners:
             self._cr.execute("SELECT to_char(m.date, 'YYYY') as ejercicio, to_char(m.date, 'MM') as mes, sum(l.debit) as debe, sum(l.credit) as haber FROM account_move_line " +
"l left join account_move m on l.move_id = m.id inner join account_account a on " +
"l.account_id = a.id inner join account_group ag on a.group_id = ag.id WHERE " +
"(m.date between %s and %s) and l.partner_id in %s and a.group_id in %s group by to_char(m.date, 'YYYY'), to_char(m.date, 'MM') order by to_char(m.date, 'YYYY'), " + 
"to_char(m.date, 'MM')", (self.date_start, self.date_end, tuple(partners), tuple(groups), ))
           else:
             self._cr.execute("SELECT to_char(m.date, 'YYYY') as ejercicio, to_char(m.date, 'MM') as mes, sum(l.debit) as debe, sum(l.credit) as haber FROM account_move_line " +
"l left join account_move m on l.move_id = m.id inner join account_account a on " +
"l.account_id = a.id inner join account_group ag on a.group_id = ag.id WHERE (m.date between %s and %s) and a.group_id in %s group by to_char(m.date, 'YYYY'), to_char(m.date, 'MM') " + 
"order by to_char(m.date, 'YYYY'), " + 
"to_char(m.date, 'MM')", (self.date_start, self.date_end, tuple(groups), ))
        datamonths = self._cr.dictfetchall()
        for regmonth in datamonths: 
         for rec in self:
           tax_model = self.env['account.tax']
           if journals and partners:
             self._cr.execute("SELECT to_char(m.date, 'YYYY') as ejercicio, to_char(m.date, 'MM') as mes, sum(l.debit) as debe, sum(l.credit) as haber, ag.code_prefix as codigo, a.group_id as cuenta, ag.name as ncuenta FROM account_move_line l left join account_move m on l.move_id = m.id inner join account_account a on " +
"l.account_id = a.id inner join account_group ag on a.group_id = ag.id WHERE l.journal_id IN %s " +
"and (m.date between %s and %s) and l.partner_id in %s and a.group_id in %s group by a.group_id, ag.code_prefix, ag.name, to_char(m.date, 'YYYY'), to_char(m.date, 'MM') order by to_char(m.date, 'YYYY'), " + 
"to_char(m.date, 'MM'), ag.code_prefix", (tuple(journals), self.date_start, self.date_end, tuple(partners), tuple(groups), ))
           else:
             if partners:
                self._cr.execute("SELECT to_char(m.date, 'YYYY') as ejercicio, to_char(m.date, 'MM') as mes, sum(l.debit) as debe, sum(l.credit) as haber, ag.code_prefix as codigo, a.group_id as cuenta, ag.name as ncuenta FROM account_move_line l left join account_move m on l.move_id = m.id inner join account_account a on " +
"l.account_id = a.id inner join account_group ag on a.group_id = ag.id WHERE " +
"(m.date between %s and %s) and l.partner_id in %s and a.group_id in %s group by a.group_id, ag.code_prefix, ag.name, to_char(m.date, 'YYYY'), to_char(m.date, 'MM') order by to_char(m.date, 'YYYY'), " + 
"to_char(m.date, 'MM'), ag.code_prefix", (self.date_start, self.date_end, tuple(partners), tuple(groups), ))
             else:
                self._cr.execute("SELECT to_char(m.date, 'YYYY') as ejercicio, to_char(m.date, 'MM') as mes, sum(l.debit) as debe, sum(l.credit) as haber, a.group_id as cuenta, ag.code_prefix as codigo, ag.name as ncuenta FROM account_move_line l left join account_move m on l.move_id = m.id inner join account_account a on " +
"l.account_id = a.id inner join account_group ag on a.group_id = ag.id WHERE (m.date between %s and %s) and a.group_id in %s and to_char(m.date, 'MM') = %s group by a.group_id, ag.code_prefix, ag.name, to_char(m.date, 'YYYY'), to_char(m.date, 'MM') order by to_char(m.date, 'YYYY'), " + 
"to_char(m.date, 'MM'), ag.code_prefix", (self.date_start, self.date_end, tuple(groups), regmonth['mes'], ))
           datagroupaccount = self._cr.dictfetchall()
           for groupa in datagroupaccount:
            #crear registro libro resumen
            rimpfact = {
                   'management_id': self.id,
                   'ref': groupa['codigo'] + " - " + groupa['ncuenta'],
                   'account_group_id': groupa['cuenta'], 
                   'year': groupa['ejercicio'],
                   'month': groupa['mes'],
                   'amount_untaxed': groupa['debe'],
                   'amount_tax': groupa['haber'],
            }
            regr = self.env['estructure.tax.line'].create(rimpfact)
            #raise Warning(regr)
         #crear registro grupo cuentas
         rimpfact = {
                   'management_id': self.id,
                   'ref': 'TOTAL MES ' + regmonth['mes'],
                   #'year': regmonth['ejercicio'],
                   #'month': regmonth['mes'],
                   'amount_untaxed': regmonth['debe'],
                   'amount_tax': regmonth['haber'],
         }
         regr = self.env['estructure.tax.line'].create(rimpfact)
        self.calculate_total_book_group()
        self.write({'name': 'Summary Book', 'type': 'b'})         
       else:
         raise UserError(_('Rellene los grupos de cuentas a consultar'))


    def calculate_details_book(self):
      if self.state == 'draft':
        groups = [x.id for x in self.account_group_ids]
        journals = [x.id for x in self.journal_ids]
        partners = [x.id for x in self.partner_ids]
        #GRABAR LINEA CON PERIODO Y FILTROS APLICADOS
        filtros = {
                   'management_id': self.id,
                   'ref': "Libro contable detallado desde " +  str(self.date_start)[8:10] + '-' + str(self.date_start)[5:7] + '-' + str(self.date_start)[0:4] + ' hasta ' + str(self.date_end)[8:10] + '-' + str(self.date_end)[5:7] + '-' + str(self.date_end)[0:4],
        }
        self.env['estructure.tax.line'].create(filtros)

        for rec in self:
          if journals:
           if partners:
             self._cr.execute("SELECT m.id as id, m.name as asiento, to_char(m.date, 'YYYY-MM-DD') as fecha, l.name as comentario, p.id as partner, p.name as empresa, l.debit as debe, l.credit as haber, a.id as idcuenta, a.code as cuenta, " +
"a.name as ncuenta FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE l.journal_id IN %s and " +
"(m.date between %s and %s) and l.partner_id in %s order by m.name", (tuple(journals), self.date_start, self.date_end, tuple(partners), ))
           else:
             self._cr.execute("SELECT m.id as id, m.name as asiento, to_char(m.date, 'YYYY-MM-DD') as fecha, l.name as comentario, p.id as partner, p.name as empresa, l.debit as debe, l.credit as haber, a.id as idcuenta, a.code as cuenta, " +
"a.name as ncuenta FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE l.journal_id IN %s and " +
"(m.date between %s and %s) order by m.name", (tuple(journals), self.date_start, self.date_end, ))
          else:
           if partners:
             self._cr.execute("SELECT m.id as id, m.name as asiento, to_char(m.date, 'YY-MM-DD') as fecha, l.name as comentario, p.id as partner, p.name as empresa, l.debit as debe, l.credit as haber, a.id as idcuenta, a.code as cuenta, " +
"a.name as ncuenta FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE l.partner_id IN %s and " +
"(m.date between %s and %s) order by m.name", (tuple(partners), self.date_start, self.date_end, ))
           else:
             self._cr.execute("SELECT m.id as id, m.name as asiento, to_char(m.date, 'YYYY-MM-DD') as fecha, l.name as comentario, p.id as partner, p.name as empresa, l.debit as debe, l.credit as haber, a.id as idcuenta, a.code as cuenta, " +
"a.name as ncuenta FROM account_move_line l left join account_move m on l.move_id = m.id left join res_partner p on l.partner_id = p.id inner join account_account a on l.account_id = a.id WHERE (m.date between %s and %s) " +
"order by m.name", (self.date_start, self.date_end, ))
          datagroupaccount = self._cr.dictfetchall()
          for groupa in datagroupaccount:
            rimpfact = {
                   'management_id': self.id,
                   'ref': groupa['comentario'],
                   'account_id': groupa['idcuenta'], 
                   'move_id': groupa['id'],
                   'partner_id': groupa['partner'],
                   'invoice_date': groupa['fecha'],
                   'amount_untaxed': groupa['debe'],
                   'amount_tax': groupa['haber'],
            }
            regr = self.env['estructure.tax.line'].create(rimpfact)
            self.write({'name': 'Details Book', 'type': 'bd'})
        self.calculate_total_book()


    @api.multi
    def btn_details_book(self):
        res = self.calculate_details_book()
        self.write({'state': 'calculated',
                    'calculation_date': fields.Datetime.now()})
        return res

    @api.multi
    def btn_taxes_iva_summary(self):
        res = self.calculate_taxes_iva_summary()
        self.write({'state': 'calculated',
                    'calculation_date': fields.Datetime.now()})
        return res
    @api.multi
    def btn_taxes_iva_details(self):
        res = self.calculate_details_taxes_iva()
        self.write({'state': 'calculated',
                    'calculation_date': fields.Datetime.now()})

    @api.multi
    def btn_summary_book(self):
        res = self.calculate_summary_book()
        self.write({'state': 'calculated',
                    'calculation_date': fields.Datetime.now()})
        return res

    @api.multi
    def btn_summary_book_balance4(self):
        res = self.calculate_summary_book_balance4()
        self.write({'state': 'calculated',
                    'calculation_date': fields.Datetime.now()})
        return res

    @api.multi
    def export_xlsx(self):
        self.ensure_one()
        context = dict(self.env.context, active_ids=self.ids)
        """raise Warning({
            'name': 'Details Taxes XLSX report',
            'model': 'management.fiscal.accounting.information',
            'type': 'ir.actions.report',
            'report_name': 'management_fiscal_accounting_information.details_taxes_xlsx',
            'report_type': 'xlsx',
            'report_file': 'details.vat.book',
            'context': context,
        })"""
        return {
            'name': 'Details Taxes XLSX report',
            'model': 'management_fiscal_accounting_information.ManagementFiscalAccountingInformation',
            'type': 'ir.actions.report',
            'report_name': 'management_fiscal_accounting_information.details_taxes_xlsx',
            'report_type': 'xlsx',
            #'report_file': 'details.vat.book',
            'context': context,
        }

