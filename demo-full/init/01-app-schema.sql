CREATE SCHEMA IF NOT EXISTS app;
CREATE TABLE IF NOT EXISTS app.mahasiswa (
    id SERIAL PRIMARY KEY, nrp VARCHAR(15) UNIQUE NOT NULL,
    nama VARCHAR(100) NOT NULL, jurusan VARCHAR(50) NOT NULL,
    angkatan INTEGER NOT NULL, created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS app.matakuliah (
    id SERIAL PRIMARY KEY, kode VARCHAR(10) UNIQUE NOT NULL,
    nama VARCHAR(100) NOT NULL, sks INTEGER NOT NULL, semester INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS app.nilai (
    id SERIAL PRIMARY KEY, mahasiswa_id INTEGER REFERENCES app.mahasiswa(id),
    mk_id INTEGER REFERENCES app.matakuliah(id), nilai DECIMAL(5,2), grade CHAR(2)
);
CREATE TABLE IF NOT EXISTS app.activity_log (
    id BIGSERIAL PRIMARY KEY, table_name VARCHAR(50), action VARCHAR(10),
    row_data JSONB, changed_at TIMESTAMP DEFAULT NOW()
);
INSERT INTO app.mahasiswa (nrp,nama,jurusan,angkatan) VALUES
  ('3122600001','Aal Ahmad','Teknologi Informasi',2022),
  ('3122600002','Budi Santoso','Teknologi Informasi',2022),
  ('3122600003','Citra Dewi','Teknologi Informasi',2022),
  ('3122600004','Doni Prasetyo','Teknologi Informasi',2022),
  ('3122600005','Eka Putri','Teknologi Informasi',2023)
ON CONFLICT (nrp) DO NOTHING;
INSERT INTO app.matakuliah (kode,nama,sks,semester) VALUES
  ('TI301','Jaringan Komputer',3,5),
  ('TI302','Keamanan Sistem',3,5),
  ('TI303','Cloud Computing',3,6),
  ('TI304','DevOps & Containers',3,6)
ON CONFLICT (kode) DO NOTHING;
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='app_reader') THEN
    CREATE USER app_reader WITH PASSWORD 'reader123';
  END IF;
END $$;
GRANT CONNECT ON DATABASE labdb TO app_reader;
GRANT USAGE ON SCHEMA app TO app_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA app TO app_reader;
