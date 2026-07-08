---
kind: synthesis
created: 2026-07-08
updated: 2026-07-08
epic_id: OPL-OFFICIAL-POLITICAL-EVENTS-20260707
issue_id: G2PR-014
status: feasibility-synthesis
spec: official-political-events-ingest-spec.md
---

# 官報 election notice feasibility

## 結論

官報は `jp_national_election_notices` における `official_notice` source として扱える。ただし、現時点で自動 connector の既定経路にはしない。

理由は次のとおり。

- 官報は法令上の告示・公告を載せる公式公報であり、選挙の公示・告示・結果告示の根拠 source として使える。
- 2026-07-08 確認時点で、官報サイトは営業日に 8:30 公開、原則 90 日分の全文閲覧・PDF ダウンロードを無料提供している。
- 一方で、利用案内には attribution requirement と、負荷を与える crawler 的収集を禁止する条件がある。
- 過去分の検索は国立印刷局の有料 search service 前提で、無料の継続 backfill source とは言いにくい。
- privacy-sensitive article は 90 日経過後に image-rendered / 閲覧制限されると明記されており、長期 archive を機械取得前提にしづらい。
- この worker では PDF download と OCR を行っていないため、text layer の有無や OCR 必要性は未検証である。

したがって、官報は source registry 上は `official_notice` として登録しつつ、初期 coverage status は `manual_review_required` を基本にするのが妥当である。自動取得を `supported` に上げるのは、対象範囲を直近 90 日に限定し、低頻度 access、attribution、fixture 保存、PDF text/OCR 方針を別 issue で固めた後に限る。

## 確認した公式 facts

確認日はいずれも 2026-07-08。

| source | URL | 確認 fact |
| --- | --- | --- |
| 官報利用案内 | https://www.kanpo.go.jp/guidance.html | 営業日 8:30 公開、原則 90 日分の全文閲覧・PDF ダウンロード、privacy-sensitive article の 90 日後制限、attribution requirement、負荷を与える crawler 的収集の禁止を確認。 |
| 国立印刷局 官報商品案内 | https://www.npb.go.jp/product_service/books/kanpo/index.html | 2025-04-01 以降の官報電子版案内、旧インターネット版の引継ぎ、search service が有料会員制であることを確認。 |

## `official_notice` としての位置づけ

`officiality_level` は `official_notice` でよい。理由は、官報が所管官庁の一次告知ページそのものではなく、法令・告示・公告を掲載する公式公報だからである。

OpenPolitics Lens での扱いは次の条件に限る。

- 対象は、選挙期日、公示、告示、結果告示など、法令上の notice として官報掲載される event。
- event candidate は官報 PDF そのもの、または官報 issue / article を指す SourceDocument と EvidenceItem に戻れる場合だけ作る。
- 官報掲載をもって「notice が出た」ことは言えるが、投票日、候補者情報、詳細 schedule は別の official_primary source で補う前提を崩さない。

## 取得可能範囲と制約

### 無料公開範囲

- 直近 90 日分は無料で全文閲覧・PDF ダウンロード可能。
- 営業日 8:30 公開なので、当日 ingest をするなら daily publication timing を前提にする必要がある。

### 過去分

- 過去分の横断検索は paid membership の search service 前提。
- よって、無料前提の nationwide historical backfill connector はこの source 単独では成立しない。
- 無料範囲外の過去分を大量に埋める要件がある場合、初期 status は `blocked_by_terms` または少なくとも `manual_review_required` に落とすべきである。

### 保存形式

- 公開形式は PDF。
- この worker では PDF を取得していないため、text layer の有無、構造の安定性、article locator の取り方は未確認。
- したがって、初期 retrieval_method は `official_notice_pdf` を候補にしつつ、parser contract は未確定のまま残す。

### 検索可否

- 無料で継続利用できる汎用 search API / open search endpoint は確認していない。
- paid search service を connector の前提にすると、repo 既定の local-only / no-remote-write / no-billing 方針から外れる。
- 初期 connector は search service 非依存、すなわち「既知の日付の issue を限定的に参照する」方式でない限り成立しにくい。

## `jp_national_election_notices` への接続条件

官報を `jp_national_election_notices` に接続する条件は次のとおり。

1. source registry では `source_system=kanpo`、`source_family=jp_national_election_notices`、`officiality_level=official_notice` とする。
2. coverage scope は「国政選挙の告示・公示・結果告示など、官報掲載で確認できる notice」に限定する。
3. 初期 `coverage_status` は `manual_review_required` を基本にする。
4. `supported` に上げる条件は、直近 90 日内、低頻度 access、attribution 明記、known issue URL からの限定取得、fixture 保存、PDF text/OCR 方針の承認が揃うこと。
5. 無料 90 日外の historical backfill や、paid search membership を必要とする設計は `blocked_by_terms` 候補として扱う。

## `blocked_by_terms` / `manual_review_required` の判断ルール

### `manual_review_required`

次の場合は `manual_review_required` が妥当である。

- 官報 issue URL や issue date は既知だが、PDF structure 未検証のため parser / locator が固まっていない。
- 90 日内の無料公開範囲だけを対象に、少量 fixture で feasibility を続ける。
- privacy-sensitive article の扱いで image-rendered / restriction の有無を人手確認する必要がある。

### `blocked_by_terms`

次の場合は `blocked_by_terms` を表現できる。

- 高頻度 polling や大量クロールなど、利用案内の禁止に抵触する収集方式が必要になる。
- 無料 90 日外の大規模 historical backfill を paid search なしで自動取得したい。
- 有料 search service や別契約を前提にしないと issue discovery が成立しない。

## PDF text layer / OCR 方針

この worker では PDF download を行っていないため、次は未検証である。

- PDF text layer が十分に存在するか
- privacy-sensitive article が image-rendered になる範囲
- page / article 単位 locator を安定して作れるか
- OCR を使う場合の confidence / warning policy

現時点の判断は次のとおり。

- PDF text layer が安定していても、官報は notice source であり article layout 依存がありうるため、EvidenceItem locator 設計は別 issue で必要。
- text layer が不十分、または image-rendered article が混ざる場合は OCR issue を別建てにし、`ocr_required` と `manual_review_required` を残す。
- 本 issue では OCR 実行要否を確定せず、「sample PDF fixture を使った parser feasibility」が後続 issue で必要、という結論に留める。

## 後続 issue に残すこと

1. 官報 PDF sample fixture を使い、text layer、page locator、article segmentation の feasibility を確認する。
2. 官報 notice から `election_notice_published` や `result_published` を作る最小 assertion contract を定める。
3. 90 日無料範囲に限定した acquisition cadence と rate-limit policy を source registry に落とす。
4. paid search service を使わない issue discovery 導線で足りるかを別途判断する。

## 残リスク

- この synthesis は worker packet の inline fact のみを根拠としており、live fetch、PDF sample 確認、OCR 実験は行っていない。
- 官報上の選挙 notice が常に十分な event metadata を持つとはまだ言えない。官報は notice の根拠 source であって、選挙 schedule 全体の primary source ではない。
- historical coverage をどこまで官報で担うかは、paid search 依存を避ける方針と衝突しうる。

## 関連ページ

- [公式政治イベント ingest 設計](official-political-events-ingest-spec.md)
- [公式政治イベント ingest ローカル issue ledger](official-political-events-ingest-issues.md)
- [Data Sources](../../data-sources.md)
- [Legal And Evidence Risk](../../legal-risk.md)
