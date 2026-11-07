# backend가 PostgreSQL에 접속하지 못한 원인: `postgres` Service 누락

## 결론

backend가 접속하는 호스트 이름 `postgres`를 가리키는 Service가 클러스터에 없었습니다. PostgreSQL StatefulSet은 배포됐지만 DNS 이름을 만들어 주는 Service 매니페스트가 어느 PR에도 들어 있지 않았습니다.

## 증상

`kubectl logs deployment/backend`에서 backend 시작이 실패했습니다.

```
Caused by: org.postgresql.util.PSQLException: The connection attempt failed.
Caused by: java.net.UnknownHostException: postgres
```

Hikari가 시작 시점에 DB 연결을 시도하다가 호스트 이름을 풀지 못해 Spring 컨텍스트 초기화가 중단됐습니다.

## 원인

| 항목 | 상태 | 근거 |
| --- | --- | --- |
| backend의 접속 대상 | `jdbc:postgresql://postgres:5432/appdb` | `infra/kubernetes/apps/backend/deployment.yaml`의 `DB_URL` |
| PostgreSQL StatefulSet | `postgres`라는 이름으로 존재 | `infra/kubernetes/databases/postgres/statefulset.yaml` |
| StatefulSet의 `serviceName` | `postgres-headless` | 같은 파일 |
| `postgres` Service | 없음 | `databases/postgres/`에 `statefulset.yaml`만 있었음 |
| `postgres-headless` Service | 없음 | 위와 같음 |

StatefulSet 이름이 `postgres`여도 클러스터 DNS에는 등록되지 않습니다. 클러스터 내부 DNS 이름은 Service가 만듭니다.

## 왜 배포 후에도 드러나지 않았나

- PR #100은 `.gitignore`, `infra/.env.example`, `statefulset.yaml` 세 파일만 추가했습니다. DB Pod는 떴지만 접근 경로는 만들지 않았습니다.
- backend가 `postgres` 호스트를 쓰도록 바꾼 변경(`c090d30`)은 별도 PR #101에 있습니다.
- 두 PR 어디에도 Service가 없어서, 각 PR을 따로 보면 이상이 없고 함께 배포했을 때만 실패합니다.

## 해결

`infra/kubernetes/databases/postgres/service.yaml`을 추가했습니다.

- `postgres`: ClusterIP, 5432 포트, selector `app: postgres`. backend가 쓰는 DNS 이름입니다.
- `postgres-headless`: `clusterIP: None`. StatefulSet의 `serviceName`이 참조합니다.

## 적용과 확인

```
sudo k3s kubectl apply -f k3s-poc/infra/kubernetes/databases/postgres/service.yaml
sudo k3s kubectl get svc,endpoints postgres
sudo k3s kubectl rollout restart deployment/backend
```

backend는 시작 시점에 연결에 실패한 상태일 수 있으므로 Service 적용 뒤 `rollout restart`가 필요합니다. `endpoints postgres`에 Pod IP가 나오면 selector가 맞게 연결된 것입니다.

## 확인하지 못한 것

- 클러스터에 실제로 적용한 결과는 확인하지 않았습니다. 매니페스트 검증은 `kubectl apply --dry-run=client`까지만 했습니다.
- `postgres-auth` Secret의 존재 여부와 `postgres-0` Pod의 Ready 상태는 확인하지 않았습니다. Secret이 없으면 DB Pod가 뜨지 않아 같은 증상 뒤에 다른 원인이 남을 수 있습니다.

## 재발 방지

StatefulSet을 추가할 때는 `serviceName`이 가리키는 Headless Service와 클라이언트가 쓰는 접속용 Service를 같은 PR에 넣습니다.
