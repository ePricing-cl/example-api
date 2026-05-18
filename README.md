# Integración de ejemplo con la API interna de ePricing

> Para documentación de integración más formal y orientada a API, revisar [GUIA_INTEGRACION_API.md](GUIA_INTEGRACION_API.md).

Este proyecto entrega un ejemplo mínimo de consumo de la API interna de ePricing usando autenticación OAuth2 con `client_credentials`.

El objetivo es que el equipo técnico del cliente pueda:

- configurar sus credenciales de acceso mediante variables de entorno,
- ejecutar una solicitud de ejemplo a la API,
- obtener una URL de descarga entregada por el servicio,
- descargar automáticamente el archivo resultante.

## Contenido del proyecto

- [epricing_api.py](epricing_api.py): script de ejemplo para autenticación, consulta y descarga.
- [.env.example](.env.example): plantilla de variables de entorno requeridas.
- [pyproject.toml](pyproject.toml): definición base del proyecto y dependencias.

## Requisitos

- Python 3.12 o superior.
- Credenciales válidas de acceso a ePricing.
- Acceso de red a los endpoints entregados por ePricing.

## Variables de entorno requeridas

El archivo [.env.example](.env.example) define las variables que deben mantenerse parametrizadas:

- `CLIENT_ID`: identificador del cliente OAuth.
- `CLIENT_SECRET`: secreto del cliente OAuth.
- `EPRICING_OAUTH_URL`: endpoint de obtención de token.
- `EPRICING_API_URL`: endpoint principal de consulta de la API.

> Importante: estas variables no deben quedar hardcodeadas en el código. Deben mantenerse externas y parametrizadas, ya que sus valores pueden cambiar en el tiempo.

## Configuración

1. Crear un archivo `.env` a partir de [.env.example](.env.example).
2. Completar los valores reales entregados por ePricing.

Ejemplo:

```env
CLIENT_ID=valor_entregado_por_epricing
CLIENT_SECRET=valor_entregado_por_epricing
EPRICING_OAUTH_URL=https://...
EPRICING_API_URL=https://...
```

## Instalación

### Opción 1: usando `pip`

