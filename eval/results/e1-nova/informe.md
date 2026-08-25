# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 150

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 54% (81/150) |
| eficiencia media (éxitos) | 0.41 |
| fracción de llamadas repetidas | 61% |
| pasos medios | 63.1 |
| llamadas al LLM medias | 62.7 |
| tokens entrada / salida | 159306 / 3409 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 65.4 s |
| latencia media | 50.3 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 70% (35/50) | 0.46 | 48% | 50.5 | 218744 |
| memoria_ajustada | 58% (29/50) | 0.45 | 58% | 60.5 | 120376 |
| memoria_minima | 34% (17/50) | 0.25 | 77% | 78.4 | 138797 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 77% (23/30) | 34% | 30.5 |
| medium | 68% (41/60) | 58% | 50.9 |
| hard | 28% (17/60) | 77% | 91.7 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 77% (23/30) | 30.5 | 34% | bucle |
| color-locks | 11 | 60% (18/30) | 54.0 | 56% | bucle |
| apartment-keys | 7 | 77% (23/30) | 47.8 | 61% | accion_invalida, bucle |
| library-search | 7 | 23% (7/30) | 82.4 | 66% | bucle |
| office-sequence | 13 | 33% (10/30) | 101.0 | 88% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 68 |
| accion_invalida | 1 |
