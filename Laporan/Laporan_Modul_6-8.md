# Laporan Praktikum Modul 6-8: Docker Monitoring, Security & Keycloak IAM

**Nama:** [Nama Mahasiswa]  
**NRP:** [NRP]  
**Kelas:** [Kelas]  
**Tanggal:** 25 Mei 2026

---

## Modul 6: Grafana Service Docker untuk Monitoring Resource

### Tujuan
Deployment stack monitoring (Prometheus + Grafana + Node Exporter + cAdvisor) untuk memantau resource host dan container secara real-time.

### Arsitektur

```
Browser --> Grafana (:3000) --> Prometheus (:9090) --> Node Exporter (:9100)
                                                  --> cAdvisor (:8088)
                                                  --> Flask App (:5000/metrics)
```

### Implementasi

**docker-compose.yml (services monitoring):**

```yaml
services:
  prometheus:
    image: prom/prometheus
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin123

  node-exporter:
    image: prom/node-exporter
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    privileged: true
    ports:
      - "8088:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:rw
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
```

**prometheus.yml:**

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
  - job_name: 'flask-app'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['flask-app:5000']
```

**Grafana Datasource Provisioning:**

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
  - name: PostgreSQL
    type: postgres
    url: postgres-db:5432
    database: labdb
    user: labuser
    secureJsonData:
      password: labpass123
```

### Hasil & Verifikasi

| Komponen | Status | URL |
|----------|--------|-----|
| Prometheus | Running | http://localhost:9090 |
| Grafana | Running | http://localhost:3000 |
| Node Exporter | Running | http://localhost:9100/metrics |
| cAdvisor | Running | http://localhost:8088 |

**PromQL Query yang digunakan:**
- CPU Usage: `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- Memory: `node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100`
- Container CPU: `rate(container_cpu_usage_seconds_total[5m])`
- Container Memory: `container_memory_usage_bytes`

### Kesimpulan Modul 6
Stack monitoring berhasil di-deploy. Prometheus melakukan scrape metrics setiap 15 detik dari Node Exporter, cAdvisor, dan Flask app. Grafana menampilkan dashboard real-time dengan data dari Prometheus dan PostgreSQL sebagai datasource.

---

## Modul 7: Docker Security, Secrets & Private Registry

### Tujuan
Menerapkan best practice keamanan Docker: non-root container, Docker Secrets, image scanning, resource limits, dan private registry.

### Implementasi

**1. Non-Root Dockerfile (flask/Dockerfile):**

```dockerfile
FROM python:3.11-slim
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
CMD ["python", "-u", "app.py"]
```

**2. Docker Secrets (file-based):**

```
secrets/
├── db_password    → labpass123
├── db_user        → labuser
├── db_name        → labdb
└── db_host        → postgres-db
```

**docker-compose.yml secrets config:**

```yaml
services:
  flask-app:
    secrets:
      - db_password
      - db_user
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

secrets:
  db_password:
    file: ./secrets/db_password
  db_user:
    file: ./secrets/db_user
```

**3. Aplikasi membaca secret dari file:**

```python
def read_secret(name, default=""):
    path = f"/run/secrets/{name}"
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return os.environ.get(name.upper(), default)
```

**4. Private Registry:**

```yaml
  registry:
    image: registry:2
    container_name: docker-registry
    ports:
      - "5000:5000"
    volumes:
      - registry-data:/var/lib/registry
    environment:
      REGISTRY_STORAGE_DELETE_ENABLED: "true"
```

**5. Resource Limits & Read-only FS:**

```yaml
  nginx-proxy:
    read_only: true
    tmpfs:
      - /var/cache/nginx
      - /var/run
    deploy:
      resources:
        limits:
          cpus: '0.25'
          memory: 128M
