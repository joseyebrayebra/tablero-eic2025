# Inventario de variables – EIC 2025

Fuente: descriptor de la base de datos de INEGI (`data/raw/docs/eic2025_micro_fd.xlsx`), tabulado completo con
todas las categorías en `docs/diccionario_eic2025.csv`. Los nombres de columnas se verificaron contra los CSV.

En todas las variables, "Nulo" significa blanco por pase (la pregunta no aplica a ese registro).

## Archivos en data/raw

| Archivo | Tamaño | Registros | Columnas |
|---|---|---|---|
| `eic2025/personas11.csv` (Guanajuato) | 181.7 MB | 796,597 | 92 |
| `eic2025/viviendas11.csv` (Guanajuato) | 46.2 MB | 223,876 | 87 |
| `eic2025/migrantes11.csv` (Guanajuato) | 2.1 MB | 17,670 | 27 |
| `eic2025/ent01/personas01.csv` (Aguascalientes) | 40.7 MB | 177,984 | 92 |
| `eic2025/ent01/viviendas01.csv` (Aguascalientes) | 10.0 MB | 48,538 | 87 |
| `eic2025/ent01/migrantes01.csv` (Aguascalientes) | 0.6 MB | 5,060 | 27 |
| `eic2025/ent14/personas14.csv` (Jalisco) | 310.0 MB | 1,355,591 | 92 |
| `eic2025/ent14/viviendas14.csv` (Jalisco) | 83.8 MB | 407,180 | 87 |
| `eic2025/ent14/migrantes14.csv` (Jalisco) | 2.2 MB | 18,778 | 27 |
| `eic2025/ent16/personas16.csv` (Michoacán) | 292.8 MB | 1,285,076 | 92 |
| `eic2025/ent16/viviendas16.csv` (Michoacán) | 77.0 MB | 372,592 | 87 |
| `eic2025/ent16/migrantes16.csv` (Michoacán) | 3.2 MB | 27,655 | 27 |
| `eic2025/ent22/personas22.csv` (Querétaro) | 73.1 MB | 318,757 | 92 |
| `eic2025/ent22/viviendas22.csv` (Querétaro) | 19.3 MB | 93,233 | 87 |
| `eic2025/ent22/migrantes22.csv` (Querétaro) | 0.8 MB | 6,612 | 27 |
| `eic2025/ent24/personas24.csv` (San Luis Potosí) | 156.6 MB | 686,573 | 92 |
| `eic2025/ent24/viviendas24.csv` (San Luis Potosí) | 41.0 MB | 198,608 | 87 |
| `eic2025/ent24/migrantes24.csv` (San Luis Potosí) | 1.4 MB | 11,968 | 27 |

Registros y columnas contados sobre el Parquet, cuya conversión verifica que coincidan con el CSV.

Otros insumos:

- `eic2025/eic2025_micro_NN_csv.zip`: los ZIP originales de los cinco estados pares (5 a 41 MB cada uno).
- `docs/`: descriptor, clasificaciones (XLSX y CSV), diseño de la muestra, cuestionario, municipios nuevos, notas de Stata (5.8 MB).
- `mg2025/`: Marco Geoestadístico de la EIC 2025, Guanajuato (126 MB) e integrado nacional (261 MB).
- `cpv2020/`: vacío.
- Archivo nacional de microdatos: no está en `data/raw`; la descarga en `~/Downloads` quedó incompleta.

## Geografía

Las mismas cinco variables están en las tres tablas.

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `CVEGEO` | personas | Clave geoestadística integrada | 01001..32058 | — |
| `CVE_ENT` | personas | Entidad federativa | 01..32 | — |
| `CVE_MUN` | personas | Municipio o demarcación territorial | 001..570 | — |
| `LOC50K` | personas | Clave de la localidad de 50 000 y más habitantes | 0000..9999 | — |
| `TAMLOC` | personas | Tamaño de localidad | 1..5 | — |

## Diseño muestral y llaves

