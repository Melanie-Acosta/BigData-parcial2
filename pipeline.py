
import sqlite3
import duckdb
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_ORIGEN = BASE_DIR / "datos" / "clinica.sqlite"
DB_DESTINO = BASE_DIR / "clinica.duckdb"


#°Extraer los datos del origen.
def extraer_datos():
    print("EXTRACCION DE DATOS")

    conexion = sqlite3.connect(
        f"{DB_ORIGEN.as_uri()}?mode=ro",
        uri=True
    )
    try:
        df = pd.read_sql_query(
            "SELECT * FROM turnos",
            conexion
        )
    finally:
        conexion.close()
    print(f"Registros extraidos: {len(df)}")
    return df


#°Cargar los datos tal cual a una tabla de DuckDB: raw_turnos.
def cargar_raw(df):
    print("Cargando datos en duck.")

    conexion = duckdb.connect(str(DB_DESTINO))
    try:
        conexion.register("datos_extraidos", df)
        conexion.execute("""
            CREATE OR REPLACE TABLE raw_turnos AS
            SELECT * FROM datos_extraidos
        """)

        cantidad = conexion.execute("""
            SELECT COUNT(*) FROM raw_turnos
        """).fetchone()[0]
        print(f"Registros cargados en raw_turnos: {cantidad}")

    finally:
        conexion.close()
    print("Completado correctamente.")


#°Validar con reglas que defina el equipo (al menos 8 reglas distintas; cada una con su nombre).
def validar_datos(df):
    print("\nValidacion de Datos:")
    datos = df.copy().reset_index(drop=True)

    # ID_TURNO_UNICO
    id_turno = datos["id_turno"].astype("string").str.strip()
    regla_id = (
        id_turno.isna()
        | id_turno.eq("")
        | id_turno.duplicated(keep=False)
    )

    # PACIENTE_VALIDO
    paciente = pd.to_numeric(
        datos["id_paciente"],
        errors="coerce"
    )
    regla_paciente = paciente.isna() | (paciente <= 0)

    # ESPECIALIDAD_OBLIGATORIA
    especialidad = datos["especialidad"].astype("string").str.strip()
    regla_especialidad = (
        especialidad.isna()
        | especialidad.eq("")
    )

    # MEDICO_VALIDO
    id_medico = datos["id_medico"].astype("string").str.strip()
    medico = datos["medico"].astype("string").str.strip()
    regla_medico = (
        id_medico.isna()
        | id_medico.eq("")
        | medico.isna()
        | medico.eq("")
    )

    # OBRA_SOCIAL_VALIDA
    obra_social = datos["obra_social"].astype("string").str.strip()
    regla_obra_social = (
        obra_social.isna()
        | obra_social.eq("")
    )

    # ESTADO_VALIDO
    estados_validos = ["atendido", "ausente", "cancelado"]
    estado = datos["estado"].astype("string").str.strip().str.lower()
    regla_estado = ~estado.isin(estados_validos)

    # FECHA_VALIDA
    fechas = datos["fecha_turno"].astype("string").str.strip()
    fecha_iso = pd.to_datetime(
        fechas,
        format="%Y-%m-%d",
        errors="coerce"
    )
    fecha_dia_mes = pd.to_datetime(
        fechas,
        format="%d/%m/%Y",
        errors="coerce"
    )
    regla_fecha = fecha_iso.isna() & fecha_dia_mes.isna()

    # COSTO_VALIDO
    costo = pd.to_numeric(
        datos["costo"],
        errors="coerce"
    )
    regla_costo = costo.isna() | (costo < 0)

    # Fue rechazado por:
    reglas = {
        "ID_TURNO_UNICO": regla_id,
        "PACIENTE_VALIDO": regla_paciente,
        "ESPECIALIDAD_OBLIGATORIA": regla_especialidad,
        "MEDICO_VALIDO": regla_medico,
        "OBRA_SOCIAL_VALIDA": regla_obra_social,
        "ESTADO_VALIDO": regla_estado,
        "FECHA_VALIDA": regla_fecha,
        "COSTO_VALIDO": regla_costo
    }
    datos["motivo_rechazo"] = ""

    for nombre, condicion in reglas.items():
        datos.loc[condicion, "motivo_rechazo"] = (
            datos.loc[condicion, "motivo_rechazo"]
            .apply(
                lambda motivo: (
                    motivo + ", " + nombre
                    if motivo else nombre
                )
            )
        )

    validos = datos[
        datos["motivo_rechazo"] == ""
    ].drop(columns=["motivo_rechazo"])
    rechazados = datos[
        datos["motivo_rechazo"] != ""
    ]

    print(f"Validos: {len(validos)}")
    print(f"Rechazados: {len(rechazados)}")
    return validos, rechazados


