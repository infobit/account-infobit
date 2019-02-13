# encoding: utf-8
{
	"name" : "Replace description the account move of invoices and add field account_id in lines of view bank statement",
	"version" : "0.1",
	"description" : """
Replace description the account move of sale invoices and add field account_id in view of bank statement lines
Developed for Infobit informatica s.l.
        """,
	"author" : "Infobit",
	"website" : "http://www.infobitinformatica.es",
	"depends" : [ 
		'account', 'l10n_es_account_invoice_sequence'
	], 
	"category" : "Partner Modules",
	"init_xml" : [],
	"demo_xml" : [],
	"data" : ['views/bank_statement.xml'],
	"installable": True
}
