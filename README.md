# Proyecto de Pruebas de Software - NextCRM

Este repositorio es un proyecto académico desarrollado para el curso de Pruebas de Software. A partir de una aplicación base pública de código abierto llamada NextCRM, se implementó una suite completa de pruebas de software automatizadas. El alcance del proyecto se limita exclusivamente al diseño, desarrollo y ejecución de pruebas, sin añadir nuevas funcionalidades de negocio al producto.

---

## Estructura del Repositorio de Pruebas

Toda la lógica de pruebas automatizadas está centralizada en el directorio tests, organizada en las siguientes categorías:

### 1. Pruebas Unitarias
Ubicadas en tests/units. Verifican el comportamiento aislado de las funciones puras, esquemas de validación, hooks y componentes de interfaz de usuario del CRM básico.
* **Herramientas:** Vitest y React Testing Library.
* **Estrategia:** Aislamiento completo reemplazando las dependencias externas (PostgreSQL, Prisma, sesión de autenticación y navegación de Next.js) por dobles de prueba (mocks, stubs y spies).

### 2. Pruebas de Integración
Ubicadas en tests/integration. Verifican la interacción entre múltiples componentes de software locales, como Server Actions, base de datos y flujos de segundo plano.
* **Herramientas:** Vitest y Prisma Client.
* **Estrategia:** Pruebas contra una base de datos local de pruebas, interactuando con esquemas reales y simulando el ciclo de vida de transacciones y autenticación.

### 3. Pruebas de Sistema (End-to-End)
Ubicadas en tests/e2e. Evalúan el sistema completo desde la perspectiva del usuario final, automatizando flujos de navegación en navegadores reales.
* **Herramientas:** Playwright.
* **Estrategia:** Implementación del patrón Page Object Model (POM) para aislar la estructura de la interfaz de la lógica del test. Los escenarios cubren flujos completos de venta, transiciones de estados y control de acceso según roles de usuario.

### 4. Pruebas de Rendimiento
Ubicadas en tests/performance. Evalúan el comportamiento de la aplicación bajo diferentes perfiles de carga y concurrencia.
* **Herramientas:** k6 y Python (matplotlib).
* **Estrategia:** Simulación de escenarios de carga estable, estrés progresivo, picos repentinos de tráfico y estabilidad sostenida. Incluye utilidades para extraer dinámicamente identificadores de la aplicación y generar gráficos analíticos de percentiles de latencia y tasas de error.

---

## Requisitos del Entorno

Para configurar el entorno y ejecutar las pruebas es necesario contar con:
* Node.js v22.12.0 o superior
* pnpm v9.0.0 o superior
* Base de datos PostgreSQL v17 o superior con la extensión pgvector habilitada
* Python 3 con soporte para matplotlib (para la generación de gráficos de rendimiento)

---

## Instalación y Configuración

1. Clonar el repositorio localmente:
   ```sh
   git clone https://github.com/ynoacamino/nextcrm-app.git
   cd nextcrm-app
   ```

2. Instalar las dependencias del proyecto:
   ```sh
   pnpm install
   ```

3. Configurar el archivo de variables de entorno:
   ```sh
   cp .env.example .env
   ```
   Definir en el archivo .env las credenciales de conexión para la base de datos de pruebas (DATABASE_URL) y la clave secreta de autenticación.

4. Inicializar y migrar el esquema de la base de datos:
   ```sh
   pnpm prisma generate
   pnpm prisma migrate deploy
   ```

5. Cargar los datos iniciales requeridos:
   ```sh
   pnpm prisma db seed
   ```

---

## Guía de Ejecución de Pruebas

Los scripts de ejecución rápida están predefinidos y se pueden invocar directamente desde la consola:

### Ejecución de Pruebas Unitarias
* Ejecutar todas las pruebas unitarias:
  ```sh
  pnpm run test:unit
  ```
* Ejecutar pruebas unitarias en modo de observación continua (watch):
  ```sh
  pnpm run test:unit:watch
  ```

### Ejecución de Pruebas de Integración
* Ejecutar todas las pruebas de integración:
  ```sh
  pnpm run test:integration
  ```
* Ejecutar pruebas de integración en modo de observación continua:
  ```sh
  pnpm run test:integration:watch
  ```

### Ejecución de Pruebas de Sistema (E2E)
* Ejecutar todas las pruebas de sistema en segundo plano:
  ```sh
  pnpm run test:e2e
  ```
* Abrir la interfaz interactiva de Playwright:
  ```sh
  pnpm run test:e2e:ui
  ```
* Ejecutar las pruebas mostrando el navegador de forma gráfica:
  ```sh
  pnpm run test:e2e:headed
  ```
* Ejecutar pruebas en modo de depuración:
  ```sh
  pnpm run test:e2e:debug
  ```

### Ejecución de Pruebas de Rendimiento (k6)
Antes de ejecutar los escenarios de rendimiento, es necesario levantar el servidor de pruebas y extraer los datos requeridos.

1. Recolectar identificadores de la base de datos y de la aplicación:
   ```sh
   pnpm run perf:collect-actions
   pnpm run perf:collect-entities
   ```

2. Ejecutar un escenario de carga específico (load, stress, spike o soak):
   * Humo (Smoke Test):
     ```sh
     pnpm run perf:smoke
     ```
   * Carga estable (Load Test):
     ```sh
     pnpm run perf:load
     ```
   * Estrés progresivo (Stress Test):
     ```sh
     pnpm run perf:stress
     ```
   * Picos de tráfico (Spike Test):
     ```sh
     pnpm run perf:spike
     ```
   * Estabilidad (Soak Test):
     ```sh
     pnpm run perf:soak
     ```

3. Generar gráficos analíticos de las ejecuciones previas:
   ```sh
   pnpm run perf:charts
   ```

---

## Documentación del Proyecto

El proceso completo de diseño y planificación de pruebas está documentado en la sección Wiki de este repositorio. Las páginas clave incluyen:
* Planificaciones específicas: planes de pruebas unitarias, integración, sistema y rendimiento.
* Diseños detallados: casos de prueba unitarios, de integración, funcionales, de sistema y rendimiento.
* Informes de resultados: evidencia de ejecución de pruebas unitarias, de integración, funcionales y de sistema.
* Registro y análisis de fallos: informe de bugs críticos corregidos y de errores de pruebas funcionales.