Presentes en las tres tablas (TIPO_REG solo en personas y viviendas).

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `FACTOR` | personas | Factor de Expansión | 1..99999 | — |
| `ESTRATO` | personas | Estrato | Alfanumérico | — |
| `UPM` | personas | Unidad Primaria de Muestreo | Alfanumérico | — |
| `COBERTURA` | personas | Tipo de cobertura en el municipio | 1..3 | — |
| `TIPO_REG` | personas | Registro imputado | 0, 1 | — |
| `ID_VIV` | personas | Identificador único de la vivienda | 010010000001..320589999999 | — |
| `ID_PERSONA` | personas | Identificador único de persona | 01001000000100001.. 32058999999999954 | — |
| `ID_MII` | migrantes | Identificador único de migrante | 01001000000101.. 32058999999999 | — |

## Demografía

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `NUMPER` | personas | Número de persona | 01..54 | — |
| `SEXO` | personas | Sexo | 1, 3 | — |
| `EDAD` | personas | Edad | 0..130, 999 | 999 |
| `PARENTESCO` | personas | Parentesco | 101..701, 999 | 999 |
| `SITUA_CONYUGAL` | personas | Situación conyugal | 01..09, 99, nulo | 99 |
| `IDENT_MADRE` | personas | Identificación de la madre | 01..54, 96..99 | 99 |
| `IDENT_PADRE` | personas | Identificación del padre | 01..54, 96..99 | 99 |
| `IDENT_PAREJA` | personas | Identificación de la pareja | 01..54, 96, 99, nulo | 99 |
| `ENT_PAIS_NAC` | personas | Entidad o país de nacimiento | 001..032, 100..536, 997..999 | 997, 998, 999 |
| `NACIONALIDAD` | personas | Nacionalidad mexicana | 1, 3, 9 | 9 |
| `NUMPERS` | viviendas | Número de personas en la vivienda | 1..54 | — |
| `JEFE_SEXO` | viviendas | Sexo de la persona de referencia (jefa o jefe de la vivienda) | 1, 3 | — |
| `JEFE_EDAD` | viviendas | Edad de la persona de referencia (jefa o jefe de la vivienda) | 12..130, 999 | 999 |
| `TIPOHOG` | viviendas | Tipo de hogar | 1..6, 9 | 9 |

## Educación

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `ASISTEN` | personas | Asistencia escolar | 1, 3, 9, nulo | 9 |
| `MUN_ASI` | personas | Municipio de asistencia escolar | 001..570, 999, nulo | 999 |
| `ENT_PAIS_ASI` | personas | Entidad o país de asistencia escolar | 001..032, 100..536, 997..999 | 997, 998, 999 |
| `TIE_TRASLADO_ESCU` | personas | Tiempo de traslado a la escuela | 1..6, 9, nulo | 9 |
| `MED_TRASLADO_ESC1` | personas | Modo o medio de traslado a la escuela (opción 1) | 01..12, 99, nulo | 99 |
| `MED_TRASLADO_ESC2` | personas | Modo o medio de traslado a la escuela (opción 2) | 02..12, nulo | — |
| `MED_TRASLADO_ESC3` | personas | Modo o medio de traslado a la escuela (opción 3) | 03..12, nulo | — |
| `NIVACAD` | personas | Nivel (Escolaridad) | 00..14, 99, nulo | 99 |
| `ESCOLARI` | personas | Grado (Escolaridad) | 00..08, 99, nulo | 99 |
| `ESCOACUM` | personas | Escolaridad acumulada | 0..24, 99, nulo | 99 |
| `ALFABET` | personas | Alfabetismo | 1, 3, 9, nulo | 9 |

## Condición de actividad y trabajo

