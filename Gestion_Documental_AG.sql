CREATE TABLE actividades_definidas (
    id_actividad INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(10),              -- 1.3, 1.6, 1.7, 1.13, etc
    nombre VARCHAR(150),             -- Alistamiento, Digitalización, etc.
    tipologia ENUM('ALTA','BAJA','INSERCION'),
    rendimiento_hora INT             -- 16, 13, 12, 135, etc.
);







