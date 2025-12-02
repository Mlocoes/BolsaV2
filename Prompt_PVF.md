Prompt para Desarrollo de Funcionalidad: Plusvalía Fiscal (FIFO)
Contexto
Desarrollar una nueva funcionalidad para calcular los resultados fiscales de operaciones bursátiles según el método FIFO (First In, First Out) vigente en España.
Requisitos Funcionales
1. Lógica de Cálculo FIFO
Implementar el sistema FIFO donde:

Las primeras acciones compradas son las primeras en venderse
Cada venta genera un resultado fiscal calculando la diferencia entre precio de venta y precio de compra de las acciones correspondientes
El sistema debe funcionar tanto para posiciones largas (compra-venta) como posiciones cortas (venta-compra)

2. Ejemplo de Implementación
Secuencia de operaciones NVDA:
01/01/25: Compra 100 @ $120
05/01/25: Compra 100 @ $130
          Posición total: 200 NVDA

20/01/25: Venta 50 @ $150
          Resultado fiscal: 50 × ($150 - $120) = $1,500
          Posición restante: 150 NVDA (50@$120 + 100@$130)

25/01/25: Venta 100 @ $125
          Resultado fiscal: 
          - 50 × ($125 - $120) = $250
          - 50 × ($125 - $130) = -$250
          Total: $0
          Posición restante: 50 NVDA @ $130

26/01/25: Venta 50 @ $120
          Resultado fiscal: 50 × ($120 - $130) = -$500
          Posición: 0

Resultado fiscal total del período: $1,500 + $0 - $500 = $1,000
3. Interfaz de Usuario
Nueva pantalla: "Resultado Fiscal"
Componentes necesarios:

Selector de fechas: Rango inicio-fin para filtrar resultados
Tabla Handsontable con las siguientes columnas:

Fecha de Venta
Fecha de Compra
Cantidad Vendida
Precio de Venta
Precio de Compra
Resultado Fiscal



4. Especificaciones Técnicas
Tabla Handsontable debe incluir:

Formato numérico apropiado para cantidades y precios
Formato de moneda para resultados fiscales
Formato de fecha consistente
Totalizador al final mostrando el resultado fiscal acumulado
Ordenamiento por fecha de venta por defecto
Capacidad de exportar datos (opcional pero recomendado)

Cálculo de resultados:

Mantener un registro histórico de todas las compras pendientes de cerrar (cola FIFO)
Al producirse una venta, extraer de la cola las compras más antiguas hasta completar la cantidad vendida
Si una venta requiere múltiples compras, generar múltiples líneas en la tabla de resultados
Actualizar la posición restante después de cada operación

Consideraciones adicionales:

Manejar correctamente las posiciones cortas (invertir lógica: venta primero, compra cierra posición)
Validar que no se vendan más acciones de las disponibles en posición
Considerar comisiones si aplican al cálculo fiscal
Manejar múltiples símbolos/activos de forma independiente

5. Formato de Salida Esperado
La tabla debe mostrar cada emparejamiento compra-venta individualmente:
Fecha VentaFecha CompraCantidadPrecio VentaPrecio CompraResultado Fiscal20/01/2501/01/2550$150.00$120.00$1,500.0025/01/2501/01/2550$125.00$120.00$250.0025/01/2505/01/2550$125.00$130.00-$250.0026/01/2505/01/2550$120.00$130.00-$500.00TOTAL$1,000.00
6. Validaciones Necesarias

Verificar que las fechas de venta sean posteriores o iguales a las fechas de compra
Alertar si se intenta vender sin posición disponible
Validar rangos de fechas del selector (inicio ≤ fin)
Manejar casos edge: ventas el mismo día, múltiples operaciones simultáneas