#°Crear la tabla validos y la tabla rechazados (con una columna motivo_rechazo que diga por que se rechazo).
def guardar_validaciones(validos, rechazados):
    conexion = duckdb.connect(str(DB_DESTINO))
    try:
        conexion.register("datos_validos", validos)
        conexion.register("datos_rechazados", rechazados)
        conexion.execute("""
            CREATE OR REPLACE TABLE validos AS
            SELECT * FROM datos_validos
        """)
        conexion.execute("""
            CREATE OR REPLACE TABLE rechazados AS
            SELECT * FROM datos_rechazados
        """)

        print("Tablas validos y rechazados:")
    finally:
        conexion.close()


#°Limpiar los rechazados con pandas o SQL y guardarlos en rechazados_limpios.
def tabla_limpia_de_rechazados(rechazados, datos):
    print("LIMPIEZA DE RECHAZADOS")
    limpios = rechazados.drop(
        columns=["motivo_rechazo"]
    ).copy()

    #Eliminar copias del mismo turno
    limpios = limpios.drop_duplicates(
        subset=["id_turno"],
        keep="first"
    )

    #Recuperar nombres de medicos usando el ID
    medicos = datos[
        ["id_medico", "medico"]
    ].dropna().copy()

    medicos["id_medico"] = (
        medicos["id_medico"].astype("string").str.strip()
    )
    medicos["medico"] = (
        medicos["medico"].astype("string").str.strip()
    )
    medicos = medicos[medicos["medico"] != ""]

    nombres_medicos = medicos.groupby(
        "id_medico"
    )["medico"].agg(lambda x: x.unique().tolist())

    mapa_medicos = {
        id_medico: nombres[0]
        for id_medico, nombres in nombres_medicos.items()
        if len(nombres) == 1
    }

    limpios["id_medico"] = (
        limpios["id_medico"].astype("string").str.strip()
    )
    limpios["medico"] = (
        limpios["medico"].astype("string").str.strip()
    )
    limpios["medico"] = limpios["medico"].replace("", pd.NA)
    limpios["medico"] = limpios["medico"].fillna(
        limpios["id_medico"].map(mapa_medicos)
    )

    #Recuperar costos usando la especialidad
    costos = datos[
        ["especialidad", "costo"]
    ].copy()

    costos["especialidad_limpia"] = (
        costos["especialidad"]
        .astype("string")
        .str.strip()
        .str.lower()
    )
    costos["costo"] = pd.to_numeric(
        costos["costo"],
        errors="coerce"
    )
    costos = costos.dropna(
        subset=["especialidad_limpia", "costo"]
    )
    costos_por_especialidad = costos.groupby(
        "especialidad_limpia"
    )["costo"].agg(lambda x: x.unique().tolist())

    mapa_costos = {
        especialidad: valores[0]
        for especialidad, valores in costos_por_especialidad.items()
        if len(valores) == 1
    }
    limpios["costo"] = pd.to_numeric(
        limpios["costo"],
        errors="coerce"
    )
    especialidades = (
        limpios["especialidad"]
        .astype("string")
        .str.strip()
        .str.lower()
    )
    limpios["costo"] = limpios["costo"].fillna(
        especialidades.map(mapa_costos)
    )

    # Normalizar fechas
    fechas = limpios["fecha_turno"].astype("string").str.strip()
    fecha_iso = pd.to_datetime(
        fechas,
        format="%Y-%m-%d",
        errors="coerce"
    )
    fecha_dia_mes = pd.to_datetime(
        fechas,
        format="%d/%m/%Y",
        errors="coerce"
    )
    limpios["fecha_turno"] = fecha_iso.fillna(fecha_dia_mes)

    # Normalizar textos
    limpios["estado"] = (
        limpios["estado"].astype("string").str.strip().str.lower()
    )
    limpios["especialidad"] = (
        limpios["especialidad"].astype("string").str.strip()
    )
    limpios["obra_social"] = (
        limpios["obra_social"].astype("string").str.strip()
    )

    # Comprobar las reglas
    recuperados, no_recuperados = validar_datos(limpios)

    # Guardar registros recuperados
    conexion = duckdb.connect(str(DB_DESTINO))
    try:
        conexion.register("datos_limpios", recuperados)

        conexion.execute("""
            CREATE OR REPLACE TABLE rechazados_limpios AS
            SELECT * FROM datos_limpios
        """)
    finally:
        conexion.close()

    print(f"Registros recuperados: {len(recuperados)}")
    print(f"Registros no recuperables: {len(no_recuperados)}")


