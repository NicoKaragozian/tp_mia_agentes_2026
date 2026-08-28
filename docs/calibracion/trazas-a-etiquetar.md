# Calibración del juez — cuadernillo de etiquetado

Cada bloque es **el texto exacto que recibió el juez** para puntuar esa
traza: ni más ni menos información. Puntuá vos con la misma rúbrica, sin
mirar `claves.json` (ahí están las notas del juez, y verlas antes arruina la
medición).

Cada anotador trabaja **por separado** y sin comentar sus notas con los
demás hasta que estén las tres planillas.

## Rúbrica (idéntica a la del juez)

Puntuás la **conducta observable, no el resultado**. Un agente puede fallar
y aun así haber explorado con criterio, y puede acertar habiendo dado
muchas vueltas.

| Dimensión | 1 | 5 |
| :---- | :---- | :---- |
| `coherencia_plan` | acciones sin relación con el objetivo | plan claro y progresivo |
| `recuperacion_errores` | repite la acción fallida sin cambiar nada | lee el error y corrige |
| `exploracion_eficiente` | repite acciones ya hechas | cada acción aporta información nueva |

Los valores intermedios (2, 3, 4) son válidos y esperables.

## Cómo cargar las notas

Copiá `etiquetas-plantilla.csv` a `etiquetas-<tunombre>.csv` y completá las
tres columnas de cada fila, poniendo tu nombre en `anotador`. Cuando estén
las tres planillas:

```
python eval/calibracion.py acuerdo
```


---

## T01

```
Escenario: office-sequence (dificultad hard)
Objetivo alcanzado: no — faltan condiciones: puerta principal está cerrada
Llamadas óptimas conocidas: 13; realizadas: 101

Secuencia de acciones:
    0. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
    1. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio amplio con cajones. Están todos vacíos salvo por clips y papel en blanco.
Está vacío
    2. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
    3. look({}) [ok] Estás en Corredor.
Un corredor central que distribuye hacia la oficina (oeste), el archivo (norte) y el depósi
    4. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
    5. look({}) [ok] Estás en Archivo.
Una sala con armarios de expedientes y una caja fuerte empotrada en la pared.
Ves:
  - caja 
    6. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Una caja fuerte empotrada con una cerradura de llave plana. Cerrada.
Está cerrado con llave. No p
    7. go({"direction": "este"}) [ERROR] Error: no hay salida 'este' desde aquí. Salidas disponibles: sur.
    8. go({"direction": "oeste"}) [ERROR] Error: no hay salida 'oeste' desde aquí. Salidas disponibles: sur.
    9. examine({"target": "escritorio"}) [ERROR] Error: no ves ningún 'escritorio' aquí.
   10. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Una caja fuerte empotrada con una cerradura de llave plana. Cerrada.
Está cerrado con llave. No p
   11. look({}) [ok] Estás en Archivo.
Una sala con armarios de expedientes y una caja fuerte empotrada en la pared.
Ves:
  - caja 
   12. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   13. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Depósito.
   14. look({}) [ok] Estás en Depósito.
Un cuarto de limpieza con estanterías metálicas y un cajón etiquetado 'LLAVES'.
Ves:
  - ca
   15. examine({"target": "cajon_llaves"}) [ok] cajón de llaves: Un cajón metálico etiquetado 'LLAVES'. Dentro cuelga una sola llave pequeña.
Contiene:
  - ll
   16. take({"item": "llave_caja"}) [ok] Tomas llave de la caja fuerte.
   17. go({"direction": "sur"}) [ERROR] Error: no hay salida 'sur' desde aquí. Salidas disponibles: oeste.
   18. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Corredor.
   19. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   20. use({"item": "llave_caja", "target": "caja_fuerte"}) [ok] Usas llave de la caja fuerte con caja fuerte. Se abre.
   21. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Una caja fuerte empotrada con una cerradura de llave plana. Cerrada.
Contiene:
  - documento conf
   22. take({"item": "llave_maestra"}) [ok] Tomas llave maestra.
   23. take({"item": "documento_confidencial"}) [ok] Tomas documento confidencial.
   24. use({"item": "llave_maestra", "target": "puerta_principal"}) [ERROR] Error: no ves ningún 'puerta_principal' aquí.
   25. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   26. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   27. use({"item": "llave_maestra", "target": "puerta_principal"}) [ERROR] Error: no ves ningún 'puerta_principal' aquí.
   28. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   29. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   30. use({"item": "llave_maestra", "target": "puerta_principal"}) [ERROR] Error: no ves ningún 'puerta_principal' aquí.
   31. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   32. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   33. use({"item": "llave_maestra", "target": "puerta_principal"}) [ERROR] Error: no ves ningún 'puerta_principal' aquí.
   34. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   35. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   36. use({"item": "llave_maestra", "target": "puerta_principal"}) [ERROR] Error: no ves ningún 'puerta_principal' aquí.
   37. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   38. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   39. use({"item": "llave_maestra", "target": "puerta_principal"}) [ERROR] Error: no ves ningún 'puerta_principal' aquí.
  … 61 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T02

```
Escenario: extreme-archive (dificultad extreme)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 4; realizadas: 2

Secuencia de acciones:
    0. examine({"target": "estantería"}) [ERROR] Error: no existe ningún objeto con id 'estantería'.
    1. examine({"target": "expediente"}) [ERROR] Error: no existe ningún objeto con id 'expediente'.
```


---

## T03

```
Escenario: library-search (dificultad hard)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 7; realizadas: 16

Secuencia de acciones:
    0. look({}) [ok] Estás en Biblioteca del archivero.
Una sala rectangular con olor a papel viejo. Al norte, una estantería alta 
    1. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
    2. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
    3. examine({"target": "libro_geometria"}) [ok] Elementos de geometría aplicada: Encuadernación rígida de cartón forrado en tela negra, lomo reforzado. Propos
    4. examine({"target": "libro_alquimia"}) [ok] Notas sobre la transmutación de los metales: Manuscrito en cuarto, encuadernación de cuero rojo desgastado, si
    5. examine({"target": "libro_filosofia"}) [ok] Diálogos sobre la naturaleza del juicio: Volumen de pequeño tamaño, encuadernado en piel verde con cantos dora
    6. examine({"target": "libro_historia"}) [ok] Anales del reino, década quinta: Tomo en folio, encuadernación de pergamino crudo, con cintas de cierre. Año 1
    7. examine({"target": "libro_jurisprudencia"}) [ok] Recopilación de sentencias del tribunal supremo: Tomo grueso encuadernado en piel parda, con el escudo real es
    8. examine({"target": "libro_recetario"}) [ok] Recetario del cocinero mayor: Manuscrito en cuarto, tapas blandas de pergamino, manchado de aceite. Receta del
    9. examine({"target": "libro_genealogia"}) [ok] Genealogía de la casa de Andrade: Tomo grande encuadernado en piel azul, con grabados heráldicos en el lomo. C
   10. examine({"target": "libro_sermones"}) [ok] Colección de sermones dominicales: Tomo encuadernado en piel negra con cantos rojos, muy usado. Sermón XXI, pa
   11. take({"item": "llave_caja"}) [ok] Tomas llave de la caja.
   12. use({"item": "llave_caja", "target": "caja_fuerte"}) [ok] Usas llave de la caja con caja fuerte. Se abre.
   13. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   14. take({"item": "llave_grabada"}) [ok] Tomas llave grabada.
   15. use({"item": "llave_grabada", "target": "puerta_principal"}) [ok] Usas llave grabada con puerta principal. Se abre.
```


---

## T04

```
Escenario: color-locks (dificultad medium)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 11; realizadas: 100

Secuencia de acciones:
    0. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
    1. examine({"target": "cofre_plata"}) [ok] cofre plateado: Un cofre pequeño con tachuelas plateadas y una cerradura del mismo color. Encaja con una llave
    2. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
    3. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
    4. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
    5. take({"item": "trapo_viejo"}) [ok] Tomas trapo viejo.
    6. examine({"target": "cofre_plateado"}) [ERROR] Error: no existe ningún objeto con id 'cofre_plateado'.
    7. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
    8. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
    9. examine({"target": "cofre_plateado"}) [ERROR] Error: no existe ningún objeto con id 'cofre_plateado'.
   10. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
   11. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
   12. examine({"target": "cofre_plateado"}) [ERROR] Error: no existe ningún objeto con id 'cofre_plateado'.
   13. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
   14. examine({"target": "cofre_plata"}) [ok] cofre plateado: Un cofre pequeño con tachuelas plateadas y una cerradura del mismo color. Encaja con una llave
   15. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   16. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   17. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
   18. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   19. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   20. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
   21. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   22. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   23. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
   24. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   25. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   26. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
   27. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   28. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   29. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
   30. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   31. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   32. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
   33. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   34. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   35. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
   36. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   37. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   38. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
   39. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
  … 60 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T05