```

### Hasil & Verifikasi

| Security Measure | Status |
|-----------------|--------|
| Non-root container (UID != 0) | ✅ Verified via `docker exec flask-app id` → uid=999(appuser) |
| Secrets mounted as files | ✅ `/run/secrets/db_password` accessible |
| Resource limits applied | ✅ `docker stats` shows memory cap |
| Private registry running | ✅ http://localhost:5000/v2/_catalog |
| Read-only filesystem | ✅ Nginx container fs immutable |

### Kesimpulan Modul 7
Keamanan container ditingkatkan dengan menjalankan proses sebagai non-root user, menyimpan kredensial di Docker Secrets (bukan environment variable), membatasi resource CPU/memory, dan menggunakan private registry untuk image internal.

---

## Modul 8: Keycloak — Identity & Access Management

### Tujuan
Deployment Keycloak sebagai Identity Provider dengan OAuth2/OIDC, integrasi dengan Flask app untuk autentikasi berbasis token.

### Arsitektur

```
Browser --> Nginx (:8080) --> Keycloak (:8081) [Identity Provider]
                          --> Flask App (:5000) [Protected Resource]
                          
Flow: Browser -> Login di Keycloak -> Dapat Token JWT -> Akses Flask API
```

### Implementasi

**Keycloak Service:**

```yaml
  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    container_name: keycloak
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin123
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres-db:5432/labdb
      KC_DB_USERNAME: labuser
      KC_DB_PASSWORD: labpass123
    command: start-dev
    ports:
      - "8081:8080"
    depends_on:
      postgres-db:
        condition: service_healthy
```

### Konfigurasi Keycloak (via Admin Console)

**1. Buat Realm:**
- Realm Name: `pens-lab`

**2. Buat Client:**
- Client ID: `flask-app`
- Client Protocol: openid-connect
- Access Type: confidential
- Valid Redirect URIs: `http://localhost:5000/*`

**3. Buat Users:**

| Username | Password | Role |
|----------|----------|------|
| mahasiswa1 | password123 | student |
| admin | admin123 | admin |

**4. Buat Roles:**
- Realm Roles: `student`, `admin`, `lab-user`

### OAuth2 Authorization Code Flow

```
1. User akses /dashboard → redirect ke Keycloak login
2. User login (username/password) di Keycloak
3. Keycloak redirect balik dengan authorization code
4. Flask exchange code → access token (JWT)
5. JWT berisi: sub, preferred_username, realm_access.roles
6. Flask validasi token → grant/deny access berdasarkan role
```

**JWT Token Structure (decoded):**

```json
{
  "sub": "user-uuid",
  "preferred_username": "mahasiswa1",
  "realm_access": {
    "roles": ["student", "lab-user"]
  },
  "exp": 1717200000
}
```

### Hasil & Verifikasi

| Komponen | Status | URL |
|----------|--------|-----|
| Keycloak Admin Console | Running | http://localhost:8081 |
| Realm 'pens-lab' | Created | Admin Console → Realms |
| Client 'flask-app' | Registered | Realm → Clients |
| User authentication | Working | Login flow tested |
| Token issued | Valid JWT | Contains roles & claims |

**Verifikasi:**
- `curl http://localhost:8081/realms/pens-lab/.well-known/openid-configuration` → returns OIDC discovery document
- Login via browser → token diterima → akses API berhasil

### Kesimpulan Modul 8
Keycloak berhasil di-deploy sebagai Identity Provider dengan PostgreSQL backend. Realm, client, user, dan role dikonfigurasi melalui Admin Console. OAuth2 Authorization Code Flow berfungsi untuk autentikasi user dan penerbitan JWT token yang berisi informasi role untuk RBAC.

---

## Ringkasan Keseluruhan

| Modul | Komponen Utama | Port | Status |
|-------|---------------|------|--------|
| 6 | Prometheus | 9090 | ✅ |
| 6 | Grafana | 3000 | ✅ |
| 6 | Node Exporter | 9100 | ✅ |
| 6 | cAdvisor | 8088 | ✅ |
| 7 | Private Registry | 5000 | ✅ |
| 7 | Non-root Flask | 5000 | ✅ |
| 8 | Keycloak | 8081 | ✅ |

Semua service berjalan dalam satu Docker Compose stack yang terintegrasi dengan network dan volume yang proper.
