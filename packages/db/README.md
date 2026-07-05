# packages/db

PostgreSQL schema、migration、seed、local fixture を置く。

RDB は system of record なので、DB schema は service 固有実装ではなく repo 横断の共有契約として扱う。