```
Escenario: apartment-keys (dificultad medium)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 7; realizadas: 11

Secuencia de acciones:
    0. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    1. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Pasillo.
    2. look({}) [ok] Estás en Pasillo.
Un pasillo en penumbra con cuadros torcidos. Conecta el recibidor al sur con la cocina al es
    3. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Cocina.
    4. look({}) [ok] Estás en Cocina.
Una cocina pequeña con azulejos blancos. Hay una mesada con un cajón cerrado y olor a café fr
    5. examine({"target": "cajon"}) [ok] cajón de la cocina: Un cajón de madera bajo la mesada. Se abre con un tirón y dentro hay cubiertos sueltos y a
    6. take({"item": "llave_oro"}) [ok] Tomas llave dorada.
    7. go({"direction": "sur"}) [ERROR] Error: no hay salida 'sur' desde aquí. Salidas disponibles: oeste.
    8. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Pasillo.
    9. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Recibidor.
   10. use({"item": "llave_oro", "target": "puerta_principal"}) [ok] Usas llave dorada con puerta principal. Se abre.
```


---

## T06

```
Escenario: vault-combination (dificultad extreme)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 21; realizadas: 25

Secuencia de acciones:
    0. look({}) [ok] Estás en Vestíbulo.
Un vestíbulo de hormigón con un panel de seguridad junto a la puerta principal. El panel t
    1. examine({"obj": "puerta_principal"}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): obj. Falta(n) el/los requerido(s): targ
    2. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta blindada controlada por un panel de tres ranuras. Solo abre cuando se colocan los
    3. look({}) [ok] Estás en Vestíbulo.
Un vestíbulo de hormigón con un panel de seguridad junto a la puerta principal. El panel t
    4. look({"dir": "norte"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
    5. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
    6. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta blindada controlada por un panel de tres ranuras. Solo abre cuando se colocan los
    7. look({"dir": "sur"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
    8. look({"dir": "norte"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
    9. look({"dir": "este"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   10. look({"dir": "oeste"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   11. look({"dir": "sur"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   12. look({"dir": "norte"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   13. look({"dir": "este"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   14. look({"dir": "oeste"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   15. look({"dir": "sur"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   16. look({"dir": "norte"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   17. look({"dir": "este"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   18. look({"dir": "oeste"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   19. look({"dir": "sur"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   20. look({"dir": "norte"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): dir. Parámetros válidos: (sin parámetros).
   21. look({}) [ok] Estás en Vestíbulo.
Un vestíbulo de hormigón con un panel de seguridad junto a la puerta principal. El panel t
   22. examine({"id": "puerta_principal"}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): id. Falta(n) el/los requerido(s): targe
   23. examine({"id": "puerta_principal", "target": "puerta_principal"}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): id. Parámetros válidos: target.
   24. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta blindada controlada por un panel de tres ranuras. Solo abre cuando se colocan los
```


---

## T07

```
Escenario: color-locks (dificultad medium)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 11; realizadas: 103

Secuencia de acciones:
    0. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
    1. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
    2. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
    3. examine({"target": "cofre_plata"}) [ok] cofre plateado: Un cofre pequeño con tachuelas plateadas y una cerradura del mismo color. Encaja con una llave
    4. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
    5. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
    6. take({"item": "trapo_viejo"}) [ok] Tomas trapo viejo.
    7. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
    8. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta gruesa de roble con marco metálico y una cerradura dorada considerable.
Estado: c
    9. examine({"target": "trapo_viejo"}) [ok] trapo viejo: Un trapo gris y manchado de aceite. Inservible.
   10. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   11. examine({"target": "repisa"}) [ERROR] Error: no existe ningún objeto con id 'repisa'.
   12. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   13. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta gruesa de roble con marco metálico y una cerradura dorada considerable.
Estado: c
   14. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   15. examine({"target": "trapo_viejo"}) [ok] trapo viejo: Un trapo gris y manchado de aceite. Inservible.
   16. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   17. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta gruesa de roble con marco metálico y una cerradura dorada considerable.
Estado: c
   18. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   19. examine({"target": "trapo_viejo"}) [ok] trapo viejo: Un trapo gris y manchado de aceite. Inservible.
   20. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   21. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta gruesa de roble con marco metálico y una cerradura dorada considerable.
Estado: c
   22. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   23. examine({"target": "trapo_viejo"}) [ok] trapo viejo: Un trapo gris y manchado de aceite. Inservible.
   24. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   25. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta gruesa de roble con marco metálico y una cerradura dorada considerable.
Estado: c
   26. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   27. examine({"target": "trapo_viejo"}) [ok] trapo viejo: Un trapo gris y manchado de aceite. Inservible.
   28. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   29. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta gruesa de roble con marco metálico y una cerradura dorada considerable.
Estado: c
   30. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   31. examine({"target": "trapo_viejo"}) [ok] trapo viejo: Un trapo gris y manchado de aceite. Inservible.
   32. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   33. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta gruesa de roble con marco metálico y una cerradura dorada considerable.
Estado: c
   34. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   35. examine({"target": "trapo_viejo"}) [ok] trapo viejo: Un trapo gris y manchado de aceite. Inservible.
   36. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   37. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta gruesa de roble con marco metálico y una cerradura dorada considerable.
Estado: c
   38. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
   39. examine({"target": "trapo_viejo"}) [ok] trapo viejo: Un trapo gris y manchado de aceite. Inservible.
  … 63 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T08

```
Escenario: color-locks (dificultad medium)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 11; realizadas: 30

Secuencia de acciones:
    0. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
    1. examine({"target": "cofre_plata"}) [ok] cofre plateado: Un cofre pequeño con tachuelas plateadas y una cerradura del mismo color. Encaja con una llave
    2. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
    3. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
    4. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
    5. take({"item": "trapo_viejo"}) [ok] Tomas trapo viejo.
    6. examine({"target": "cofre_plata"}) [ok] cofre plateado: Un cofre pequeño con tachuelas plateadas y una cerradura del mismo color. Encaja con una llave
    7. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
    8. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
    9. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
   10. use({"item": "trapo_viejo", "target": "cofre_plata"}) [ok] Intentas usar trapo viejo con cofre plateado, pero no encaja.
   11. use({"item": "trapo_viejo", "target": "cofre_rojo"}) [ok] Intentas usar trapo viejo con cofre rojo, pero no encaja.
   12. use({"item": "trapo_viejo", "target": "cofre_verde"}) [ok] Intentas usar trapo viejo con cofre verde, pero no encaja.
   13. use({"item": "trapo_viejo", "target": "puerta_principal"}) [ok] Intentas usar trapo viejo con puerta principal, pero no encaja.
   14. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
   15. use({"item": "llave_plata", "target": "cofre_plata"}) [ERROR] Error: no llevas ningún 'llave_plata'.
   16. take({"item": "llave_plata"}) [ok] Tomas llave plateada.
   17. use({"item": "llave_plata", "target": "cofre_plata"}) [ok] Usas llave plateada con cofre plateado. Se abre.
   18. examine({"target": "cofre_plata"}) [ok] cofre plateado: Un cofre pequeño con tachuelas plateadas y una cerradura del mismo color. Encaja con una llave
   19. use({"item": "llave_roja", "target": "cofre_rojo"}) [ERROR] Error: no llevas ningún 'llave_roja'.
   20. take({"item": "llave_roja"}) [ok] Tomas llave roja.
   21. use({"item": "llave_roja", "target": "cofre_rojo"}) [ok] Usas llave roja con cofre rojo. Se abre.
   22. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   23. use({"item": "llave_verde", "target": "cofre_verde"}) [ERROR] Error: no llevas ningún 'llave_verde'.
   24. take({"item": "llave_verde"}) [ok] Tomas llave verde.
   25. use({"item": "llave_verde", "target": "cofre_verde"}) [ok] Usas llave verde con cofre verde. Se abre.
   26. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   27. use({"item": "llave_oro", "target": "puerta_principal"}) [ERROR] Error: no llevas ningún 'llave_oro'.
   28. take({"item": "llave_oro"}) [ok] Tomas llave dorada.
   29. use({"item": "llave_oro", "target": "puerta_principal"}) [ok] Usas llave dorada con puerta principal. Se abre.
```


---

## T09

```
Escenario: apartment-keys (dificultad medium)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 7; realizadas: 28

Secuencia de acciones:
    0. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    1. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta de metal con una cerradura simple. Necesita una llave para abrirse.
