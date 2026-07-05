# packages

複数 app/service から参照される共有契約と共有 model を置く。

初期境界:

- `contracts/`: OpenAPI、JSON Schema、event schema。
- `db/`: migration、seed、local fixture。
- `domain/`: domain enum、state、軽量 model。

runtime implementation は各 app/service に置き、ここには共有すべき契約だけを置く。
