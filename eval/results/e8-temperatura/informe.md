# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 150

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 79% (118/150) |
| eficiencia media (éxitos) | 0.47 |
| fracción de llamadas repetidas | 43% |
| pasos medios | 41.8 |
| llamadas al LLM medias | 41.8 |
| tokens entrada / salida | 184117 / 2466 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 16.3 s |
| latencia media | 40.1 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 78% (39/50) | 0.45 | 46% | 44.8 | 212027 |
| temperatura_05 | 78% (39/50) | 0.45 | 46% | 48.0 | 207255 |
| temperatura_09 | 80% (40/50) | 0.49 | 37% | 32.7 | 133068 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 97% (29/30) | 8% | 8.0 |
| medium | 77% (46/60) | 46% | 34.5 |
| hard | 72% (43/60) | 57% | 66.0 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 97% (29/30) | 8.0 | 8% | bucle |
| color-locks | 11 | 70% (21/30) | 39.4 | 44% | bucle |
| apartment-keys | 7 | 83% (25/30) | 29.6 | 49% | bucle |
| library-search | 7 | 67% (20/30) | 43.1 | 33% | bucle, parada_prematura |
| office-sequence | 13 | 77% (23/30) | 89.0 | 82% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 31 |
| parada_prematura | 1 |