Se pregunta a la población de 12 años y más.

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `CONACT` | personas | Condición de actividad (con rescate por verificación de actividad) | 10, 13..20, 30, 40, 50, 60, 70, 80, 99, nulo | 99 |
| `OCUPACION_C` | personas | Ocupación - Clave | 111..989, 999, nulo | 999 |
| `SITTRA` | personas | Posición en el trabajo | 1..6, 9, nulo | 9 |
| `ACTIVIDADES_C` | personas | Sector de actividad económica - Clave | 1110..9399, 9999, nulo | 9999 |
| `HORTRA` | personas | Horas trabajadas | 0..140, 999, nulo | 999 |
| `INGTRMEN` | personas | Ingresos por trabajo mensualizado | 0..999998, 999999, nulo | 999999 |
| `SM` | personas | Ingresos por trabajo medido en salarios mínimos | 01..12, 99, nulo | 99 |
| `AGUINALDO` | personas | Aguinaldo (Prestaciones laborales) | 1, 2, 9, nulo | 9 |
| `VACACIONES` | personas | Vacaciones con goce de sueldo (Prestaciones laborales) | 3, 4, 9, nulo | 9 |
| `SERVICIO_MEDICO` | personas | Servicio médico (Prestaciones laborales) | 5, 6, 9, nulo | 9 |
| `UTILIDADES` | personas | Reparto de utilidades (Prestaciones laborales) | 7..9, nulo | 9 |
| `INCAP_SUELDO` | personas | Licencia o incapacidad con goce de sueldo (Prestaciones laborales) | 1, 2, 9, nulo | 9 |
| `SAR_AFORE` | personas | Ahorro para el retiro (Prestaciones laborales) | 3, 4, 9, nulo | 9 |
| `CREDITO_VIVIENDA` | personas | Crédito para la vivienda (Prestaciones laborales) | 5, 6, 9, nulo | 9 |
| `MUN_TRAB` | personas | Municipio de trabajo | 001..570, 999, nulo | 999 |
| `ENT_PAIS_TRAB` | personas | Entidad o país de trabajo | 001..032, 100..536, 997..999 | 997, 998, 999 |
| `TIE_TRASLADO_TRAB` | personas | Tiempo de traslado al trabajo | 1..7, 9, nulo | 9 |
| `MED_TRASLADO_TRAB1` | personas | Modo o medio de traslado al trabajo (opción 1) | 01..12, 99, nulo | 99 |
| `MED_TRASLADO_TRAB2` | personas | Modo o medio de traslado al trabajo (opción 2) | 02..12, nulo | — |
| `MED_TRASLADO_TRAB3` | personas | Modo o medio de traslado al trabajo (opción 3) | 03..12, nulo | — |
| `INGTRHOG` | viviendas | Ingresos por trabajo en el hogar | 0..999999, nulo | 999999 |

## Etnicidad

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `PERTE_INDIGENA` | personas | Autoadscripción indígena | 1, 3, 9 | 9 |
| `AFRODES` | personas | Afrodescendientes o Afromexicanos | 1, 3, 9 | 9 |
| `HLENGUA` | personas | Habla lengua indígena | 1, 3, 9, nulo | 9 |
| `QDIALECT_INALI` | personas | Lengua indígena - Clave | 0101..9030, 9999, nulo | 9999 |
| `HESPANOL` | personas | Habla español | 1, 3, 9, nulo | 9 |
| `ELENGUA` | personas | Comprensión de lengua indígena | 5, 7, 9, nulo | 9 |

## Discapacidad

En DIS_VER a DIS_HABLAR: 1 sin dificultad, 2 poca, 3 mucha, 4 no puede.

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `DIS_VER` | personas | Dificultad para ver aun usando lentes | 1..4, 8, 9 | 8, 9 |
| `DIS_OIR` | personas | Dificultad para oír aun usando aparato auditivo | 1..4, 8, 9 | 8, 9 |
| `DIS_CAMINAR` | personas | Dificultad para caminar, subir o bajar | 1..4, 8, 9 | 8, 9 |
| `DIS_RECORDAR` | personas | Dificultad para recordar o concentrarse | 1..4, 8, 9 | 8, 9 |
| `DIS_BANARSE` | personas | Dificultad para bañarse, vestirse o comer | 1..4, 8, 9 | 8, 9 |
| `DIS_HABLAR` | personas | Dificultad para hablar o comunicarse | 1..4, 8, 9 | 8, 9 |
| `DIS_MENTAL` | personas | Problema o condición mental | 5, 6, 9 | 9 |
| `CAU_VER` | personas | Causa de la dificultad para ver aun usando lentes | 1..5, 9, nulo | 9 |
| `CAU_OIR` | personas | Causa de la dificultad para oír aun usando aparato auditivo | 1..5, 9, nulo | 9 |
| `CAU_CAMINAR` | personas | Causa de la dificultad para caminar, subir o bajar | 1..5, 9, nulo | 9 |
| `CAU_RECORDAR` | personas | Causa de la dificultad para recordar o concentrarse | 1..5, 9, nulo | 9 |
| `CAU_BANARSE` | personas | Causa de la dificultad para bañarse, vestirse o comer | 1..5, 9, nulo | 9 |
| `CAU_HABLAR` | personas | Causa de la dificultad para hablar o comunicarse | 1..5, 9, nulo | 9 |
| `CAU_MENTAL` | personas | Causa del problema o condición mental | 1..5, 9, nulo | 9 |
| `COND_MENTAL_C` | personas | Problema o condición mental - Clave | 101..401, 999, nulo | 999 |
| `COND_MENTAL_G` | personas | Problema o condición mental - Grupo | 1..4, 9, nulo | — |