#°Unir en tabla_final (sin duplicados, tipos correctos).
def crear_tabla_final():
    print("Creacion de la tabla final:")

    conexion = duckdb.connect(str(DB_DESTINO))
    try:
        conexion.execute("""
            CREATE OR REPLACE TABLE tabla_final AS
            WITH registros AS (
                SELECT
                    CAST(id_turno AS VARCHAR) AS id_turno,
                    CAST(fecha_turno AS VARCHAR) AS fecha_turno,
                    CAST(id_paciente AS VARCHAR) AS id_paciente,
                    CAST(edad AS VARCHAR) AS edad,
                    CAST(especialidad AS VARCHAR) AS especialidad,
                    CAST(id_medico AS VARCHAR) AS id_medico,
                    CAST(medico AS VARCHAR) AS medico,
                    CAST(obra_social AS VARCHAR) AS obra_social,
                    CAST(costo AS VARCHAR) AS costo,
                    CAST(estado AS VARCHAR) AS estado
                FROM validos
                UNION ALL
                SELECT
                    CAST(id_turno AS VARCHAR),
                    CAST(fecha_turno AS VARCHAR),
                    CAST(id_paciente AS VARCHAR),
                    CAST(edad AS VARCHAR),
                    CAST(especialidad AS VARCHAR),
                    CAST(id_medico AS VARCHAR),
                    CAST(medico AS VARCHAR),
                    CAST(obra_social AS VARCHAR),
                    CAST(costo AS VARCHAR),
                    CAST(estado AS VARCHAR)
                FROM rechazados_limpios
            )
            SELECT
                id_turno,
                COALESCE(
                    TRY_CAST(fecha_turno AS DATE),
                    CAST(
                        TRY_STRPTIME(fecha_turno, '%d/%m/%Y')
                        AS DATE
                    )
                ) AS fecha_turno,
                TRY_CAST(id_paciente AS BIGINT) AS id_paciente,
                TRY_CAST(edad AS INTEGER) AS edad,
                especialidad,
                id_medico,
                medico,
                obra_social,
                TRY_CAST(costo AS DECIMAL(12,2)) AS costo,
                estado
            FROM registros
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY id_turno
                ORDER BY id_turno
            ) = 1
        """)

        cantidad = conexion.execute("""
            SELECT COUNT(*) FROM tabla_final
        """).fetchone()[0]

        print(f"Registros en tabla_final: {cantidad}")
        print("Tabla final creada correctamente.")
    finally:
        conexion.close()

if __name__ == "__main__":
    datos = extraer_datos()
    cargar_raw(datos)
    validos, rechazados = validar_datos(datos)
    guardar_validaciones(validos, rechazados)
    tabla_limpia_de_rechazados(rechazados, datos)
    crear_tabla_final()
    print("Pipeline finalizado.")
        

