# Traducciones y datos educativos — Fase 6

Fecha: 2026-11-14 · Rama `experimental/zoonauta-v6-modern-web`.
**No se ha cambiado ningún dato ni ninguna traducción**: esta fase añade validación
automática y prepara la revisión humana en ambos idiomas.

## Validación automática

```bash
python -m codigo.nucleo.validar_catalogo            # catálogo ampliado
python -m codigo.nucleo.validar_textos_interfaz     # textos de interfaz 5.0 y 6.0
python -m unittest tests.test_validacion_contenido  # ambos, como prueba
```

### Catálogo ampliado (`validar_catalogo`): correcto, 0 errores

| Comprobación | Resultado |
|---|---|
| IDs únicos y con formato | 288 animales (A01–A48, N001–N240), 48 hábitats, 144 pistas, 402 pictogramas |
| Referencias entre archivos | todas existen: pictogramas, hábitat de referencia, secundarios, contrastes, afines, pistas |
| Recursos | todas las imágenes de pictogramas y paisajes están presentes |
| Pistas por hábitat | niveles 1, 2 y 3 en los 48 hábitats |
| Secundarios | 31, todos con fuente verificable (URL) y distintos del hábitat de referencia |
| Contrastes | ninguno coincide con un hábitat válido del animal |
| Traducciones por ID | 940 pares es / pt-BR completos y con las mismas variables |
| Variedad | ninguna forma de España (es-ES) ni de Portugal (pt-PT) detectada |

**Avisos para revisión humana (35, no bloquean):**

- 29 textos idénticos en ambos idiomas (Guepardo, Morsa, Alce, Guanaco, Orca, Cachalote,
  Dugongo, Tundra, Coníferas, Arbustos…). En una primera lectura parecen correctos en
  pt-BR; excepción: «Algas altas» (`P_R54`), poco natural en pt-BR.
- 6 nombres científicos con una nota dentro del mismo campo (p. ej. «Panthera uncia
  (fuente histórica: Uncia uncia)»). La información es correcta; conviene separar el
  nombre y la nota en el futuro (cambio de datos: requiere decisión).

### Interfaz (`validar_textos_interfaz`): correcto

94 textos traducidos que usan el frontend 6.0 y el de 5.0: todos tienen traducción pt-BR
con las mismas variables, salvo **6 borradores nuevos de la 6.0** pendientes de revisión
(«Reducir movimiento», textos del carrusel y de movimiento reducido), que viven en
`TEXTOS_NUEVOS_PENDIENTES` (`frontend/src/i18n.ts`) hasta que se aprueben y pasen a
`datos/traducciones_pt_BR.json`.

Límite: las pantallas de carga y de error de conexión de la 6.0 se muestran en español
porque aparecen antes de saber el idioma de la sesión.

### Herramientas evaluadas y no incorporadas

- **pydantic / JSON Schema**: los validadores usan solo la biblioteca estándar, así
  que no añaden dependencias al juego (que se abre sin instalar nada). Comprueban
  además relaciones entre archivos que un esquema por archivo no expresa.
- **i18next / FormatJS**: el sistema actual (texto en español como clave, diccionario
  pt-BR servido por Python) cubre las necesidades y lo comparten 5.0 y 6.0. Migrarlo
  añadiría riesgo sin beneficio inmediato.
- **LibreTranslate / Argos / Weblate**: no se generaron traducciones automáticas. Si la
  revisión necesita colaboradores, Weblate podría usar la hoja CSV como punto de partida.

## Revisión humana: `revision_es_pt.csv`

1.226 filas con todo lo que el juego muestra o lee en voz alta, en UTF-8 (abre bien en
Excel o LibreOffice):

| Grupo | Filas | Qué es |
|---|---:|---|
| interfaz | 144 | botones, Preferencias, avisos (6 son borradores nuevos) |
| mensaje | 115 | mensajes de la guía y del sistema (incluye «Probar voz») |
| error | 27 | mensajes de error |
| animal | 288 | nombre común (la nota lleva el nombre científico) |
| contexto | 10 | contextos educativos de las confirmaciones |
| habitat / habitat_frase | 48 + 48 | nombre y frase que se lee al confirmar |
| pista | 144 | pistas de los 3 niveles |
| pictograma | 402 | etiqueta bajo cada pictograma |

Columnas para quien revisa: `revision_es`, `revision_pt_BR` (OK / cambiar),
`cambio_propuesto` y `observaciones`. `aviso_automatico` y `nota_preliminar` son de
apoyo: no son decisiones.

Criterios: lenguaje claro y breve para el público; tuteo en es-419 y «você» en pt-BR;
no simplificar conceptos científicos si cambia el significado; los contextos educativos
y las asociaciones biológicas requieren además revisión con fuente.

Para regenerar la hoja sin perder lo ya revisado:

```bash
python -m codigo.nucleo.hoja_revision_traducciones
```

Los cambios aprobados se aplican después por ID en los datos, con su prueba, y si un
texto leído en voz alta cambia, su grabación de ElevenLabs deja de usarse sola (se
busca por texto exacto) y hay que regrabarla.
