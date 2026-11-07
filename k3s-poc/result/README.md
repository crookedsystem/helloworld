# result

k3s PoC를 진행하며 터미널에서 실행한 명령과 출력을 단계별로 모아 둔 기록입니다. 각 파일은 `$ 명령` 줄, 출력, `(exit N)` 종료 코드 순서로 쌓여 있고 ANSI 색상 코드를 포함합니다. 색을 그대로 보려면 `less -R <파일>`로 열고, 색 없이 보려면 아래처럼 코드를 제거합니다.

```bash
sed 's/\x1b\[[0-9;]*m//g' result/21-final-verification.ansi
```

## 기존 매니페스트를 Helm 릴리스로 전환 (06~16)

| 파일 | 내용 |
| --- | --- |
| `06-probes-deploy.ansi` | backend에 Health Check Probe와 리소스 설정을 넣고 jar 빌드, 이미지 `k3s-demo-backend:v3` 빌드, containerd 등록, `kubectl apply`, 롤아웃 확인까지 |
| `07-helm-install.ansi` | Helm 3 설치와 버전, 릴리스 목록, 노드 상태 확인 |
| `08-pre-migration-state.ansi` | Helm 전환 전 Deployment, StatefulSet, Service, PVC, Secret 상태와 StatefulSet의 `serviceName`, PVC 템플릿 이름, 스토리지 설정 조회 |
| `09-backup.ansi` | 전환 전 리소스 YAML 백업과 `pg_dump`로 DB 덤프 생성 |
| `10-chart-validation.ansi` | 기존 `infra/helm` 차트의 `helm lint`, `helm template`, 서버 측 `--dry-run`, 클러스터와의 `kubectl diff` |
| `11-postgres-takeover.ansi` | `--take-ownership`으로 기존 PostgreSQL 리소스를 Helm 릴리스 `postgres`로 인계. 데이터와 PVC UID가 유지되는지 확인 |
| `12-backend-takeover.ansi` | 기존 backend 리소스를 Helm 릴리스 `backend`로 인계하고 롤아웃 확인 |
| `13-integration-test.ansi` | Health Check, User API 생성과 조회, DB 조회로 backend와 PostgreSQL 연동 확인 |
| `14-upgrade-rollback.ansi` | `helm upgrade`로 값을 바꾼 뒤 `helm rollback`으로 되돌려 이력 확인 |
| `15-remove-legacy-yaml.ansi` | Helm으로 대체된 `infra/kubernetes` 아래 기존 YAML 삭제 |
| `16-final-verification.ansi` | 전환 완료 후 릴리스, 매니페스트, 파드, PVC 최종 상태 확인 |

## 차트 구조 재구성 (17~21)

`infra/helm`을 `infra/charts`와 `infra/environments`로 나눈 작업의 기록입니다. 클러스터에는 적용하지 않고 렌더링 결과만 검증했으며, 파일 번호는 커밋 순서와 같습니다.

| 파일 | 내용 |
| --- | --- |
| `17-chart-move.ansi` | `git mv`로 차트를 `charts/spring-app`, `charts/postgres`로 옮기고 `values-local.yaml`을 `environments/local/backend.yaml`로 이동. 이동 전후 `helm template` 결과가 같은지 `diff`로 확인 |
| `18-environment-values.ansi` | 공통 DB 설정 `platform.yaml`과 서비스별 `backend.yaml`, `postgres.yaml` 작성. YAML 문법 검증 |
| `19-spring-app-chart.ansi` | spring-app 차트가 `global.database`를 참조하도록 변경한 `git diff`, `helm lint`, `helm template`, 이전 렌더링과의 `diff` |
| `20-postgres-chart.ansi` | postgres 차트의 같은 변경과 검증. 렌더링 결과는 이전과 동일 |
| `21-final-verification.ansi` | 실행 중인 `backend`, `postgres` Helm 릴리스 매니페스트와 새 차트 렌더링을 비교하고 커밋 목록 확인 |

`diff`가 `(exit 1)`로 끝난 기록은 차이가 있다는 뜻이며 오류가 아닙니다. 17~21의 차이는 `# Source:` 주석의 차트 이름과 파일 끝 빈 줄뿐입니다.
