# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 100

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 76% (76/100) |
| eficiencia media (éxitos) | 0.48 |
| fracción de llamadas repetidas | 44% |
| pasos medios | 46.6 |
| llamadas al LLM medias | 43.1 |
| tokens entrada / salida | 203187 / 2426 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 16.9 s |
| latencia media | 41.0 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 68% (34/50) | 0.50 | 49% | 56.2 | 241028 |
| con_reflexion | 84% (42/50) | 0.47 | 38% | 37.0 | 165345 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 90% (18/20) | 10% | 14.1 |
| medium | 78% (31/40) | 48% | 37.4 |
| hard | 68% (27/40) | 56% | 72.0 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 90% (18/20) | 14.1 | 10% | bucle |
| color-locks | 11 | 75% (15/20) | 41.4 | 43% | bucle |
| apartment-keys | 7 | 80% (16/20) | 33.5 | 53% | bucle |
| library-search | 7 | 60% (12/20) | 63.0 | 36% | bucle |
| office-sequence | 13 | 75% (15/20) | 81.0 | 76% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 24 |
