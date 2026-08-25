# Resultados de la evaluación

Modelo: `bedrock:amazon.nova-lite-v1:0` · corridas: 100

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 70% (70/100) |
| eficiencia media (éxitos) | 0.46 |
| fracción de llamadas repetidas | 49% |
| pasos medios | 51.0 |
| llamadas al LLM medias | 48.8 |
| tokens entrada / salida | 196786 / 2814 |
| corridas descartadas (fallo de infraestructura) | 0 |
| latencia mediana | 17.3 s |
| latencia media | 45.8 s |

## Por condición

| condición | éxito | eficiencia | repetidas | pasos | tokens in |
|---|---|---|---|---|---|
| baseline | 70% (35/50) | 0.46 | 50% | 51.6 | 225734 |
| prompt_generico | 70% (35/50) | 0.47 | 48% | 50.4 | 167838 |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 95% (19/20) | 15% | 10.1 |
| medium | 65% (26/40) | 53% | 47.5 |
| hard | 62% (25/40) | 62% | 74.8 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 95% (19/20) | 10.1 | 15% | bucle |
| color-locks | 11 | 45% (9/20) | 64.8 | 58% | accion_invalida, bucle |
| apartment-keys | 7 | 85% (17/20) | 30.4 | 48% | bucle |
| library-search | 7 | 50% (10/20) | 61.2 | 43% | accion_invalida, bucle |
| office-sequence | 13 | 75% (15/20) | 88.5 | 80% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 28 |
| accion_invalida | 2 |