## Fecundidad y mortalidad

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `HIJOS_NAC_VIVOS` | personas | Hijas(os) nacidas(os) vivas(os) | 0..25, 98, 99, nulo | 98, 99 |
| `HIJOS_FALLECIDOS` | personas | Hijas(os) fallecidas(os) | 0..25, 99, nulo | 99 |
| `HIJOS_SOBREVIV` | personas | Hijas(os) sobrevivientes | 0..25, 99, nulo | 99 |
| `FECHA_NAC_M` | personas | Fecha de nacimiento (mes) | 01..12, 99, nulo | 99 |
| `FECHA_NAC_A` | personas | Fecha de nacimiento (año) | 1925..2025, 9999, nulo | 9999 |
| `SOBREVIVENCIA` | personas | Sobrevivencia | 1, 3, 9, nulo | 9 |
| `EDAD_MORIR_D` | personas | Edad al morir (días) | 0..29, 98, 99, nulo | 99 |
| `EDAD_MORIR_M` | personas | Edad al morir (meses) | 1..11, 98, nulo | — |
| `EDAD_MORIR_A` | personas | Edad al morir (años) | 1..99, nulo | — |

## Migración interna (personas)

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `ENT_PAIS_RES_5A` | personas | Entidad o país de residencia en octubre de 2020 | 001..032, 100..536, 997..999 | 997, 998, 999 |
| `MUN_RES_5A` | personas | Municipio de residencia en octubre de 2020 | 001..570, 999, nulo | 999 |
| `CAUSA_MIG_C` | personas | Causa de la migración (otra causa) | 0101..0902, 9999, nulo | 9999 |

## Migración internacional (viviendas y tabla de migrantes)

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `MCONMIG` | viviendas | Condición de migración internacional | 1, 3, 9 | 9 |
| `MNUMPERS` | viviendas | Número de emigrantes internacionales | 1..54, nulo | — |
| `MPER` | migrantes | Lista de emigrantes internacionales | 01..54 | — |
| `MCONRES` | migrantes | Condición de residencia | 1 | — |
| `MSEXO` | migrantes | Sexo del migrante | 1, 3 | — |
| `MEDAD` | migrantes | Edad al migrar | 0..130, 999 | 999 |
| `MFECEMIM` | migrantes | Fecha de la emigración (mes) | 01..12, 99 | 99 |
| `MFECEMIA` | migrantes | Fecha de la emigración (año) | 2020..2025, 9999 | 9999 |
| `MCAUSAEMIG_V` | migrantes | Causa de la emigración - Clave | 0101..0902, 9999 | 9999 |
| `MLUGORI_C` | migrantes | Lugar de origen (otro estado) - Clave | 001..032, 999 | 999 |
| `MPAIDES_C` | migrantes | País de destino (otro país) - Clave | 001..032, 999 | 999 |
| `MPAIRES` | migrantes | País de residencia | 1..3, 9 | 9 |
| `MFECRETM` | migrantes | Fecha de retorno (mes) | 01..12, 99, nulo | 99 |
| `MFECRETA` | migrantes | Fecha de retorno (año) | 2020..2025, 9999, nulo | 9999 |
| `MCAUSARETO_V` | migrantes | Causa del retorno - Clave | 0101..0902, 9999, nulo | 9999 |
| `MCONRESACT` | migrantes | Condición de residencia actual | 1, 3, 9, nulo | 9 |
| `MPERLS` | migrantes | Identificación del migrante en la lista de personas | 01..54, 99, nulo | 99 |

