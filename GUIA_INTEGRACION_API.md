# Guía de integración API ePricing

## 1. Objetivo

Esta guía está orientada al equipo técnico del cliente que necesite integrarse con la API interna de ePricing para generar reportes y descargar sus resultados mediante una URL firmada.

La API permite:

- autenticarse vía OAuth2 usando `client_credentials`,
- solicitar la generación de un reporte,
- aplicar filtros y rangos de fechas,
- obtener una `download_url` para descargar el archivo resultante.

## 2. Alcance

Esta guía cubre el flujo de integración disponible en este repositorio:

1. obtención de token,
2. invocación del endpoint de descarga,
3. descarga del archivo retornado por la API.

La referencia técnica navegable se encuentra en la documentación OpenAPI publicada por ePricing:

- QA / Swagger: https://apiv2qa.epricing.cl/docs#/Downloads/download_v2_download_post
- OpenAPI JSON: https://apiv2qa.epricing.cl/openapi.json

## 3. Ambientes

### Producción

- Endpoint productivo de descarga: `https://apiv2.epricing.cl/download`
- Endpoint productivo OAuth: `https://oauth.epricing.cl/oauth2/token`

## 4. Requisitos previos

Para implementar esta integración por ejemplo con Python, el cliente debe contar con:

- Python 3.12 o superior,
- credenciales válidas de acceso,
- conectividad hacia los endpoints de autenticación y API,
- un mecanismo seguro para administrar variables de entorno.

## 5. Estructura del proyecto de ejemplo

- [epricing_api.py](epricing_api.py): script de referencia para autenticación, consulta y descarga.
- [.env.example](.env.example): plantilla de variables de entorno requeridas.
- [README.md](README.md): documento base del ejemplo.

## 6. Variables de entorno

Las siguientes variables deben mantenerse parametrizadas:

- `CLIENT_ID`: identificador del cliente OAuth.
- `CLIENT_SECRET`: secreto del cliente OAuth.
- `EPRICING_OAUTH_URL`: endpoint de obtención de token.
- `EPRICING_API_URL`: endpoint principal para solicitar la generación del reporte.

Ejemplo de archivo `.env`:

```env
CLIENT_ID=valor_entregado_por_epricing
CLIENT_SECRET=valor_entregado_por_epricing
EPRICING_OAUTH_URL=https://...
EPRICING_API_URL=https://...
```

> Importante: no hardcodear credenciales ni endpoints en el código fuente. Se deben administrar de manera segura.

## 7. Autenticación

La integración implementada en [epricing_api.py](epricing_api.py) utiliza OAuth2 con `grant_type=client_credentials`.

### Endpoint OAuth productivo

- `https://oauth.epricing.cl/oauth2/token`

### Solicitud de token

La aplicación envía un `POST` al endpoint configurado en `EPRICING_OAUTH_URL` con los siguientes campos:

- `grant_type=client_credentials`
- `client_id`
- `client_secret`

### Uso del token

Una vez obtenido el `access_token`, este se envía en el header:

```http
Authorization: Bearer <access_token>
```

### Vigencia del token

- El `access_token` emitido tiene una vigencia de `1 hora`.
- `client_id` y `client_secret` son credenciales fijas entregadas por ePricing.

### Respuesta observada del endpoint OAuth

Ejemplo de respuesta:

```json
{
  "access_token": "eyJraWQiOiIzU.....",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

Campos observados:

- `access_token`: token JWT utilizado para autenticación contra la API.
- `expires_in`: duración del token en segundos. Valor observado: `3600`.
- `token_type`: tipo de token. Valor observado: `Bearer`.


## 8. Endpoint disponible

### POST `/download`

**Resumen:** generar URL de descarga de reportes.

**URL productiva:** `https://apiv2.epricing.cl/download`

**Descripción funcional:**
Procesa una solicitud para generar un reporte específico. El sistema valida el tipo de reporte, aplica los filtros y rangos de fechas proporcionados, y retorna una URL firmada de S3 para la descarga.

## 9. Request body

De acuerdo con el OpenAPI disponible, el esquema de request corresponde a `DownloadRequest`.