Crear un entorno virtual e instalar dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install requests python-dotenv
```

### Opción 2: usando el proyecto tal como está definido

Si se utiliza una herramienta compatible con [pyproject.toml](pyproject.toml), instalar las dependencias del proyecto según el flujo habitual del cliente.

Las dependencias actuales son:

- `requests`
- `python-dotenv`

## Ejecución

Con el entorno ya configurado y el archivo `.env` completo:

```bash
python epricing_api.py
```

## Flujo que implementa el script

El script [epricing_api.py](epricing_api.py) realiza lo siguiente:

1. Carga variables de entorno desde el archivo `.env`.
2. Solicita un token OAuth2 usando `grant_type=client_credentials`.
3. Ejecuta una consulta POST a la API de ePricing con un payload de ejemplo.
4. Obtiene `download_url` desde la respuesta.
5. Descarga el archivo y lo guarda localmente con el nombre extraído desde la URL.

## Payload de ejemplo

La API procesa una solicitud para generar un reporte específico. El sistema valida el tipo de reporte, aplica los filtros y rangos de fechas proporcionados, y retorna una URL firmada de S3 para la descarga.

Actualmente el ejemplo consulta un reporte con esta estructura general:

- `report_type`: `prices`
- `type_date`: `day`
- `dates_ranges`: rango de fechas a consultar
- `filters`: filtros aplicados a la consulta

Ejemplo simplificado:

```json
{
	"report_type": "prices",
	"type_date": "day",
	"dates_ranges": [
		{
			"start_date": "2026-04-01",
			"end_date": "2026-04-30"
		}
	],
	"filters": [
		{
			"key": "chain",
			"values": ["Ahumada", "Cruz Verde"]
		}
	]
}
```

### Configuración de periodos (`type_date` y `dates_ranges`)

El sistema valida la coherencia entre el rango de fechas y el tipo de agrupación solicitado.

#### Formato de fechas

- `start_date` y `end_date` deben enviarse en formato `YYYY-MM-DD`.
- Ejemplo válido: `2026-05-07`.
- Validación: la API rechazará solicitudes donde `start_date` sea posterior a `end_date`.

#### Valores posibles de `type_date`

- `day`: agrupación diaria. Ideal para análisis de variaciones de precio inmediatas.
- `week`: agrupación semanal. Se recomienda que las fechas cubran ciclos de 7 días para reportes consistentes.
- `month`: agrupación mensual. Útil para cierres de mes y análisis de stock de mayor horizonte.

#### Notas sobre rangos y tipos

- `type_date` determina la granularidad temporal del reporte: diario, semanal o mensual.
- `dates_ranges` acepta una lista de intervalos.
- Cada intervalo debe respetar el formato `YYYY-MM-DD`.
- Es responsabilidad del integrador asegurar que la temporalidad solicitada tenga sentido con el análisis esperado.

### Guía detallada de filtros

El parámetro `filters` acepta una lista de objetos. Cada objeto define un criterio de filtrado mediante las propiedades `key` y `values`.

Los campos `filter_type` y `data_type` ya no deben enviarse desde el cliente. El backend los infiere automáticamente en base a la configuración de atributos.

Estructura general:

```json
{
	"key": "chain",
	"values": ["Ahumada", "Cruz Verde"]
}
```

### Filtros de estructura (base)

- `market`: segmento de mercado específico.
	- Ejemplo: `["Aciclovir Jarabe 200 (100)"]`
- `chain`: cadenas de retail o farmacias.
	- Ejemplo: `["Ahumada", "Cruz Verde"]`

### Atributos de producto

Estos filtros permiten granular la búsqueda según características técnicas del catálogo.

- `categoria`: categoría lógica del producto.
	- Ejemplo: `["Medicamentos"]`
- `marca`: marca comercial.
	- Ejemplo: `["Abrilar", "Sophia"]`
- `fabricante`: laboratorio o proveedor.
	- Ejemplo: `["Abbott", "Bayer"]`
- `principio-activo`: compuesto farmacológico.
	- Ejemplo: `["Diclofenaco", "Aciclovir"]`
- `forma-farmaceutica`: presentación del producto.
	- Ejemplo: `["Solución Oftálmica", "Cápsulas"]`
- `concentracion`: valor numérico de potencia.
	- Ejemplo: `["0.1", "800"]`
- `u-concentracion`: unidad de potencia.
	- Ejemplo: `["mg", "%", "mg/ml"]`
- `u-medida`: unidad de empaque o medida.
	- Ejemplo: `["ml", "Ampolla", "Comp"]`
- `codigo-ims`: código de auditoría farmacéutica.
	- Ejemplo: `["0535820"]`
	- `descripcion-producto-homologado`: nombre específico estandarizado.
	- Ejemplo: `["Abrilar Jbe. x 100 ml"]`

En el ejemplo incluido se usa un filtro por cadena (`chain`) con los siguientes valores:

- `Ahumada`
- `Cruz Verde`
- `Salcobrand`
- `Ligafarmacia`
- `Cofar`

El payload puede ajustarse según las necesidades funcionales del cliente y según los filtros o habilitaciones disponibles en la API.

## Resultado esperado

Si la ejecución es exitosa, el script:

- imprime mensajes de progreso en consola,
- obtiene la URL firmada de descarga,
- descarga el archivo,
- guarda el archivo en el mismo directorio desde donde se ejecuta el script.

## Consideraciones de seguridad

- No versionar el archivo `.env` con credenciales reales.
- No exponer `CLIENT_SECRET` en repositorios, correos ni documentación compartida públicamente.
- Mantener los endpoints y credenciales como parámetros externos.
- Si ePricing actualiza endpoints, credenciales o scopes futuros, el cambio debe resolverse en variables de entorno o configuración, evitando modificar la lógica principal salvo que el contrato API cambie.

## Consideraciones de implementación

- Este repositorio es un ejemplo funcional y deliberadamente simple.
- Está pensado como base de referencia para una integración técnica inicial.
- Para un uso productivo, se recomienda que el cliente agregue al menos:
	- manejo explícito de errores y timeouts,
	- logs estructurados,
	- validación de variables requeridas al inicio,
	- parametrización del payload de consulta,
	- tests automatizados,
	- manejo de rutas de salida para archivos descargados.

## Soporte esperado del lado cliente

Para implementar esta integración, el equipo técnico del cliente debe:

1. Mantener actualizado el archivo `.env` con los valores entregados por ePricing.
2. Ejecutar el script en un entorno con acceso a internet y a los endpoints autorizados.
3. Ajustar el payload según el caso de uso requerido.
4. Incorporar este ejemplo dentro de su flujo interno si necesitan automatizar consultas o descargas.

## Nota final

La parametrización del archivo [.env.example](.env.example) debe considerarse obligatoria. Es el mecanismo definido para desacoplar credenciales y endpoints de la lógica del código, facilitando mantención y futuros cambios de configuración.