## Vivienda y hogar: TIC y bienes

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `REFRIGERADOR` | viviendas | Refrigerador (Bienes y TIC) | 1, 2, 9, nulo | 9 |
| `LAVADORA` | viviendas | Lavadora (Bienes y TIC) | 3, 4, 9, nulo | 9 |
| `HORNO` | viviendas | Horno de microondas (Bienes y TIC) | 5, 6, 9, nulo | 9 |
| `AUTOPROP` | viviendas | Automóvil o camioneta (Bienes y TIC) | 7..9, nulo | 9 |
| `MOTOCICLETA` | viviendas | Motocicleta o motoneta (Bienes y TIC) | 1, 2, 9, nulo | 9 |
| `BICICLETA` | viviendas | Bicicleta como medio de transporte (Bienes y TIC) | 3, 4, 9, nulo | 9 |
| `RADIO` | viviendas | Radio (Bienes y TIC) | 5, 6, 9, nulo | 9 |
| `TELEVISOR` | viviendas | Televisor (Bienes y TIC) | 7..9, nulo | 9 |
| `COMPUTADORA` | viviendas | Computadora, laptop o tablet (Bienes y TIC) | 1, 2, 9, nulo | 9 |
| `TELEFONO` | viviendas | Línea telefónica fija (Bienes y TIC) | 3, 4, 9, nulo | 9 |
| `CELULAR` | viviendas | Teléfono celular (Bienes y TIC) | 5, 6, 9, nulo | 9 |
| `INTERNET` | viviendas | Internet (Bienes y TIC) | 7..9, nulo | 9 |
| `SERV_TV_PAGA` | viviendas | Servicio de televisión de paga (Bienes y TIC) | 1, 2, 9, nulo | 9 |

## Vivienda y hogar: servicios

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `ELECTRICIDAD` | viviendas | Electricidad | 1, 3, 9, nulo | 9 |
| `AGUA_ENTUBADA` | viviendas | Agua entubada | 1..3, 9, nulo | 9 |
| `ABA_AGUA_ENTU` | viviendas | Abastecimiento de agua | 1..7, 9, nulo | 9 |
| `ABA_AGUA_NO_ENTU` | viviendas | Agua no entubada | 1..6, 9, nulo | 9 |
| `SERSAN` | viviendas | Sanitario | 1..3, 9, nulo | 9 |
| `CONAGUA` | viviendas | Admisión de agua en el sanitario | 1..3, 9, nulo | 9 |
| `DRENAJE` | viviendas | Drenaje | 1..5, 9, nulo | 9 |
| `COMBUSTIBLE` | viviendas | Combustible | 1..5, 9, nulo | 9 |
| `DESTINO_BAS` | viviendas | Eliminación de basura | 1..6, 9, nulo | 9 |
| `SEPARACION1` | viviendas | Separación de basura orgánica e inorgánica | 1, 2, 9, nulo | 9 |
| `SEPARACION2` | viviendas | Separación de desperdicios para alimentar animales | 3, 4, 9, nulo | 9 |
| `SEPARACION3` | viviendas | Separación de desperdicios para echarlos a las plantas | 5, 6, 9, nulo | 9 |
| `SEPARACION4` | viviendas | Separación de desperdicios para vender, regalar, donar o reutilizar | 7..9, nulo | 9 |

## Vivienda y hogar: alimentación