Estado: cerra
    2. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    3. examine({"target": "alfombra"}) [ERROR] Error: no existe ningún objeto con id 'alfombra'.
    4. take({"item": "llave"}) [ERROR] Error: no existe ningún objeto con id 'llave'.
    5. go({"direction": "pasillo"}) [ERROR] Error: no hay salida 'pasillo' desde aquí. Salidas disponibles: norte.
    6. use({"item": "llave", "target": "puerta_principal"}) [ERROR] Error: no llevas ningún 'llave'.
    7. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    8. examine({"text": "La sala actual es el recibidor. Hay una puerta principal cerrada con llave y un pasillo que se interna en el apartamento. El inventario está vacío.", "type": "text"}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): text, type. Falta(n) el/los requerido(s
    9. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta de metal con una cerradura simple. Necesita una llave para abrirse.
Estado: cerra
   10. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   11. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
   12. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   13. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta de metal con una cerradura simple. Necesita una llave para abrirse.
Estado: cerra
   14. look({"direction": "norte"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): direction. Parámetros válidos: (sin paráme
   15. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   16. examine({"target": "perchero"}) [ERROR] Error: no existe ningún objeto con id 'perchero'.
   17. examine({"target": "espejo"}) [ERROR] Error: no existe ningún objeto con id 'espejo'.
   18. examine({"target": "cerradura simple"}) [ERROR] Error: no existe ningún objeto con id 'cerradura simple'.
   19. examine({"target": "puerta principal"}) [ERROR] Error: no existe ningún objeto con id 'puerta principal'.
   20. look({"target": "pasillo"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): target. Parámetros válidos: (sin parámetro
   21. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   22. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta de metal con una cerradura simple. Necesita una llave para abrirse.
Estado: cerra
   23. look({"target": "pasillo"}) [ERROR] Argumentos inválidos para 'look'. No existe(n) el/los parámetro(s): target. Parámetros válidos: (sin parámetro
   24. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   25. examine({"target": "perchero"}) [ERROR] Error: no existe ningún objeto con id 'perchero'.
   26. examine({"target": "espejo"}) [ERROR] Error: no existe ningún objeto con id 'espejo'.
   27. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
```


---

## T10

```
Escenario: color-locks (dificultad medium)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 11; realizadas: 102

Secuencia de acciones:
    0. examine({"target": "llave"}) [ERROR] Error: no existe ningún objeto con id 'llave'.
    1. examine({"target": "cofre_plateado"}) [ERROR] Error: no existe ningún objeto con id 'cofre_plateado'.
    2. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
    3. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
    4. examine({"target": "cofre_azul"}) [ok] cofre azul: Un cofre pintado de azul desconchado. Sorprendentemente, no tiene cerradura: las bisagras se abren
    5. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
    6. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
    7. take({"item": "llave_plateada"}) [ERROR] Error: no existe ningún objeto con id 'llave_plateada'.
    8. take({"item": "llave"}) [ERROR] Error: no existe ningún objeto con id 'llave'.
    9. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   10. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   11. use({"item": "llave", "target": "cofre_rojo"}) [ERROR] Error: no llevas ningún 'llave'.
   12. take({"item": "llave"}) [ERROR] Error: no existe ningún objeto con id 'llave'.
   13. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   14. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   15. use({"item": "llave", "target": "cofre_rojo"}) [ERROR] Error: no llevas ningún 'llave'.
   16. take({"item": "llave"}) [ERROR] Error: no existe ningún objeto con id 'llave'.
   17. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   18. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   19. use({"item": "llave", "target": "cofre_rojo"}) [ERROR] Error: no llevas ningún 'llave'.
   20. take({"item": "llave"}) [ERROR] Error: no existe ningún objeto con id 'llave'.
   21. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   22. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   23. use({"item": "llave", "target": "cofre_rojo"}) [ERROR] Error: no llevas ningún 'llave'.
   24. take({"item": "llave"}) [ERROR] Error: no existe ningún objeto con id 'llave'.
   25. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   26. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   27. use({"item": "llave", "target": "cofre_rojo"}) [ERROR] Error: no llevas ningún 'llave'.
   28. take({"item": "llave"}) [ERROR] Error: no existe ningún objeto con id 'llave'.
   29. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   30. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   31. use({"item": "llave", "target": "cofre_rojo"}) [ERROR] Error: no llevas ningún 'llave'.
   32. take({"item": "llave"}) [ERROR] Error: no existe ningún objeto con id 'llave'.
   33. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   34. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   35. use({"item": "llave", "target": "cofre_rojo"}) [ERROR] Error: no llevas ningún 'llave'.
   36. take({"item": "llave"}) [ERROR] Error: no existe ningún objeto con id 'llave'.
   37. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   38. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   39. use({"item": "llave", "target": "cofre_rojo"}) [ERROR] Error: no llevas ningún 'llave'.
  … 62 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T11

```
Escenario: library-search (dificultad hard)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 7; realizadas: 17

Secuencia de acciones:
    0. look({}) [ok] Estás en Biblioteca del archivero.
Una sala rectangular con olor a papel viejo. Al norte, una estantería alta 
    1. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
    2. examine({"target": "libro_geometria"}) [ok] Elementos de geometría aplicada: Encuadernación rígida de cartón forrado en tela negra, lomo reforzado. Propos
    3. examine({"target": "libro_alquimia"}) [ok] Notas sobre la transmutación de los metales: Manuscrito en cuarto, encuadernación de cuero rojo desgastado, si
    4. examine({"target": "libro_filosofia"}) [ok] Diálogos sobre la naturaleza del juicio: Volumen de pequeño tamaño, encuadernado en piel verde con cantos dora
    5. examine({"target": "libro_historia"}) [ok] Anales del reino, década quinta: Tomo en folio, encuadernación de pergamino crudo, con cintas de cierre. Año 1
    6. examine({"target": "libro_jurisprudencia"}) [ok] Recopilación de sentencias del tribunal supremo: Tomo grueso encuadernado en piel parda, con el escudo real es
    7. examine({"target": "libro_recetario"}) [ok] Recetario del cocinero mayor: Manuscrito en cuarto, tapas blandas de pergamino, manchado de aceite. Receta del
    8. examine({"target": "libro_genealogia"}) [ok] Genealogía de la casa de Andrade: Tomo grande encuadernado en piel azul, con grabados heráldicos en el lomo. C
    9. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   10. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
   11. examine({"target": "libro_sermones"}) [ok] Colección de sermones dominicales: Tomo encuadernado en piel negra con cantos rojos, muy usado. Sermón XXI, pa
   12. take({"item": "llave_caja"}) [ok] Tomas llave de la caja.
   13. use({"item": "llave_caja", "target": "caja_fuerte"}) [ok] Usas llave de la caja con caja fuerte. Se abre.
   14. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   15. take({"item": "llave_grabada"}) [ok] Tomas llave grabada.
   16. use({"item": "llave_grabada", "target": "puerta_principal"}) [ok] Usas llave grabada con puerta principal. Se abre.
```


---

## T12

```
Escenario: library-search (dificultad hard)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 7; realizadas: 100

Secuencia de acciones:
    0. look({}) [ok] Estás en Biblioteca del archivero.
Una sala rectangular con olor a papel viejo. Al norte, una estantería alta 
    1. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
    2. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
    3. examine({"target": "libro_geometria"}) [ok] Elementos de geometría aplicada: Encuadernación rígida de cartón forrado en tela negra, lomo reforzado. Propos
    4. examine({"target": "libro_alquimia"}) [ok] Notas sobre la transmutación de los metales: Manuscrito en cuarto, encuadernación de cuero rojo desgastado, si
    5. examine({"target": "libro_filosofia"}) [ok] Diálogos sobre la naturaleza del juicio: Volumen de pequeño tamaño, encuadernado en piel verde con cantos dora
    6. examine({"target": "libro_historia"}) [ok] Anales del reino, década quinta: Tomo en folio, encuadernación de pergamino crudo, con cintas de cierre. Año 1
    7. examine({"target": "libro_medicina"}) [ERROR] Error: no existe ningún objeto con id 'libro_medicina'.
    8. examine({"target": "libro_alquimia"}) [ok] Notas sobre la transmutación de los metales: Manuscrito en cuarto, encuadernación de cuero rojo desgastado, si
    9. examine({"target": "libro_filosofia"}) [ok] Diálogos sobre la naturaleza del juicio: Volumen de pequeño tamaño, encuadernado en piel verde con cantos dora
   10. examine({"target": "libro_historia"}) [ok] Anales del reino, década quinta: Tomo en folio, encuadernación de pergamino crudo, con cintas de cierre. Año 1
   11. examine({"target": "estanteria"}) [ERROR] Error: no existe ningún objeto con id 'estanteria'.
   12. examine({"target": "estanteria_norte"}) [ERROR] Error: no existe ningún objeto con id 'estanteria_norte'.
   13. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
   14. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   15. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
   16. examine({"target": "libro_geometria"}) [ok] Elementos de geometría aplicada: Encuadernación rígida de cartón forrado en tela negra, lomo reforzado. Propos
   17. examine({"target": "estanteria"}) [ERROR] Error: no existe ningún objeto con id 'estanteria'.
   18. examine({"target": "libro_algebra"}) [ERROR] Error: no existe ningún objeto con id 'libro_algebra'.
   19. examine({"target": "libro_geometria"}) [ok] Elementos de geometría aplicada: Encuadernación rígida de cartón forrado en tela negra, lomo reforzado. Propos
   20. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   21. examine({"target": "estanteria"}) [ERROR] Error: no existe ningún objeto con id 'estanteria'.
   22. examine({"target": "estanteria"}) [ERROR] Error: no existe ningún objeto con id 'estanteria'.
   23. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
   24. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
   25. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   26. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   27. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   28. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   29. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   30. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   31. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   32. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   33. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   34. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   35. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   36. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   37. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   38. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
   39. examine({"target": "caja_segura"}) [ERROR] Error: no existe ningún objeto con id 'caja_segura'.
  … 60 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T13

```
Escenario: office-sequence (dificultad hard)
Objetivo alcanzado: sí — secuencia completada en el orden correcto
Llamadas óptimas conocidas: 13; realizadas: 100

Secuencia de acciones:
    0. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
    1. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio amplio con cajones. Están todos vacíos salvo por clips y papel en blanco.
Está vacío
    2. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
    3. look({}) [ok] Estás en Corredor.
Un corredor central que distribuye hacia la oficina (oeste), el archivo (norte) y el depósi
    4. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Depósito.
    5. look({}) [ok] Estás en Depósito.
Un cuarto de limpieza con estanterías metálicas y un cajón etiquetado 'LLAVES'.
Ves:
  - ca
    6. examine({"target": "cajon_llaves"}) [ok] cajón de llaves: Un cajón metálico etiquetado 'LLAVES'. Dentro cuelga una sola llave pequeña.
Contiene:
  - ll
    7. take({"item": "llave_caja"}) [ok] Tomas llave de la caja fuerte.
    8. go({"direction": "norte"}) [ERROR] Error: no hay salida 'norte' desde aquí. Salidas disponibles: oeste.
    9. look({}) [ok] Estás en Depósito.
Un cuarto de limpieza con estanterías metálicas y un cajón etiquetado 'LLAVES'.
Ves:
  - ca
   10. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Corredor.
   11. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   12. look({}) [ok] Estás en Archivo.
Una sala con armarios de expedientes y una caja fuerte empotrada en la pared.
Ves:
  - caja 
   13. use({"item": "llave_caja", "target": "caja_fuerte"}) [ok] Usas llave de la caja fuerte con caja fuerte. Se abre.
   14. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Una caja fuerte empotrada con una cerradura de llave plana. Cerrada.
Contiene:
  - documento conf
   15. take({"item": "documento_confidencial"}) [ok] Tomas documento confidencial.
   16. take({"item": "llave_maestra"}) [ok] Tomas llave maestra.
   17. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   18. go({"direction": "sur"}) [ERROR] Error: no hay salida 'sur' desde aquí. Salidas disponibles: este, norte, oeste.
   19. look({}) [ok] Estás en Corredor.
Un corredor central que distribuye hacia la oficina (oeste), el archivo (norte) y el depósi
   20. use({"item": "llave_maestra", "target": "puerta_principal"}) [ERROR] Error: no ves ningún 'puerta_principal' aquí.
   21. look({}) [ok] Estás en Corredor.
Un corredor central que distribuye hacia la oficina (oeste), el archivo (norte) y el depósi
   22. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   23. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
   24. use({"item": "llave_maestra", "target": "puerta_principal"}) [ok] Usas llave maestra con puerta principal. Se abre.
   25. go({"direction": "puerta_principal"}) [ERROR] Error: no hay salida 'puerta_principal' desde aquí. Salidas disponibles: este.
   26. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
   27. go({"direction": "puerta_principal"}) [ERROR] Error: no hay salida 'puerta_principal' desde aquí. Salidas disponibles: este.
   28. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
   29. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
   30. look({}) [ok] Estás en Corredor.
Un corredor central que distribuye hacia la oficina (oeste), el archivo (norte) y el depósi
   31. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   32. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
   33. go({"direction": "puerta_principal"}) [ERROR] Error: no hay salida 'puerta_principal' desde aquí. Salidas disponibles: este.
   34. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
   35. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
   36. look({}) [ok] Estás en Corredor.
Un corredor central que distribuye hacia la oficina (oeste), el archivo (norte) y el depósi
   37. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   38. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
   39. go({"direction": "puerta_principal"}) [ERROR] Error: no hay salida 'puerta_principal' desde aquí. Salidas disponibles: este.
  … 60 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T14

```
Escenario: library-search (dificultad hard)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 7; realizadas: 17

Secuencia de acciones:
    0. look({}) [ok] Estás en Biblioteca del archivero.
Una sala rectangular con olor a papel viejo. Al norte, una estantería alta 
    1. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
    2. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
    3. examine({"target": "libro_jurisprudencia"}) [ok] Recopilación de sentencias del tribunal supremo: Tomo grueso encuadernado en piel parda, con el escudo real es
    4. examine({"target": "libro_genealogia"}) [ok] Genealogía de la casa de Andrade: Tomo grande encuadernado en piel azul, con grabados heráldicos en el lomo. C
    5. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
    6. examine({"target": "libro_alquimia"}) [ok] Notas sobre la transmutación de los metales: Manuscrito en cuarto, encuadernación de cuero rojo desgastado, si
    7. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta de hierro negro con la cerradura grabada con símbolos. Solo una llave con grabado
    8. examine({"target": "libro_filosofia"}) [ok] Diálogos sobre la naturaleza del juicio: Volumen de pequeño tamaño, encuadernado en piel verde con cantos dora
    9. examine({"target": "libro_historia"}) [ok] Anales del reino, década quinta: Tomo en folio, encuadernación de pergamino crudo, con cintas de cierre. Año 1
   10. examine({"target": "libro_recetario"}) [ok] Recetario del cocinero mayor: Manuscrito en cuarto, tapas blandas de pergamino, manchado de aceite. Receta del
   11. examine({"target": "libro_sermones"}) [ok] Colección de sermones dominicales: Tomo encuadernado en piel negra con cantos rojos, muy usado. Sermón XXI, pa
   12. take({"item": "llave_caja"}) [ok] Tomas llave de la caja.
   13. use({"item": "llave_caja", "target": "caja_fuerte"}) [ok] Usas llave de la caja con caja fuerte. Se abre.
   14. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   15. take({"item": "llave_grabada"}) [ok] Tomas llave grabada.
   16. use({"item": "llave_grabada", "target": "puerta_principal"}) [ok] Usas llave grabada con puerta principal. Se abre.
```


---

## T15

```
Escenario: study-with-key (dificultad easy)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 3; realizadas: 24

Secuencia de acciones:
    0. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
    1. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Contiene:
  - llave dorada [id: llave_oro]
    2. take({"item": "llave_oro"}) [ok] Tomas llave dorada.
    3. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
    4. examine({"target": "libro"}) [ERROR] Error: no existe ningún objeto con id 'libro'.
    5. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
    6. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
    7. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
    8. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
    9. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
   10. examine({"target": "estanteria"}) [ERROR] Error: no existe ningún objeto con id 'estanteria'.
   11. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   12. examine({"target": "estanteria"}) [ERROR] Error: no existe ningún objeto con id 'estanteria'.
   13. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   14. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   15. take({"item": "alfombra"}) [ERROR] Error: alfombra no es algo que puedas llevarte.
   16. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   17. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   18. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   19. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
   20. examine({"target": "puerta"}) [ERROR] Error: no existe ningún objeto con id 'puerta'.
   21. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta robusta de roble. La cerradura es dorada y parece reciente.
Estado: cerrada.
   22. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   23. use({"item": "llave_oro", "target": "puerta_principal"}) [ok] Usas llave dorada con puerta principal. Se abre.
```


---

## T16

```
Escenario: office-sequence (dificultad hard)
Objetivo alcanzado: no — faltan condiciones: documento confidencial no está en el inventario; puerta principal está cerrada
Llamadas óptimas conocidas: 13; realizadas: 100

Secuencia de acciones:
    0. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
    1. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio amplio con cajones. Están todos vacíos salvo por clips y papel en blanco.
Está vacío
    2. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
    3. look({}) [ok] Estás en Corredor.
Un corredor central que distribuye hacia la oficina (oeste), el archivo (norte) y el depósi
    4. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
    5. look({}) [ok] Estás en Archivo.
Una sala con armarios de expedientes y una caja fuerte empotrada en la pared.
Ves:
  - caja 
    6. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Una caja fuerte empotrada con una cerradura de llave plana. Cerrada.
Está cerrado con llave. No p
    7. go({"direction": "este"}) [ERROR] Error: no hay salida 'este' desde aquí. Salidas disponibles: sur.
    8. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
    9. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   10. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio amplio con cajones. Están todos vacíos salvo por clips y papel en blanco.
Está vacío
   11. go({"direction": "norte"}) [ERROR] Error: no hay salida 'norte' desde aquí. Salidas disponibles: este.
   12. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
   13. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
   14. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   15. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Una caja fuerte empotrada con una cerradura de llave plana. Cerrada.
Está cerrado con llave. No p
   16. go({"direction": "este"}) [ERROR] Error: no hay salida 'este' desde aquí. Salidas disponibles: sur.
   17. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   18. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   19. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio amplio con cajones. Están todos vacíos salvo por clips y papel en blanco.
Está vacío
   20. go({"direction": "norte"}) [ERROR] Error: no hay salida 'norte' desde aquí. Salidas disponibles: este.
   21. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
   22. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
   23. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   24. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Una caja fuerte empotrada con una cerradura de llave plana. Cerrada.
Está cerrado con llave. No p
   25. go({"direction": "este"}) [ERROR] Error: no hay salida 'este' desde aquí. Salidas disponibles: sur.
   26. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   27. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   28. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio amplio con cajones. Están todos vacíos salvo por clips y papel en blanco.
Está vacío
   29. go({"direction": "norte"}) [ERROR] Error: no hay salida 'norte' desde aquí. Salidas disponibles: este.
   30. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
   31. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
   32. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   33. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Una caja fuerte empotrada con una cerradura de llave plana. Cerrada.
Está cerrado con llave. No p
   34. go({"direction": "este"}) [ERROR] Error: no hay salida 'este' desde aquí. Salidas disponibles: sur.
   35. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   36. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   37. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio amplio con cajones. Están todos vacíos salvo por clips y papel en blanco.
Está vacío
   38. go({"direction": "norte"}) [ERROR] Error: no hay salida 'norte' desde aquí. Salidas disponibles: este.
   39. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
  … 60 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T17

```
Escenario: vault-combination (dificultad extreme)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 21; realizadas: 2

Secuencia de acciones:
    0. look({}) [ok] Estás en Vestíbulo.
Un vestíbulo de hormigón con un panel de seguridad junto a la puerta principal. El panel t
    1. examine({"obj": "puerta_principal"}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): obj. Falta(n) el/los requerido(s): targ
```


---

## T18

```
Escenario: study-with-key (dificultad easy)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 3; realizadas: 2

Secuencia de acciones:
    0. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
    1. examine({"objeto": "alfombra"}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): objeto. Falta(n) el/los requerido(s): t
```


---

## T19

```
Escenario: backtracking-vault (dificultad extreme)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 18; realizadas: 5

Secuencia de acciones:
    0. look({}) [ok] Estás en Entrada de la bóveda.
Una antesala con la puerta principal de salida y un cofre antiguo de hierro con
    1. examine({"objeto": "cofre_antiguo"}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): objeto. Falta(n) el/los requerido(s): t
    2. examine({"target": "cofre_antiguo"}) [ok] cofre antiguo: Un cofre de hierro con una cerradura corroída. Necesita una llave oxidada que encaje en su meca
    3. examine({"target": "puerta_principal"}) [ok] puerta principal: La puerta de salida. Su cerradura pide una llave maestra.
Estado: cerrada.
    4. examine({"target": "cerradura_corroída"}) [ERROR] Error: no existe ningún objeto con id 'cerradura_corroída'.
```


---

## T20

```
Escenario: extreme-archive (dificultad extreme)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 4; realizadas: 2

Secuencia de acciones:
    0. examine({"target": "estantería"}) [ERROR] Error: no existe ningún objeto con id 'estantería'.
    1. examine({"target": "expediente"}) [ERROR] Error: no existe ningún objeto con id 'expediente'.
```


---

## T21

```
Escenario: extreme-archive (dificultad extreme)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 4; realizadas: 2

Secuencia de acciones:
    0. examine({"target": "estantería"}) [ERROR] Error: no existe ningún objeto con id 'estantería'.
    1. examine({"target": "expediente"}) [ERROR] Error: no existe ningún objeto con id 'expediente'.
```


---

## T22

```
Escenario: office-sequence (dificultad hard)
Objetivo alcanzado: sí — secuencia completada en el orden correcto
Llamadas óptimas conocidas: 13; realizadas: 100

Secuencia de acciones:
    0. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
    1. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
    2. look({}) [ok] Estás en Corredor.
Un corredor central que distribuye hacia la oficina (oeste), el archivo (norte) y el depósi
    3. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Depósito.
    4. look({}) [ok] Estás en Depósito.
Un cuarto de limpieza con estanterías metálicas y un cajón etiquetado 'LLAVES'.
Ves:
  - ca
    5. take({"item": "cajon_llaves"}) [ERROR] Error: cajón de llaves no es algo que puedas llevarte.
    6. examine({"target": "cajon_llaves"}) [ok] cajón de llaves: Un cajón metálico etiquetado 'LLAVES'. Dentro cuelga una sola llave pequeña.
Contiene:
  - ll
    7. take({"item": "llave_caja"}) [ok] Tomas llave de la caja fuerte.
    8. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Corredor.
    9. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   10. examine({"target": "caja_fuerte"}) [ERROR] Error: no ves ningún 'caja_fuerte' aquí.
   11. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
   12. go({"direction": "norte"}) [ERROR] Error: no hay salida 'norte' desde aquí. Salidas disponibles: este.
   13. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
   14. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   15. look({}) [ok] Estás en Archivo.
Una sala con armarios de expedientes y una caja fuerte empotrada en la pared.
Ves:
  - caja 
   16. use({"item": "llave_caja", "target": "caja_fuerta"}) [ERROR] Error: no existe ningún objeto con id 'caja_fuerta'.
   17. look({}) [ok] Estás en Archivo.
Una sala con armarios de expedientes y una caja fuerte empotrada en la pared.
Ves:
  - caja 
   18. use({"item": "llave_caja", "target": "caja_fuerte"}) [ok] Usas llave de la caja fuerte con caja fuerte. Se abre.
   19. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Una caja fuerte empotrada con una cerradura de llave plana. Cerrada.
Contiene:
  - documento conf
   20. take({"item": "documento_confidencial"}) [ok] Tomas documento confidencial.
   21. take({"item": "llave_maestra"}) [ok] Tomas llave maestra.
   22. go({"direction": "este"}) [ERROR] Error: no hay salida 'este' desde aquí. Salidas disponibles: sur.
   23. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   24. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Depósito.
   25. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Corredor.
   26. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   27. go({"direction": "norte"}) [ERROR] Error: no hay salida 'norte' desde aquí. Salidas disponibles: este.
   28. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
   29. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Depósito.
   30. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Corredor.
   31. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   32. use({"item": "llave_maestra", "target": "puerta_principal"}) [ok] Usas llave maestra con puerta principal. Se abre.
   33. go({"direction": "norte"}) [ERROR] Error: no hay salida 'norte' desde aquí. Salidas disponibles: este.
   34. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
   35. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Depósito.
   36. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Corredor.
   37. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   38. use({"item": "llave_maestra", "target": "puerta_principal"}) [ok] puerta principal ya está abierta.
   39. go({"direction": "norte"}) [ERROR] Error: no hay salida 'norte' desde aquí. Salidas disponibles: este.
  … 60 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T23

```
Escenario: vault-combination (dificultad extreme)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 21; realizadas: 50

Secuencia de acciones:
    0. look({}) [ok] Estás en Vestíbulo.
Un vestíbulo de hormigón con un panel de seguridad junto a la puerta principal. El panel t
    1. examine({"obj": "puerta_principal"}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): obj. Falta(n) el/los requerido(s): targ
    2. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta blindada controlada por un panel de tres ranuras. Solo abre cuando se colocan los
    3. look({}) [ok] Estás en Vestíbulo.
Un vestíbulo de hormigón con un panel de seguridad junto a la puerta principal. El panel t
    4. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Galería central.
    5. look({}) [ok] Estás en Galería central.
Una galería que distribuye hacia varias salas: el taller al este, la biblioteca al o
    6. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
    7. look({}) [ok] Estás en Galería central.
Una galería que distribuye hacia varias salas: el taller al este, la biblioteca al o
    8. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
    9. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   10. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   11. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   12. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   13. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   14. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   15. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   16. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   17. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   18. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   19. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   20. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   21. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   22. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   23. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   24. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   25. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   26. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   27. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   28. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   29. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   30. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   31. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   32. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   33. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   34. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   35. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   36. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   37. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   38. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
   39. examine({"target": "puerta_deposito"}) [ok] puerta del depósito: Una puerta metálica con una cerradura robusta. Cerrada.
Estado: cerrada.
  … 10 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (50).
```


---

## T24

```
Escenario: apartment-keys (dificultad medium)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 7; realizadas: 12

Secuencia de acciones:
    0. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    1. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Pasillo.
    2. look({}) [ok] Estás en Pasillo.
Un pasillo en penumbra con cuadros torcidos. Conecta el recibidor al sur con la cocina al es
    3. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Cocina.
    4. look({}) [ok] Estás en Cocina.
Una cocina pequeña con azulejos blancos. Hay una mesada con un cajón cerrado y olor a café fr
    5. examine({"target": "cajon"}) [ok] cajón de la cocina: Un cajón de madera bajo la mesada. Se abre con un tirón y dentro hay cubiertos sueltos y a
    6. take({"item": "llave_oro"}) [ok] Tomas llave dorada.
    7. go({"direction": "sur"}) [ERROR] Error: no hay salida 'sur' desde aquí. Salidas disponibles: oeste.
    8. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Pasillo.
    9. go({"direction": "oeste"}) [ERROR] Error: no hay salida 'oeste' desde aquí. Salidas disponibles: este, sur.
   10. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Recibidor.
   11. use({"item": "llave_oro", "target": "puerta_principal"}) [ok] Usas llave dorada con puerta principal. Se abre.
```


---

## T25

```
Escenario: apartment-keys (dificultad medium)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 7; realizadas: 14

Secuencia de acciones:
    0. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    1. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Pasillo.
    2. look({}) [ok] Estás en Pasillo.
Un pasillo en penumbra con cuadros torcidos. Conecta el recibidor al sur con la cocina al es
    3. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Cocina.
    4. look({}) [ok] Estás en Cocina.
Una cocina pequeña con azulejos blancos. Hay una mesada con un cajón cerrado y olor a café fr
    5. examine({"target": "cajon"}) [ok] cajón de la cocina: Un cajón de madera bajo la mesada. Se abre con un tirón y dentro hay cubiertos sueltos y a
    6. take({"item": "llave_oro"}) [ok] Tomas llave dorada.
    7. use({"item": "llave_oro", "target": "puerta_principal"}) [ERROR] Error: no ves ningún 'puerta_principal' aquí.
    8. look({}) [ok] Estás en Cocina.
Una cocina pequeña con azulejos blancos. Hay una mesada con un cajón cerrado y olor a café fr
    9. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Pasillo.
   10. go({"direction": "oeste"}) [ERROR] Error: no hay salida 'oeste' desde aquí. Salidas disponibles: este, sur.
   11. look({}) [ok] Estás en Pasillo.
Un pasillo en penumbra con cuadros torcidos. Conecta el recibidor al sur con la cocina al es
   12. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Recibidor.
   13. use({"item": "llave_oro", "target": "puerta_principal"}) [ok] Usas llave dorada con puerta principal. Se abre.
```


---

## T26

```
Escenario: color-locks (dificultad medium)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 11; realizadas: 19

Secuencia de acciones:
    0. examine({"target": "cofre_plateado"}) [ERROR] Error: no existe ningún objeto con id 'cofre_plateado'.
    1. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
    2. examine({"target": "cofre_plata"}) [ok] cofre plateado: Un cofre pequeño con tachuelas plateadas y una cerradura del mismo color. Encaja con una llave
    3. take({"item": "llave_plata"}) [ok] Tomas llave plateada.
    4. examine({"target": "cofre_plata"}) [ok] cofre plateado: Un cofre pequeño con tachuelas plateadas y una cerradura del mismo color. Encaja con una llave
    5. use({"item": "llave_plata", "target": "cofre_plata"}) [ok] Usas llave plateada con cofre plateado. Se abre.
    6. examine({"target": "cofre_plata"}) [ok] cofre plateado: Un cofre pequeño con tachuelas plateadas y una cerradura del mismo color. Encaja con una llave
    7. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
    8. use({"item": "llave_roja", "target": "cofre_rojo"}) [ERROR] Error: no llevas ningún 'llave_roja'.
    9. take({"item": "llave_roja"}) [ok] Tomas llave roja.
   10. use({"item": "llave_roja", "target": "cofre_rojo"}) [ok] Usas llave roja con cofre rojo. Se abre.
   11. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   12. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   13. use({"item": "llave_verde", "target": "cofre_verde"}) [ERROR] Error: no llevas ningún 'llave_verde'.
   14. take({"item": "llave_verde"}) [ok] Tomas llave verde.
   15. use({"item": "llave_verde", "target": "cofre_verde"}) [ok] Usas llave verde con cofre verde. Se abre.
   16. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   17. take({"item": "llave_oro"}) [ok] Tomas llave dorada.
   18. use({"item": "llave_oro", "target": "puerta_principal"}) [ok] Usas llave dorada con puerta principal. Se abre.
```


---

## T27

```
Escenario: apartment-keys (dificultad medium)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 7; realizadas: 23

Secuencia de acciones:
    0. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    1. examine({"type": "output", "text": "Estás en el recibidor de un apartamento desconocido. La puerta principal está cerrada con llave. Hay un pasillo que se interna en el apartamento. El inventario está vacío."}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): text, type. Falta(n) el/los requerido(s
    2. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta de metal con una cerradura simple. Necesita una llave para abrirse.
Estado: cerra
    3. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    4. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
    5. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    6. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
    7. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    8. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
    9. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   10. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
   11. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   12. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
   13. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   14. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
   15. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   16. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
   17. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   18. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
   19. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   20. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.
   21. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   22. examine({"target": "pasillo"}) [ERROR] Error: no existe ningún objeto con id 'pasillo'.

Corte del bucle: Se alcanzó el máximo de iteraciones (22).
```


---

## T28

```
Escenario: study-with-key (dificultad easy)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 3; realizadas: 101

Secuencia de acciones:
    0. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
    1. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
    2. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Contiene:
  - llave dorada [id: llave_oro]
    3. take({"item": "llave_oro"}) [ok] Tomas llave dorada.
    4. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
    5. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
    6. take({"item": "alfombra"}) [ERROR] Error: alfombra no es algo que puedas llevarte.
    7. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
    8. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
    9. examine({"target": "libro"}) [ERROR] Error: no existe ningún objeto con id 'libro'.
   10. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
   11. examine({"target": "cajones"}) [ERROR] Error: no existe ningún objeto con id 'cajones'.
   12. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   13. examine({"target": "libro"}) [ERROR] Error: no existe ningún objeto con id 'libro'.
   14. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   15. examine({"target": "libro"}) [ERROR] Error: no existe ningún objeto con id 'libro'.
   16. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   17. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   18. take({"item": "alfombra"}) [ERROR] Error: alfombra no es algo que puedas llevarte.
   19. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   20. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
   21. examine({"target": "libro"}) [ERROR] Error: no existe ningún objeto con id 'libro'.
   22. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   23. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   24. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
   25. examine({"target": "estanteria"}) [ERROR] Error: no existe ningún objeto con id 'estanteria'.
   26. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   27. examine({"target": "estanteria"}) [ERROR] Error: no existe ningún objeto con id 'estanteria'.
   28. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   29. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   30. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
   31. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   32. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   33. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
   34. examine({"target": "cajones"}) [ERROR] Error: no existe ningún objeto con id 'cajones'.
   35. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   36. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   37. take({"item": "alfombra"}) [ERROR] Error: alfombra no es algo que puedas llevarte.
   38. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   39. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
  … 61 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T29

```
Escenario: library-search (dificultad hard)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 7; realizadas: 100

Secuencia de acciones:
    0. look({}) [ok] Estás en Biblioteca del archivero.
Una sala rectangular con olor a papel viejo. Al norte, una estantería alta 
    1. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
    2. examine({"target": "libro_geometria"}) [ok] Elementos de geometría aplicada: Encuadernación rígida de cartón forrado en tela negra, lomo reforzado. Propos
    3. examine({"target": "libro_alquimia"}) [ok] Notas sobre la transmutación de los metales: Manuscrito en cuarto, encuadernación de cuero rojo desgastado, si
    4. examine({"target": "libro_filosofia"}) [ok] Diálogos sobre la naturaleza del juicio: Volumen de pequeño tamaño, encuadernado en piel verde con cantos dora
    5. examine({"target": "libro_historia"}) [ok] Anales del reino, década quinta: Tomo en folio, encuadernación de pergamino crudo, con cintas de cierre. Año 1
    6. examine({"target": "libro_jurisprudencia"}) [ok] Recopilación de sentencias del tribunal supremo: Tomo grueso encuadernado en piel parda, con el escudo real es
    7. examine({"target": "libro_recetario"}) [ok] Recetario del cocinero mayor: Manuscrito en cuarto, tapas blandas de pergamino, manchado de aceite. Receta del
    8. examine({"target": "libro_genealogia"}) [ok] Genealogía de la casa de Andrade: Tomo grande encuadernado en piel azul, con grabados heráldicos en el lomo. C
    9. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   10. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
   11. examine({"target": "libro_sermones"}) [ok] Colección de sermones dominicales: Tomo encuadernado en piel negra con cantos rojos, muy usado. Sermón XXI, pa
   12. take({"item": "llave_caja"}) [ok] Tomas llave de la caja.
   13. use({"item": "llave_caja", "target": "caja_fuerte"}) [ok] Usas llave de la caja con caja fuerte. Se abre.
   14. look({}) [ok] Estás en Biblioteca del archivero.
Una sala rectangular con olor a papel viejo. Al norte, una estantería alta 
   15. examine({"target": "libro_geometria"}) [ok] Elementos de geometría aplicada: Encuadernación rígida de cartón forrado en tela negra, lomo reforzado. Propos
   16. examine({"target": "libro_alquimia"}) [ok] Notas sobre la transmutación de los metales: Manuscrito en cuarto, encuadernación de cuero rojo desgastado, si
   17. examine({"target": "libro_filosofia"}) [ok] Diálogos sobre la naturaleza del juicio: Volumen de pequeño tamaño, encuadernado en piel verde con cantos dora
   18. examine({"target": "libro_historia"}) [ok] Anales del reino, década quinta: Tomo en folio, encuadernación de pergamino crudo, con cintas de cierre. Año 1
   19. examine({"target": "libro_jurisprudencia"}) [ok] Recopilación de sentencias del tribunal supremo: Tomo grueso encuadernado en piel parda, con el escudo real es
   20. examine({"target": "libro_recetario"}) [ok] Recetario del cocinero mayor: Manuscrito en cuarto, tapas blandas de pergamino, manchado de aceite. Receta del
   21. examine({"target": "libro_genealogia"}) [ok] Genealogía de la casa de Andrade: Tomo grande encuadernado en piel azul, con grabados heráldicos en el lomo. C
   22. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
   23. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
   24. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   25. examine({"target": "llave_grabada"}) [ok] llave grabada: Una llave gruesa de hierro, con grabados de alquimia en la cabeza. Pesada. Encaja en una cerrad
   26. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
   27. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
   28. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   29. examine({"target": "llave_grabada"}) [ok] llave grabada: Una llave gruesa de hierro, con grabados de alquimia en la cabeza. Pesada. Encaja en una cerrad
   30. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
   31. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
   32. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   33. examine({"target": "llave_grabada"}) [ok] llave grabada: Una llave gruesa de hierro, con grabados de alquimia en la cabeza. Pesada. Encaja en una cerrad
   34. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
   35. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
   36. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   37. examine({"target": "llave_grabada"}) [ok] llave grabada: Una llave gruesa de hierro, con grabados de alquimia en la cabeza. Pesada. Encaja en una cerrad
   38. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
   39. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
  … 60 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T30

```
Escenario: apartment-keys (dificultad medium)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 7; realizadas: 100

Secuencia de acciones:
    0. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    1. examine({"target": "perchero"}) [ERROR] Error: no existe ningún objeto con id 'perchero'.
    2. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    3. examine({"target": "espejo"}) [ERROR] Error: no existe ningún objeto con id 'espejo'.
    4. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    5. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    6. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    7. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    8. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    9. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   10. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   11. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   12. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   13. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   14. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   15. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   16. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   17. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   18. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   19. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   20. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   21. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   22. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   23. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   24. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   25. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   26. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   27. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   28. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   29. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   30. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   31. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   32. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   33. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   34. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   35. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   36. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   37. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   38. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   39. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
  … 60 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T31

```
Escenario: apartment-keys (dificultad medium)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 7; realizadas: 100

Secuencia de acciones:
    0. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    1. examine({"target": "espejo"}) [ERROR] Error: no existe ningún objeto con id 'espejo'.
    2. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    3. examine({"target": "perchero"}) [ERROR] Error: no existe ningún objeto con id 'perchero'.
    4. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    5. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    6. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    7. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    8. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
    9. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   10. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   11. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   12. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   13. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   14. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   15. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   16. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   17. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   18. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   19. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   20. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   21. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   22. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   23. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   24. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   25. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   26. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   27. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   28. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   29. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   30. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   31. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   32. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   33. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   34. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   35. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   36. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   37. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   38. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
   39. look({}) [ok] Estás en Recibidor.
Un recibidor estrecho con un perchero vacío y un espejo polvoriento. La puerta principal, 
  … 60 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T32

```
Escenario: study-with-key (dificultad easy)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 3; realizadas: 20

Secuencia de acciones:
    0. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
    1. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Contiene:
  - llave dorada [id: llave_oro]
    2. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
    3. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Contiene:
  - llave dorada [id: llave_oro]
    4. examine({"target": "cajon_cerrado"}) [ERROR] Error: no existe ningún objeto con id 'cajon_cerrado'.
    5. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
    6. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Contiene:
  - llave dorada [id: llave_oro]
    7. take({"item": "llave_oro"}) [ok] Tomas llave dorada.
    8. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
    9. examine({"target": "piso"}) [ERROR] Error: no existe ningún objeto con id 'piso'.
   10. examine({"target": "suelo"}) [ERROR] Error: no existe ningún objeto con id 'suelo'.
   11. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   12. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   13. take({"item": "alfombra"}) [ERROR] Error: alfombra no es algo que puedas llevarte.
   14. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Está vacío.
   15. examine({"target": "caja"}) [ERROR] Error: no existe ningún objeto con id 'caja'.
   16. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
   17. examine({"target": "habitacion"}) [ERROR] Error: no existe ningún objeto con id 'habitacion'.
   18. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
   19. use({"item": "llave_oro", "target": "puerta_principal"}) [ok] Usas llave dorada con puerta principal. Se abre.
```


---

## T33

```
Escenario: backtracking-vault (dificultad extreme)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 18; realizadas: 5

Secuencia de acciones:
    0. look({}) [ok] Estás en Entrada de la bóveda.
Una antesala con la puerta principal de salida y un cofre antiguo de hierro con
    1. examine({"objeto": "cofre_antiguo"}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): objeto. Falta(n) el/los requerido(s): t
    2. examine({"target": "cofre_antiguo"}) [ok] cofre antiguo: Un cofre de hierro con una cerradura corroída. Necesita una llave oxidada que encaje en su meca
    3. examine({"target": "puerta_principal"}) [ok] puerta principal: La puerta de salida. Su cerradura pide una llave maestra.
Estado: cerrada.
    4. examine({"target": "cerradura"}) [ERROR] Error: no existe ningún objeto con id 'cerradura'.
```


---

## T34

```
Escenario: color-locks (dificultad medium)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 11; realizadas: 21

Secuencia de acciones:
    0. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
    1. examine({"target": "llave_plateada"}) [ERROR] Error: no existe ningún objeto con id 'llave_plateada'.
    2. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
    3. examine({"target": "llave_plata"}) [ok] llave plateada: Una llave pequeña y brillante, de plata pulida. Por su tamaño, parece encajar en una cerradura
    4. take({"item": "llave_plata"}) [ok] Tomas llave plateada.
    5. examine({"target": "cofre_plata"}) [ok] cofre plateado: Un cofre pequeño con tachuelas plateadas y una cerradura del mismo color. Encaja con una llave
    6. use({"item": "llave_plata", "target": "cofre_plata"}) [ok] Usas llave plateada con cofre plateado. Se abre.
    7. examine({"target": "llave_plateada"}) [ERROR] Error: no existe ningún objeto con id 'llave_plateada'.
    8. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
    9. examine({"target": "cofre_plata"}) [ok] cofre plateado: Un cofre pequeño con tachuelas plateadas y una cerradura del mismo color. Encaja con una llave
   10. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   11. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
   12. take({"item": "llave_roja"}) [ok] Tomas llave roja.
   13. use({"item": "llave_roja", "target": "cofre_rojo"}) [ok] Usas llave roja con cofre rojo. Se abre.
   14. examine({"target": "cofre_rojo"}) [ok] cofre rojo: Un cofre mediano pintado de rojo, con una cerradura roja del mismo tono. Encaja con una llave del 
   15. take({"item": "llave_verde"}) [ok] Tomas llave verde.
   16. use({"item": "llave_verde", "target": "cofre_verde"}) [ok] Usas llave verde con cofre verde. Se abre.
   17. examine({"target": "cofre_verde"}) [ok] cofre verde: Un cofre grande pintado de verde, con una cerradura verde voluminosa. Encaja con una llave del mi
   18. take({"item": "llave_oro"}) [ok] Tomas llave dorada.
   19. use({"item": "llave_oro", "target": "puerta_principal"}) [ok] Usas llave dorada con puerta principal. Se abre.
   20. look({}) [ok] Estás en Sótano.
Un sótano de piedra con olor a humedad y una bombilla solitaria colgando del techo. Una repis
```


---

## T35

```
Escenario: office-sequence (dificultad hard)
Objetivo alcanzado: sí — secuencia completada en el orden correcto
Llamadas óptimas conocidas: 13; realizadas: 100

Secuencia de acciones:
    0. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
    1. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio amplio con cajones. Están todos vacíos salvo por clips y papel en blanco.
Está vacío
    2. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
    3. look({}) [ok] Estás en Corredor.
Un corredor central que distribuye hacia la oficina (oeste), el archivo (norte) y el depósi
    4. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
    5. look({}) [ok] Estás en Archivo.
Una sala con armarios de expedientes y una caja fuerte empotrada en la pared.
Ves:
  - caja 
    6. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Una caja fuerte empotrada con una cerradura de llave plana. Cerrada.
Está cerrado con llave. No p
    7. examine({"target": "armarios"}) [ERROR] Error: no existe ningún objeto con id 'armarios'.
    8. look({}) [ok] Estás en Archivo.
Una sala con armarios de expedientes y una caja fuerte empotrada en la pared.
Ves:
  - caja 
    9. go({"direction": "este"}) [ERROR] Error: no hay salida 'este' desde aquí. Salidas disponibles: sur.
   10. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   11. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Depósito.
   12. look({}) [ok] Estás en Depósito.
Un cuarto de limpieza con estanterías metálicas y un cajón etiquetado 'LLAVES'.
Ves:
  - ca
   13. examine({"target": "cajon_llaves"}) [ok] cajón de llaves: Un cajón metálico etiquetado 'LLAVES'. Dentro cuelga una sola llave pequeña.
Contiene:
  - ll
   14. take({"item": "llave_caja"}) [ok] Tomas llave de la caja fuerte.
   15. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Corredor.
   16. go({"direction": "norte"}) [ok] Caminas hacia norte. Llegas a Archivo.
   17. use({"item": "llave_caja", "target": "caja_fuerte"}) [ok] Usas llave de la caja fuerte con caja fuerte. Se abre.
   18. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Una caja fuerte empotrada con una cerradura de llave plana. Cerrada.
Contiene:
  - documento conf
   19. take({"item": "documento_confidencial"}) [ok] Tomas documento confidencial.
   20. take({"item": "llave_maestra"}) [ok] Tomas llave maestra.
   21. use({"item": "llave_maestra", "target": "puerta_principal"}) [ERROR] Error: no ves ningún 'puerta_principal' aquí.
   22. look({}) [ok] Estás en Archivo.
Una sala con armarios de expedientes y una caja fuerte empotrada en la pared.
Ves:
  - caja 
   23. go({"direction": "oeste"}) [ERROR] Error: no hay salida 'oeste' desde aquí. Salidas disponibles: sur.
   24. go({"direction": "sur"}) [ok] Caminas hacia sur. Llegas a Corredor.
   25. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   26. look({}) [ok] Estás en Oficina principal.
Una oficina con un escritorio amplio y una puerta principal blindada. Un corredor 
   27. use({"item": "llave_maestra", "target": "puerta_principal"}) [ok] Usas llave maestra con puerta principal. Se abre.
   28. go({"direction": "puerta_principal"}) [ERROR] Error: no hay salida 'puerta_principal' desde aquí. Salidas disponibles: este.
   29. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
   30. go({"direction": "puerta_principal"}) [ERROR] Error: no hay salida 'puerta_principal' desde aquí. Salidas disponibles: este, norte, oeste.
   31. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Depósito.
   32. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Corredor.
   33. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
   34. go({"direction": "puerta_principal"}) [ERROR] Error: no hay salida 'puerta_principal' desde aquí. Salidas disponibles: este.
   35. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Corredor.
   36. go({"direction": "puerta_principal"}) [ERROR] Error: no hay salida 'puerta_principal' desde aquí. Salidas disponibles: este, norte, oeste.
   37. go({"direction": "este"}) [ok] Caminas hacia este. Llegas a Depósito.
   38. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Corredor.
   39. go({"direction": "oeste"}) [ok] Caminas hacia oeste. Llegas a Oficina principal.
  … 60 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T36

```
Escenario: library-search (dificultad hard)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 7; realizadas: 22

Secuencia de acciones:
    0. look({}) [ok] Estás en Biblioteca del archivero.
Una sala rectangular con olor a papel viejo. Al norte, una estantería alta 
    1. examine({"objeto": "caja_fuerte"}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): objeto. Falta(n) el/los requerido(s): t
    2. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
    3. examine({"target": "estanteria_alta"}) [ok] estantería alta: Una estantería de roble de cuatro baldas. Solo la balda superior tiene libros — ocho volúmene
    4. examine({"target": "libro_genealogia"}) [ok] Genealogía de la casa de Andrade: Tomo grande encuadernado en piel azul, con grabados heráldicos en el lomo. C
    5. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta de hierro negro con la cerradura grabada con símbolos. Solo una llave con grabado
    6. examine({"target": "caja_forte"}) [ERROR] Error: no existe ningún objeto con id 'caja_forte'.
    7. examine({"target": "estanteria_norte"}) [ERROR] Error: no existe ningún objeto con id 'estanteria_norte'.
    8. examine({"target": "escritorio_centro"}) [ERROR] Error: no existe ningún objeto con id 'escritorio_centro'.
    9. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta de hierro negro con la cerradura grabada con símbolos. Solo una llave con grabado
   10. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   11. examine({"target": "estanteria_norte"}) [ERROR] Error: no existe ningún objeto con id 'estanteria_norte'.
   12. examine({"target": "estanteria"}) [ERROR] Error: no existe ningún objeto con id 'estanteria'.
   13. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
   14. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   15. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta de hierro negro con la cerradura grabada con símbolos. Solo una llave con grabado
   16. examine({"target": "estantería"}) [ERROR] Error: no existe ningún objeto con id 'estantería'.
   17. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con un único cajón estrecho. Lo abres y lo encuentras vacío salvo por resto
   18. examine({"target": "caja_fuerte"}) [ok] caja fuerte: Caja fuerte de hierro empotrada en el muro. El disco de combinación visible es decorativo: la cer
   19. examine({"target": "puerta_principal"}) [ok] puerta principal: Una puerta de hierro negro con la cerradura grabada con símbolos. Solo una llave con grabado
   20. examine({"target": "estantería"}) [ERROR] Error: no existe ningún objeto con id 'estantería'.
   21. examine({"target": "volúmenes"}) [ERROR] Error: no existe ningún objeto con id 'volúmenes'.

Corte del bucle: Se alcanzó el máximo de iteraciones (22).
```


---

## T37

```
Escenario: office-sequence (dificultad hard)
Objetivo alcanzado: no — faltan condiciones: documento confidencial no está en el inventario; puerta principal está cerrada
Llamadas óptimas conocidas: 13; realizadas: 1

Secuencia de acciones:
    0. go({"direction": "sur"}) [ERROR] Error: no hay salida 'sur' desde aquí. Salidas disponibles: este.
```


---

## T38

```
Escenario: study-with-key (dificultad easy)
Objetivo alcanzado: sí — puerta principal está abierta
Llamadas óptimas conocidas: 3; realizadas: 4

Secuencia de acciones:
    0. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
    1. examine({"target": "alfombra"}) [ok] alfombra: Una vieja alfombra persa. Algo abulta debajo.
Contiene:
  - llave dorada [id: llave_oro]
    2. take({"item": "llave_oro"}) [ok] Tomas llave dorada.
    3. use({"item": "llave_oro", "target": "puerta_principal"}) [ok] Usas llave dorada con puerta principal. Se abre.
```


---

## T39

```
Escenario: study-with-key (dificultad easy)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 3; realizadas: 100

Secuencia de acciones:
    0. look({}) [ok] Estás en Estudio.
Un estudio pequeño forrado de libros. Una alfombra persa cubre el centro del suelo. A un lad
    1. examine({"target": "escritorio"}) [ok] escritorio: Un escritorio de roble con dos cajones. Ambos están abiertos y vacíos.
Está vacío.
    2. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
    3. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
    4. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
    5. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
    6. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
    7. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
    8. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
    9. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   10. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   11. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   12. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   13. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   14. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   15. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   16. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   17. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   18. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   19. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   20. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   21. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   22. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   23. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   24. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   25. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   26. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   27. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   28. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   29. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   30. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   31. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   32. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   33. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   34. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   35. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   36. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   37. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
   38. examine({"target": "cajon_izquierdo"}) [ERROR] Error: no existe ningún objeto con id 'cajon_izquierdo'.
   39. examine({"target": "cajon_derecho"}) [ERROR] Error: no existe ningún objeto con id 'cajon_derecho'.
  … 60 acciones más (omitidas)

Corte del bucle: Se alcanzó el máximo de iteraciones (100).
```


---

## T40

```
Escenario: backtracking-vault (dificultad extreme)
Objetivo alcanzado: no — puerta principal está cerrada
Llamadas óptimas conocidas: 18; realizadas: 2

Secuencia de acciones:
    0. look({}) [ok] Estás en Entrada de la bóveda.
Una antesala con la puerta principal de salida y un cofre antiguo de hierro con
    1. examine({"objeto": "cofre_antiguo"}) [ERROR] Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): objeto. Falta(n) el/los requerido(s): t
```
