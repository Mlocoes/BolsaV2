Vamos crear una app robusta, segura, multiusuario, escalable, en Python, Docker y Docker-compose y PostgreSQL.
Vamos trabajar en 3 etapas:
1 – Base de datos.
Vamos crear una base de datos con toda las tablas y campos necesarios:
	1 – Tabla de usuarios.
	2 - Tabla de valores (acciones, fondos, etc).
	3 – Tabla de cotizaciones de los valores.
	4 – Tabla de operaciones.
	5 – Tabla de carteras.
	6 – Tabla de resultados.
2 – Backend.
Debe estar escrito en Python funcionando dentro de un contenedor Docker a través de un Dockfile y Docker-Compose.
Debe tener previsto archivo de ambiente de ejemplo.
Todos los datos sensibles (credenciales, urls, direcciones de correo, directorios de sistema, etc) deben estar guardadas en este archivo .env, nunca hardcordeadas.
El Backend debe ser factorable con uso de las mejores prácticas, escalable y totalmente independente del frontend para que sea muy sencillo el cambio de frontend.
Debe tener sistemas de seguridad robusto con uso de credenciales guardadas en memoria y utilizadas para garantir la seguridad de las llamadas de las APIs internas. Las credenciales deben ser perdidas en caso de recarga de la tela y nuevamente solicitadas (nuevo login) previsto no frontend.
Prever todos los tipos de vulnerabilidades conocidas de las herramientas utilizadas.
Los datos de cotizaciones deben ser obtenidos con el uso de la API Finnhub-Stock-API, existe un repositorio público para consultar informaciones: https://github.com/Finnhub-Stock-API/finnhub-python.git.
3 – Frontend.
Debe ser moderno, con colores sobrios (un sistema empresarial), con visiones tanto en ordenador como en móvil.
Debe hacer uso de Handsontable para crear las tablas de información, cotizaciones, operaciones, etc.
El frontend debe ser totalmente modular para que se pueda cambiar.
Las telas del Frontend:
	1 – Login. Una tela sencilla de login que permita entrar las credenciales (nombre/contraseña). Siempre que ocurre una carga en el sistema esta tela debe ser carregada y pedir nuevas credenciales.
	2 – Dashboard – Enseña las carteras que posee el usuario. Al clicar sobre el nombre de la cartera se abre las posiciones de esta cartera y se enseña sus datos (nombre del valor, C/V, cuantidad, precio de compra, ultimo precio conocido, financiero de compra, financiero actual, resultado del día, porcentual del resultado del día, resultado acumulado y porcentual del resultado acumulado) en una tabla (Handsontable) no editable. Un grafico con los resultados mes a mes de todas las carteras sumadas.
	3 – Catastro de Valores. Enseña una tabla (Handsontable) editable con todos los tickets catastrados en la BD, permitido cambios de tickets y exclusiones de los mismos.
	4 – Catastro de Carteras. Pide un nombre, se abre una tabla (Handsontable) editable para catastrar las operaciones, los datos pedidos deben ser: Fecha, nombre del valor, C/V, cuantidad y precio. Un usuario puede tener mas de una cartera.
	5 – Catastro de usuarios. Pide datos básicos como: Nombre de usuario, contraseña y email.
	6 – Tela de importación de datos.
		Esa tela tendrá:
 	Un botón de importar las cotizaciones históricas de los nuevos valores catastrados.
	Un botón de importar las ultimas cotizaciones de los valores catastrados.
	Un botón para importar varias operaciones de una cartera del usuario a través de un Excel. El modelo del Excel que se debe respetar será fornecido.
Vamos desarrollar el sistema etapa a etapa.
El sistema debe tener previsto un script de instalación que pide datos como las credenciales del usuario administrador, credenciales de la BD, etc. Eses datos deben ser guardados en un único archivo .env para todo el sistema.
Este script además debe verificar las dependencias del sistema e instalarlas si no están presentes, hacer la descarga del sistema del repositorio Github del sistema si no está hecho, crear la base de datos con las credenciales fornecidas si no está creada, crear el usuario administrador si no este creado y empezar el sistema. Siempre se debe preguntar antes de hacer cualquier paso.
Al final del desarrollo debe hacer un README.md con la información de todo el sistema y inicializar el repositorio en Github  - https://github.com/Mlocoes/BolsaV2.git
Haga un prompt con todo eso.
