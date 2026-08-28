# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 250

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 84% (211/250) |
| eficiencia media (éxitos) | 0.46 |
| fracción de llamadas repetidas | 40% |
| pasos medios | 38.1 |
| llamadas al LLM medias | 38.0 |
| tokens entrada / salida | 163227 / 2071 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 15.6 s |
| latencia media | 35.5 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 98% (49/50) | 6% | 7.8 |
| medium | 82% (82/100) | 46% | 33.9 |
| hard | 80% (80/100) | 49% | 57.4 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 98% (49/50) | 7.8 | 6% | bucle |
| color-locks | 11 | 70% (35/50) | 46.1 | 48% | bucle |
| apartment-keys | 7 | 94% (47/50) | 21.6 | 45% | bucle |
| library-search | 7 | 86% (43/50) | 34.4 | 23% | bucle |
| office-sequence | 13 | 74% (37/50) | 80.3 | 76% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 39 |