Variables de hogar: se analizan como hogares.

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `ALIMENTACION` | viviendas | Acceso a los alimentos en la vivienda | 1, 3, 9 | 9 |
| `ALIM_ADL1` | viviendas | Tuvieron poca variedad de alimentos (Alimentación de los adultos) | 1, 2, 9 | 9 |
| `ALIM_ADL2` | viviendas | Dejaron de desayunar, comer o cenar (Alimentación de los adultos) | 3, 4, 9 | 9 |
| `ALIM_ADL3` | viviendas | Comieron menos de lo que usted piensa debían comer (Alimentación de los adultos) | 5, 6, 9 | 9 |
| `ING_ALIM_ADL1` | viviendas | Sintieron hambre pero no comieron (Ingesta de alimentos de los adultos) | 1, 2, 9, nulo | 9 |
| `ING_ALIM_ADL2` | viviendas | Solo comieron una vez al día o dejaron de comer todo un día (Ingesta de alimentos de los adultos) | 3, 4, 9, nulo | 9 |
| `ALIM_MEN1` | viviendas | Tuvo poca variedad de alimentos (Alimentación de los menores de 18 años) | 1, 2, 9, nulo | 9 |
| `ALIM_MEN2` | viviendas | Comió menos (Alimentación de los menores de 18 años) | 3, 4, 9, nulo | 9 |
| `ALIM_MEN3` | viviendas | Disminuyó la cantidad de comida (Alimentación de los menores de 18 años) | 5, 6, 9, nulo | 9 |
| `ING_ALIM_MEN1` | viviendas | Sintió hambre pero no comió (Ingesta de alimentos de los menores de 18 años) | 1, 2, 9, nulo | 9 |
| `ING_ALIM_MEN2` | viviendas | Se acostó con hambre (Ingesta de alimentos de los menores de 18 años) | 3, 4, 9, nulo | 9 |
| `ING_ALIM_MEN3` | viviendas | Comió solo una vez o dejó de comer (Ingesta de alimentos de los menores de 18 años) | 5, 6, 9, nulo | 9 |

## Vivienda y hogar: ingresos no laborales

Variables de hogar: se analizan como hogares.

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `INGR_PEROTROPAIS` | viviendas | Reciben ingresos de alguien que vive en otro país (Otros ingresos) | 1, 2, 9 | 9 |
| `INGR_PERDENTPAIS` | viviendas | Reciben ingresos de alguien que vive en otra vivienda dentro del país (Otros ingresos) | 3, 4, 9 | 9 |
| `INGR_AYUGOB` | viviendas | Reciben ingresos de programas de gobierno (Otros ingresos) | 5, 6, 9 | 9 |
| `INGR_JUBPEN` | viviendas | Reciben ingreso por jubilación o pensión (Otros ingresos) | 7..9 | 9 |

## Vivienda y hogar: desplazamiento forzado interno

Variables de hogar: se analizan como hogares.

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `DESP_INSEGURIDAD` | viviendas | Desplazamiento forzado interno por inseguridad | 1, 2, 9 | 9 |
| `DESP_CATASTROFES` | viviendas | Desplazamiento forzado interno por catástrofes | 3, 4, 9 | 9 |

## Vivienda y hogar: materiales, espacios, equipamiento y tenencia

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `CLAVIVP` | viviendas | Clase de vivienda particular | 01..09, 99 | 99 |
| `PAREDES` | viviendas | Paredes | 1..8, 9, nulo | 9 |
| `TECHOS` | viviendas | Techos | 01..10, 99, nulo | 99 |
| `PISOS` | viviendas | Pisos | 1..3, 9, nulo | 9 |
| `COCINA` | viviendas | Cocina | 1, 3, 9, nulo | 9 |
| `CUADORM` | viviendas | Dormitorios | 1..25, 99, nulo | 99 |
| `TOTCUART` | viviendas | Cuartos | 1..25, 99, nulo | 99 |
| `LUG_COC` | viviendas | Lugar donde cocinan | 1..6, 9, nulo | 9 |
| `ESTUFA` | viviendas | Fogón con chimenea | 1, 3, 9, nulo | 9 |
| `TINACO` | viviendas | Tinaco (Equipamiento) | 1, 2, 9, nulo | 9 |
| `CISTERNA` | viviendas | Cisterna o aljibe (Equipamiento) | 3, 4, 9, nulo | 9 |
| `BOMBA_AGUA` | viviendas | Bomba de agua (Equipamiento) | 5, 6, 9, nulo | 9 |
| `REGADERA` | viviendas | Regadera (Equipamiento) | 7..9, nulo | 9 |
| `BOILER` | viviendas | Boiler o calentador de agua (Equipamiento) | 1, 2, 9, nulo | 9 |
| `CALENTADOR_SOLAR` | viviendas | Calentador solar de agua (Equipamiento) | 3, 4, 9, nulo | 9 |
| `AIRE_ACON` | viviendas | Aire acondicionado (Equipamiento) | 5, 6, 9, nulo | 9 |
| `PANEL_SOLAR` | viviendas | Panel solar para tener electricidad (Equipamiento) | 7..9, nulo | 9 |
| `TENENCIA` | viviendas | Tenencia | 1..6, 9, nulo | 9 |
| `ESCRITURAS` | viviendas | Escritura o título | 1..3, 8, 9, nulo | 9 |
| `FORMA_ADQUI` | viviendas | Adquisición | 1..6, 9, nulo | 9 |
| `FINANCIAMIENTO1` | viviendas | Financiamiento (opción 1) | 1..8, 9, nulo | 9 |
| `FINANCIAMIENTO2` | viviendas | Financiamiento (opción 2) | 2..8, nulo | — |
| `FINANCIAMIENTO3` | viviendas | Financiamiento (opción 3) | 3..8, nulo | — |
| `DUE1_NUM` | viviendas | Número de la primera persona dueña o propietaria | 01..54, 98, 99, nulo | 99 |
| `DUE2_NUM` | viviendas | Número de la segunda persona dueña o propietaria | 02..54, nulo | — |