### Campos principales

- `report_type`: tipo de reporte.
- `filters`: lista de filtros aplicados a la consulta.
- `dates_ranges`: lista de rangos de fechas.
- `type_date`: granularidad temporal.
- `str_as_formula`: bandera booleana disponible en el esquema OpenAPI.

### Valores identificados en OpenAPI

#### `report_type`
Valor permitido: `prices`

#### `type_date`
Valores permitidos según OpenAPI:

- `day`
- `week`
- `month`

#### `data_type`
Valores permitidos según OpenAPI:

- `STRING`
- `NUMERIC`
- `BOOLEAN`

#### `filter_type`
Valores identificados en OpenAPI:

- `product_column`
- `product_attribute`
- `chain_filter`
- `market_filter`

> Nota: `product_column` aparece definido en OpenAPI y debe considerarse parte del contrato técnico. Sin embargo, las claves funcionales específicas habilitadas para este tipo de filtro deben confirmarse antes de documentarlas en detalle para el cliente.

## 10. Configuración de periodos

El sistema valida la coherencia entre el rango de fechas y el tipo de agrupación solicitado.

### Formato de fechas

- `start_date` y `end_date` deben enviarse en formato `YYYY-MM-DD`.
- Ejemplo: `2026-05-07`.
- La API rechazará solicitudes donde `start_date` sea posterior a `end_date`.

### Temporalidad (`type_date`)

- `day`: agrupación diaria. Ideal para análisis de variaciones inmediatas.
- `week`: agrupación semanal. Se recomienda usar ciclos consistentes de 7 días.
- `month`: agrupación mensual. Útil para análisis de largo plazo o cierres mensuales.

### Notas

- `dates_ranges` acepta una lista de intervalos.
- Cada intervalo debe mantener formato `YYYY-MM-DD`.
- La temporalidad debe ser coherente con el objetivo analítico del reporte.
- El volumen del resultado depende de la combinación de fechas y filtros solicitados.
- Como recomendación operativa, no se debe sobrepasar `1 mes` de historia por consulta.

## 11. Filtros soportados

El parámetro `filters` acepta una lista de objetos con esta estructura:

```json
{
  "key": "chain",
  "data_type": "STRING",
  "filter_type": "chain_filter",
  "values": ["Ahumada", "Cruz Verde"]
}
```

### 11.1 Filtros de estructura

- `market` con `filter_type: market_filter`
  - Descripción: segmento de mercado específico.
  - Ejemplo: `["Aciclovir Jarabe 200 (100)"]`

- `chain` con `filter_type: chain_filter`
  - Descripción: cadenas de retail o farmacias.
  - Ejemplo: `["Ahumada", "Cruz Verde"]`

### 11.2 Atributos de producto

Estos filtros usan `filter_type: product_attribute`.

- `categoria`
  - Ejemplo: `["Medicamentos"]`
- `marca`
  - Ejemplo: `["Abrilar", "Sophia"]`
- `fabricante`
  - Ejemplo: `["Abbott", "Bayer"]`
- `principio-activo`
  - Ejemplo: `["Diclofenaco", "Aciclovir"]`
- `forma-farmaceutica`
  - Ejemplo: `["Solución Oftálmica", "Cápsulas"]`
- `concentracion`
  - Ejemplo: `["0.1", "800"]`
- `u-concentracion`
  - Ejemplo: `["mg", "%", "mg/ml"]`
- `u-medida`
  - Ejemplo: `["ml", "Ampolla", "Comp"]`
- `codigo-ims`
  - Ejemplo: `["0535820"]`
- `descripcion-producto-homologado`
  - Ejemplo: `["Abrilar Jbe. x 100 ml"]`

### 11.3 Filtros `product_column`

El tipo `product_column` aparece en el contrato OpenAPI como un `filter_type` válido.

