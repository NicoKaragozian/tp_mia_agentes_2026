# Resultados de la evaluación

Modelo: `ollama:llama3.1:8b` · corridas: 8

## Global

| métrica | valor |
|---|---|
| tasa de éxito | 25% (2/8) |
| eficiencia media (éxitos) | 0.45 |
| fracción de llamadas repetidas | 51% |
| pasos medios | 25.4 |
| llamadas al LLM medias | 23.6 |
| tokens entrada / salida | 41924 / 478 |
| latencia media | 35.8 s |

## Por dificultad

| dificultad | éxito | repetidas | pasos medios |
|---|---|---|---|
| easy | 100% (1/1) | 0% | 7.0 |
| medium | 50% (1/2) | 53% | 31.0 |
| hard | 0% (0/2) | 32% | 12.0 |
| extreme | 0% (0/3) | 79% | 36.7 |

## Por escenario

| escenario | óptimo | éxito | pasos medios | repetidas | modo de fallo principal |
|---|---|---|---|---|---|
| study-with-key | 3 | 100% (1/1) | 7.0 | 0% | — |
| color-locks | 11 | 100% (1/1) | 23.0 | 22% | — |
| apartment-keys | 7 | 0% (0/1) | 39.0 | 85% | bucle |
| library-search | 7 | 0% (0/1) | 22.0 | 64% | bucle |
| office-sequence | 13 | 0% (0/1) | 2.0 | 0% | tool_call_en_texto |
| extreme-archive | 4 | 0% (0/1) | 16.0 | 81% | bucle |
| vault-combination | 21 | 0% (0/1) | 50.0 | 88% | bucle |
| backtracking-vault | 18 | 0% (0/1) | 44.0 | 68% | bucle |

## Modos de fallo (categoría principal por corrida fallida)

| modo | corridas |
|---|---|
| bucle | 5 |
| tool_call_en_texto | 1 |
