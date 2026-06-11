-- ==============================================
-- Init Script: Database Schema untuk Lab PENS
-- Dijalankan otomatis saat container pertama kali start
-- ==============================================

CREATE DATABASE inventory_db;

\c labdb

CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE app.mahasiswa (
    id SERIAL PRIMARY KEY,
    nrp VARCHAR(15) UNIQUE NOT NULL,
    nama VARCHAR(100) NOT NULL,
    kelas CHAR(1) CHECK (kelas IN ('A', 'B', 'C', 'D')),
    kelompok INTEGER CHECK (kelompok BETWEEN 1 AND 10),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE app.matakuliah (
    id SERIAL PRIMARY KEY,
    kode VARCHAR(10) UNIQUE NOT NULL,
    nama VARCHAR(100) NOT NULL,
    sks INTEGER CHECK (sks BETWEEN 1 AND 6)
);

CREATE TABLE app.nilai (
    id SERIAL PRIMARY KEY,
    mahasiswa_id INTEGER REFERENCES app.mahasiswa(id) ON DELETE CASCADE,
    matakuliah_id INTEGER REFERENCES app.matakuliah(id) ON DELETE CASCADE,
    nilai_angka NUMERIC(5,2) CHECK (nilai_angka BETWEEN 0 AND 100),
    grade CHAR(2),
    semester VARCHAR(10),
    UNIQUE(mahasiswa_id, matakuliah_id, semester)
);

CREATE TABLE app.activity_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(10) DEFAULT 'INFO',
    source VARCHAR(50),
    message TEXT,
    metadata JSONB
);

CREATE INDEX idx_mahasiswa_kelas ON app.mahasiswa(kelas);
CREATE INDEX idx_mahasiswa_nrp ON app.mahasiswa(nrp);
CREATE INDEX idx_nilai_semester ON app.nilai(semester);
CREATE INDEX idx_activity_log_timestamp ON app.activity_log(timestamp);
CREATE INDEX idx_activity_log_level ON app.activity_log(level);
CREATE INDEX idx_activity_log_metadata ON app.activity_log USING GIN(metadata);

INSERT INTO app.matakuliah (kode, nama, sks) VALUES
    ('JAR01', 'Administrasi Jaringan', 3),
    ('SBD01', 'Sistem Basis Data', 3),
    ('SO01',  'Sistem Operasi', 2),
    ('WEB01', 'Pemrograman Web', 3);

INSERT INTO app.mahasiswa (nrp, nama, kelas, kelompok, email) VALUES
    ('3122600001', 'Ahmad Fauzi', 'A', 1, 'ahmad@student.pens.ac.id'),
    ('3122600002', 'Budi Santoso', 'A', 1, 'budi@student.pens.ac.id'),
    ('3122600003', 'Citra Dewi', 'B', 2, 'citra@student.pens.ac.id'),
    ('3122600004', 'Dian Pratama', 'B', 2, 'dian@student.pens.ac.id'),
    ('3122600005', 'Eka Putra', 'C', 3, 'eka@student.pens.ac.id');

INSERT INTO app.nilai (mahasiswa_id, matakuliah_id, nilai_angka, grade, semester) VALUES
    (1, 1, 85.50, 'A', '2025-1'),
    (1, 2, 78.00, 'B+', '2025-1'),
    (2, 1, 92.00, 'A', '2025-1'),
    (3, 1, 70.25, 'B', '2025-1'),
    (4, 3, 88.75, 'A', '2025-1');

CREATE USER app_reader WITH PASSWORD 'reader123';
GRANT USAGE ON SCHEMA app TO app_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA app TO app_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT ON TABLES TO app_reader;

RAISE NOTICE 'Database initialization completed successfully!';
