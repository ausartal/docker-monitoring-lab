# Docker Monitoring Lab — PENS

**Nama:** Aal  
**Institusi:** Mahasiswa IT — Politeknik Elektronika Negeri Surabaya (PENS)

Repositori ini berisi semua file praktikum Docker dari Modul 1 hingga Modul 9.

---

## Struktur Modul

| Modul | Topik |
|-------|-------|
| [modul-1](./modul-1/) | Instalasi Docker & Dockerfile Dasar |
| [modul-2](./modul-2/) | Docker Service, Volume & Mount Point |
| [modul-3](./modul-3/) | Web Service Docker — Apache & Nginx |
| [modul-4](./modul-4/) | Database Service — PostgreSQL |
| [modul-5](./modul-5/) | Logging Service — Fluent Bit + PostgreSQL |
| [modul-6](./modul-6/) | Grafana Monitoring — Prometheus + Grafana |
| [modul-7](./modul-7/) | Docker Security, Secrets & Private Registry |
| [modul-8](./modul-8/) | Keycloak — Identity & Access Management |
| [modul-9](./modul-9/) | CI/CD Pipeline — Gitea & Drone CI |

---

## Cara Penggunaan

Setiap folder modul memiliki `docker-compose.yml` sendiri (kecuali modul-1).  
Jalankan dari dalam folder modul yang bersangkutan:

```bash
cd modul-X
docker compose up --build -d
```

Lihat README masing-masing modul atau file MODUL_*.md untuk instruksi lengkap.
