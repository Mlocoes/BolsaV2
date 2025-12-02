Plus Valia Fiscal.
Vamos desarrollar una nueva funcionalidad.
Empecemos por la lógica de funcionamiento:
1 – Sera una forma de calculo de los resultados fiscales de las operaciones en bolsa.
2 – En España el sistema fiscal vigente es el FIFO (First In, First Out), asi, voy explicar su funcionamiento con ejemplos para que pueda implementar el código.
	Caso 1 – Hacemos las siguientes transacciones:
	01/01/25 – compra de 100 NVDA a USD 120. Cierre de NVDA a USD 125.
	05/01/25 – compra de 100 NVDA a USD 130. Cierre de NVDA a USD 140.
	10/01/25 - Tenemos de posición 200 NVDA a USD 125. Cierre de NVDA a USD 150.
	20/01/25 – venta de 50 NVDA a USD 150. Cierre de NVDA a USD 160. Primero resultado fiscal. Resultado = 50(cuantidad venta) * (150(precio de venta) – 120(precio de la compra)) = 1500. Posición 150 NVDA a (50 a 120 + 100 a 130) USD 126,67.
	25/01/25 – venta de 100 a USD 125. Cierre de NVDA a USD 125. Segundo resultado fiscal. Resultado = (50(cuantidad venta) * (125(precio de venta) – 120(precio de la compra))) + (50(cuantidad venta) * (125(precio de venta) – 130(precio de la compra))) = 250 – 250 = 0. Posición 50 NVDA a USD 130.
	26/01/25 – venta de 50 NVDA a USD 120. Cierre de NVDA a USD 120. Tercero resultado fiscal. Resultado = 50(cuantidad venta) * (120(precio de venta) – 130(precio de la compra)) = -500. Posición cero.
Resultados fiscales:
20/01/25 = 1500
25/01/25 = 0
26/01/25 = -500
Resultado fiscal total = 1500 + 0 – 500 = 1000.
Pasaría lo mismo si empecemos con una posición en corto, pero las compras generarían los cierres de posición o los resultados fiscales.
Esta nueva funcionalidad debe tener una nueva pantalla “Resultado Fiscal”.
Los resultados deben ser presentados en una tabla Handsontable.
Debe haber seleccionadores de fechas, inicio y fin, para enseñar en la tabla.
La tabla debe enseñar los siguientes datos por línea:
Fecha de venta – fecha de compra – cuantidad venta – precio de venta – precio de compra – resultado fiscal.
