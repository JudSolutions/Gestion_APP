create database Gestion_Documental_AG;
USE Gestion_Documental_AG;

-- Tabla de usuarios (autenticaciòn)
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(120) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol ENUM('Administrador','Auxiliar','Lider','Analista','Jefe','Director') DEFAULT 'Auxiliar',
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Auxiliares (Para asignaciòn)
CREATE TABLE auxiliares (
    id_auxiliar INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    cedula VARCHAR(20),
    correo VARCHAR(120),
    hoja_excel VARCHAR (100), 		-- nombre de la hoja de cada auxiliar
    capacidad_hora DECIMAL(5,2),  	-- Folios que puede ejecutar por hora
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de tipologias documentales
CREATE TABLE tipologias (
    id_tipologia INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipologia VARCHAR(100),
    descripcion TEXT
);

-- Tabla de tareas principales (una fila por registro del Excel)
CREATE TABLE cuadro_control (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cedula VARCHAR(20) NOT NULL,
    apellidos_nombres VARCHAR(150) NOT NULL,
    tipologia_finca VARCHAR(150),
    folios INT,
    semana INT,
    fecha_publicacion DATE,
    fecha_indexacion DATE,
    ans_indexacion INT,
    fecha_ins_fisica DATE,
    ans_ins_fisica INT,
    finca VARCHAR(50),
    numero_tarea_wm VARCHAR(50),
    tipo VARCHAR(50),
    observacion TEXT,
    mes VARCHAR(20),               -- para identificar de qué hoja del libro viene (enero, febrero, etc.)
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Asignación de tareas por auxiliar
CREATE TABLE asignaciones (
    id_asignacion INT AUTO_INCREMENT PRIMARY KEY,
    id_control INT,
    id_auxiliar INT,
    fecha_asignacion DATE,
    estado ENUM('Pendiente','En proceso','Completada','Vencida') DEFAULT 'Pendiente',
    FOREIGN KEY (id_control) REFERENCES cuadro_control(id),
    FOREIGN KEY (id_auxiliar) REFERENCES auxiliares(id_auxiliar)
);

-- Tabla para notificaciones (Teams o correo)
CREATE TABLE notificaciones (
    id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_asignacion INT,
    tipo ENUM('Correo','Teams','Sistema'),
    mensaje TEXT,
    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('Pendiente','Enviada','Error') DEFAULT 'Pendiente',
    FOREIGN KEY (id_asignacion) REFERENCES asignaciones(id_asignacion)
);

-- Logs de sincronización
CREATE TABLE logs_sincronizacion (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    mes_excel VARCHAR(20),
    archivo_fuente VARCHAR(200),
    fecha_sincronizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    registros_actualizados INT,
    observaciones TEXT
);

-- Control de producción por auxiliar (alimentará los libros Excel de cada uno)
CREATE TABLE control_produccion (
    id_produccion INT AUTO_INCREMENT PRIMARY KEY,
    id_asignacion INT,
    fecha_ejecucion DATE,
    actividad VARCHAR(200),
    hora_inicio TIME,
    hora_fin TIME,
    resultado TEXT,
    FOREIGN KEY (id_asignacion) REFERENCES asignaciones(id_asignacion)
);

CREATE TABLE produccion_auxiliar (
    id SERIAL PRIMARY KEY,
    auxiliar VARCHAR(100) NOT NULL,
    fecha_produccion DATE NOT NULL,
    empresa VARCHAR(100),
    actividad TEXT,
    unidad_medida VARCHAR(50),
    hora_inicio TIME,
    hora_fin TIME,
    cantidad_ejecutada DECIMAL(10,2),
    porcentaje_cumplimiento DECIMAL(5,2),
    caja_mantis VARCHAR(20),
    observaciones TEXT,
    deber_ejecutar DECIMAL(10,2),
    horas_ejecutadas DECIMAL(10,2),
    estandar_h DECIMAL(10,2),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);