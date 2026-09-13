"""Expert mode: render an attack image from YOUR payload.

    nano payload.txt          write your own instruction
    python craft.py           render it into invoices/invoice-attack.png

The rest of the pipeline does not change. You are choosing what the invoice
says to the machine, while the paper still says $8,750.00 and net 30.
"""
from make_invoices import craft

craft()