## Salud (no solicitado, disponible)

| Variable | Tabla | Descripción | Valores válidos | No especificado |
|---|---|---|---|---|
| `SERSALUD` | personas | Uso de servicios de salud | 01..10, 99 | 99 |
| `DHSERSAL1` | personas | Afiliación o acceso a servicios de salud (opción 1) | 01..09, 99 | 99 |
| `DHSERSAL2` | personas | Afiliación a o acceso servicios de salud (opción 2) | 2..8, nulo | — |
| `DHSERSAL_ACCESO` | personas | Reconocimiento de acceso a servicios públicos de salud | 1, 3, 9, nulo | 9 |

## Lo que no se encontró

| Buscado | Resultado |
|---|---|
| Clave de localidad | No existe. Solo `LOC50K` identifica las localidades de 50 mil y más habitantes; el resto va como 0000. El tamaño de localidad sí está (`TAMLOC`) |
| AGEB o manzana | No existen en el microdato |
| Nivel y grado al que se asiste | No existe. La EIC solo pregunta si asiste (`ASISTEN`) y el último nivel y grado aprobado |
| Tipo de escuela (pública o privada) | No existe |
| Causa de no asistencia o de abandono escolar | No existe |
| Carrera o campo de formación | No existe |
| Antecedente escolar como variable separada | No existe; va implícito en los códigos de `NIVACAD` (06 a 09) |
| Total de UPM por estrato (para corrección por población finita) | No existe |
| Ingresos no laborales en monto | No existen; solo condición sí/no por fuente (`INGR_*`) |
| Desplazamiento a nivel persona | No existe; solo a nivel vivienda (`DESP_*`) |
| Identificador de hogar distinto de la vivienda | No existe; `TIPOHOG` e `INGTRHOG` vienen una fila por vivienda |

## Notas sobre "no especificado"

- Convención general: 9, 99, 999 o 9999 según la longitud del campo.
- `ENT_PAIS_*`: 997 = no especificado de entidad, 998 = de país, 999 = no especificado.
- `DIS_*` (dificultad): 8 = se desconoce el grado de la dificultad, 9 = no especificado.
- `HIJOS_NAC_VIVOS`: 98 = no especificado por omisión en todas las preguntas del tema; 99 = no especificado.
- `INGTRMEN` e `INGTRHOG`: 999999 = no especificado; 999998 = ingresos mayores a 999,997.
- `IDENT_MADRE`, `IDENT_PADRE`: 96 = vive en otra vivienda, 97 = ya falleció, 98 = no sabe, 99 = no especificado.
- `DUE1_NUM`: 98 = no vive en esta vivienda (no es "no especificado"); `EDAD_MORIR_D`: 98 = murió con menos de un mes.
- `SEXO`, `FACTOR`, `ESTRATO`, `UPM`, `TAMLOC` y la geografía no tienen "no especificado".
