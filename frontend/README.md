# Documentación del Frontend - BolsaV2

## 📋 Descripción General

El frontend de BolsaV2 es una aplicación de una sola página (SPA) construida con **React 18** y **TypeScript**. Se enfoca en la velocidad, la interactividad y la visualización de datos financieros complejos. Utiliza **Vite** como herramienta de construcción para un desarrollo ultrarrápido.

## 🛠️ Tecnologías Clave

- **React 18**: Librería de UI.
- **TypeScript**: Tipado estático para mayor robustez.
- **Vite**: Build tool y servidor de desarrollo.
- **Tailwind CSS**: Framework de utilidades CSS para diseño rápido y responsivo.
- **Handsontable**: Componente de hoja de cálculo para edición masiva y visualización de datos tabulares.
- **Zustand**: Gestión de estado global ligero y eficiente.
- **React Router DOM**: Enrutamiento del lado del cliente.
- **Recharts**: Librería de gráficos para visualizar el rendimiento del portafolio.

## 📂 Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/     # Componentes UI reutilizables (Botones, Modales, Gráficos)
│   ├── pages/          # Componentes de página (Vistas completas)
│   │   ├── Dashboard.tsx       # Vista principal
│   │   ├── AssetsCatalog.tsx   # Catálogo de activos (Handsontable)
│   │   ├── Quotes.tsx          # Visualizador de cotizaciones
│   │   └── ...
│   ├── services/       # Clientes API (Axios) y definición de tipos de respuesta
│   ├── stores/         # Stores de Zustand (Auth, UI State)
│   ├── styles/         # CSS global y configuraciones de Tailwind
│   ├── App.tsx         # Configuración de rutas y layout principal
│   └── main.tsx        # Punto de entrada
├── public/             # Assets estáticos
└── vite.config.ts      # Configuración de Vite
```

## 🚀 Configuración y Ejecución Local

### 1. Prerrequisitos
- Node.js 18+
- npm o yarn

### 2. Instalación de Dependencias

```bash
cd frontend
npm install
```

### 3. Variables de Entorno

Crea un archivo `.env` en `frontend/`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

### 4. Ejecución en Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000` (o el puerto que indique Vite).

## 🧩 Componentes Clave

### Handsontable (`AssetsCatalog.tsx`, `Quotes.tsx`)
Utilizamos Handsontable para ofrecer una experiencia similar a Excel.
- **Características**: Ordenamiento, filtrado, edición en línea (donde se permite), y renderizado eficiente de grandes conjuntos de datos.
- **Personalización**: Se utilizan "Renderers" personalizados para botones de acción y formato de números/monedas.

### Gráficos (`PerformanceChart.tsx`)
Implementados con Recharts. Muestran la evolución del valor del portafolio a lo largo del tiempo basándose en los `Snapshots` calculados por el backend.

## 📦 Construcción para Producción

Para generar los archivos estáticos optimizados:

```bash
npm run build
```

Los archivos se generarán en la carpeta `dist/`, listos para ser servidos por Nginx o cualquier servidor web estático.

## ⚠️ Notas de Desarrollo

- **Docker**: Si ejecutas el frontend dentro de Docker, recuerda que el "Hot Reload" puede no funcionar automáticamente dependiendo de la configuración de volúmenes. Se recomienda desarrollar localmente (`npm run dev`) contra el backend en Docker o local.