- Debe considerarse soportado a nivel de contrato técnico.
- Claves permitidas actualmente:
  - `categoria`
    - Ejemplo: `["Medicamentos"]`
  - `marca`
    - Ejemplo: `["Abrilar", "Sophia"]`
  - `fabricante`
    - Ejemplo: `["Abbott", "Bayer"]`
  - `principio-activo`
    - Ejemplo: `["Diclofenaco", "Aciclovir"]`
  - `forma-farmaceutica`
    - Ejemplo: `["Solución Oftálmica", "Cápsulas"]`
  - `concentracion`
    - Ejemplo: `["0.1", "800"]`
  - `u-concentracion`
    - Ejemplo: `["mg", "%", "mg/ml"]`
  - `u-medida`
    - Ejemplo: `["ml", "Ampolla", "Comp"]`
  - `codigo-ims`
    - Ejemplo: `["0535820"]`
  - `descripcion-producto-homologado`
    - Ejemplo: `["Abrilar Jbe. x 100 ml"]`

## 12. Ejemplo de request

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
      "data_type": "STRING",
      "filter_type": "chain_filter",
      "values": ["Ahumada", "Cruz Verde", "Salcobrand", "Ligafarmacia", "Cofar"]
    }
  ]
}
```

## 13. Respuestas esperadas

Según OpenAPI, el endpoint documenta los siguientes códigos:

- `200`: URL de descarga generada exitosamente.
- `400`: tipo de reporte no soportado o error en los filtros.
- `404`: no se encontraron datos para los filtros dados.
- `429`: rate limit excedido para el cliente o la credencial utilizada.
- `422`: error de validación del request.
- `500`: error interno del servidor durante la generación.

### Respuesta `429` - Rate limit

El código `429` indica que la aplicación superó el límite de solicitudes permitido en una ventana de tiempo determinada.

Consideraciones operativas:

- este error está asociado a políticas de rate limiting,
- el cliente debe evitar reintentos inmediatos en bucle,
- se recomienda implementar reintentos con espera progresiva (`backoff`),
- si el patrón de uso es recurrente, se debe revisar el volumen de invocaciones y su distribución temporal.

### Respuesta exitosa

La respuesta exitosa incluye el campo:

- `download_url`: URL firmada para descargar el archivo.

Consideraciones confirmadas:

- el archivo descargado es `CSV`,
- la `download_url` tiene una vigencia de `1 día`.

Ejemplo esperado:

```json
{
  "download_url": "https://..."
}
```

**Pendiente de confirmación:**
- no existe un tamaño máximo fijo documentado; el volumen depende de la cantidad de filtros y fechas consultadas.
- como referencia operativa, se recomienda no sobrepasar `1 mes` de historia por consulta.

## 14. Flujo de integración recomendado

1. Cargar variables de entorno.
2. Solicitar token OAuth.
3. Construir el payload de consulta.
4. Ejecutar `POST /download` con header `Authorization: Bearer <token>`.
5. Leer `download_url` desde la respuesta.
6. Descargar el archivo usando la URL firmada.
7. Guardar el archivo en una ruta controlada por la aplicación del cliente.

## 15. Ejemplo Python incluido

El archivo [epricing_api.py](epricing_api.py) implementa el flujo mínimo de referencia:

1. obtiene token,
2. invoca la API,
3. toma `download_url`,
4. descarga el archivo,
5. guarda el resultado localmente.

## 16. Consideraciones de seguridad

- No exponer `CLIENT_SECRET`.
- No versionar archivos `.env` con secretos reales.
- Parametrizar endpoints y credenciales.
- Proteger logs para no registrar tokens ni secretos.

## 17. Recomendaciones para productivización

Si el cliente llevará esta integración a producción, se recomienda agregar:

- manejo de timeouts,
- reintentos controlados,
- logs estructurados,
- parametrización del payload,
- almacenamiento de archivos en rutas definidas,
- monitoreo y alertas,
- pruebas automatizadas.

## 18. Soporte

Para consultas técnicas relacionadas con la integración:

- `contacto@epricing.cl`

## 19. Versionado del documento

### Versión actual

- `1.0`

### Control de cambios

| Versión | Fecha | Descripción |
| :--- | :--- | :--- |
| 1.0 | 2026-05-13 | Primera versión formal de la guía de integración para cliente. |
