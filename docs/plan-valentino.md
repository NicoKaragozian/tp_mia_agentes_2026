# Plan — Valentino · Herramientas obligatorias

> Este es mi plan. El código lo escribo yo en `student_framework/tools/calculadora.py` y
> `student_framework/tools/lector.py`. No toco `mia_agents/**` ni `tests/conformance/**` (FIJOS).

## Objetivo

Implementar dos de las tres herramientas obligatorias de M1, cada una como una **función pura**
con tipos en la firma (`Annotated` + `Field`) y su `ToolSchema` derivado con
`ToolSchema.from_callable`. Mis tools no saben nada del agente → las testeo solas.

## Patrón común (toda tool)

- Firma con `Annotated[tipo, Field(description="...")]` por argumento.
- **Docstring completo** = descripción de la tool para el LLM.
- **Devuelve siempre `str`** (incluidos los mensajes de error, como texto).
- Al final del módulo: `<fn>_schema = ToolSchema.from_callable(<fn>)` y exponer
  `TOOLS = [(<fn>, <fn>_schema)]` para que el registro la descubra (ver Sprint 0).
- **No** armar el JSON Schema a mano: lo deriva `from_callable`.

## Tool 1 — Calculadora (`tools/calculadora.py`)

- **Entrada:** dos operandos numéricos + un operador (string).
- **Operadores:** `+`, `-`, `*`, `/`. (El enunciado pide división; el README menciona `%` →
  lo dejo anotado como discrepancia y, si quiero, agrego `%` como extra.)
- **Salida:** el resultado de la operación, **como string**.
- **Casos de error (devueltos como string, no excepción):**
  - operador no soportado → mensaje claro.
  - división por cero → mensaje claro.
- **Decisión de diseño:** nombres de argumentos claros para que el LLM los complete bien
  (p. ej. `operando_a`, `operando_b`, `operador`); el `schema.name` debe ser inequívoco.

## Tool 2 — Lector de archivos (`tools/lector.py`)

- **Entrada:** una ruta a un archivo.
- **Comportamiento:** leer y devolver el contenido de un archivo **de texto**.
- **Acceso acotado (guardrail):** restringir la lectura a un directorio base permitido (p. ej.
  `data/`) usando rutas resueltas; rechazar intentos de salir de ese directorio (`../`). Esto
  anticipa los guardrails de M3 y suma para la oral. (Si decidimos simplificar, se puede leer una
  ruta directa, pero lo dejo documentado.)
- **Casos de error (como string):**
  - archivo inexistente o no es un archivo regular.
  - contenido no decodificable como texto UTF-8.
  - cualquier otra excepción de IO → mensaje controlado.

## Cómo las testeo solo (sin agente, sin LLM)

`pytest` llamando directamente a las funciones:

- Calculadora: `+ - * /` con casos conocidos; división por cero; operador inválido. Verificar que
  el retorno es `str`.
- Lector: crear un archivo temporal en el directorio permitido y leerlo; ruta inexistente; intento
  de path traversal (`../algo`) → mensaje de acceso denegado; archivo binario → error de texto.
- Verificar que `from_callable` genera un `ToolSchema` con los argumentos esperados (que el
  `parameters` tenga las properties correctas).

## Coordinación / no-bloqueo

- Mis dos archivos son independientes del bucle de Nicolás y del registro de Federico.
- Solo dependo de que exista el stub de cada archivo tras el Sprint 0 (para que los imports
  resuelvan). Puedo empezar a escribir y testear apenas estén los stubs.

## Definition of Done

- [ ] Calculadora y lector implementadas como funciones puras que devuelven `str`.
- [ ] Cada módulo expone su `_schema` y su `TOOLS`.
- [ ] Mis tests unitarios pasan (incluye casos de error y el path traversal del lector).
- [ ] Las tools quedan descubiertas por el registro (aparecen al construir el agente).
- [ ] No toqué archivos FIJOS.
