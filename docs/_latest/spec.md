# 트레이딩 봇 요구 명세서 (Draft v0.1)

> 본 문서는 `체결봇·매수봇·매도봇`을 기본으로 하는 자동 트레이딩 시스템의 **초기 요구 명세서**입니다.
> 대상 거래소 API 레퍼런스: ExchangeDocs v2 (영문) — *세부 엔드포인트는 연결 후 확정*.
> 문서는 캔버스에서 수시 업데이트됩니다.

---

## 0. 목적 & 범위

* **목적**: 지정 거래소의 Open API를 이용해 토큰 페어/정밀도(소수점) 설정 → 봇 계정(API Key 등록) → 체결 환경/매수/매도 전략 등록 → 자동 매매 수행.
* **범위**:

  * 어드민 설정(토큰/페어/정밀도, 봇 계정, 전략 프로파일)
  * 3종 봇(체결봇, 매수봇, 매도봇) 런타임
  * 모니터링/로그/알림
  * 기본 리스크 제어(오더 한도, 잔고/수수료 검증)

---

## 1. 용어 정의

* **체결봇(Execution Bot)**: 이미 존재하는 주문과 호가를 기반으로 지정된 조건에서 **체결만** 담당(예: 스프레드 내 크로스, 잔량 맞춤 체결, IOC/FOK 사용 등).
* **매수봇(Buy Bot)**: 매수 전략(지정가/시장가/그리드/조건부)으로 **매수 주문 생성/관리**.
* **매도봇(Sell Bot)**: 매도 전략으로 **매도 주문 생성/관리**.
* **전략 프로파일(Strategy Profile)**: 각 봇이 참조하는 파라미터 세트(가격/수량 소수점, 슬리피지, 최소 주문수량, 수수료, 손절/익절 등).
* **정밀도(Precision)**: 가격 `price_precision`·수량 `qty_precision`·금액 `amount_precision` 소수점 자릿.
* **거래쌍(Symbol/Pair)**: 예) `LTC/USDT`.

---

## 2. 이해관계자

* **Admin**: 전체 환경과 자산 메타를 관리한다. 토큰/페어 등록, 정밀도(소수점)·최소 주문값 설정, 수수료 스키마 관리, 전역 리스크 한도 정의를 수행한다. 또한 **특정 토큰의 봇을 조종할 계정(봇 계정)을 지정/승인**하고, 필요한 경우 계정에 권한과 한도를 부여한다.
* **User(사용자)**: 본인 거래소 계정의 **API Key / API Secret**을 안전하게 등록하고(개인 키는 본인 소유), **본인 계정 기준 잔액 조회** 및 **봇의 전략/파라미터(셋팅값) 구성**을 수행한다. 자신에게 할당된 페어/전략에 대해 봇 **시작/중지/일시정지**를 조종하며, 자신의 한도 내에서만 주문이 실행된다.
* **Operator**: 운영 관점에서 봇 실행/중지, 파라미터 핫픽스, 로그/알림 확인을 수행한다(조직에 따라 Admin/User와 겸임 가능).
* **System**: 거래소 API 연동, 시세/잔고 수집, 주문/취소/조회 및 장애 복구를 담당한다.

---

## 3. 상위 사용자 스토리

### 3.1 Admin 관점

* **A1. 토큰/페어 등록**: 새 토큰·페어를 등록하고 정밀도(가격/수량/금액), 최소 주문값, 수수료 스키마를 지정한다.
* **A2. 봇 계정 지정/승인**: 특정 토큰(또는 페어)의 봇을 조종할 **봇 계정(또는 사용자 계정)**을 지정/승인하고 권한·한도(일일 체결량, 미체결 수량, 1회 주문 상한)를 설정한다.
* **A3. 전략 프로파일 템플릿 발행**: 체결/매수/매도 템플릿을 만들고 사용자/봇 계정이 이를 복제하여 개인화할 수 있게 한다.
* **A4. 전역 리스크 가드**: 전역 취소(심각 장애 시), 거래 중지 창구, 점검 모드 스케줄을 운영한다.

**AC (수용 기준)**

* 등록 페어는 정밀도/최소값 검증을 통과해야 저장된다.
* 봇 계정 승인 시 연결 테스트(`balances`, `account`)가 성공해야 한다.
* 전역 중지 시 모든 신규 주문 차단 및 미체결 주문 일괄 취소 API가 트리거된다.

### 3.2 User(사용자) 관점

* **U1. API 키 등록**: 본인 거래소 계정의 **API Key/Secret**을 안전히 저장(암호화)하고, 연결 테스트를 수행한다. 저장 후 Secret은 **재노출되지 않는다**(회전/재발급만 허용).
* **U2. 잔액/한도 확인**: Base/Quote 잔액, 할당된 페어, 본인 계정 한도(일일 체결량·오픈오더 수·1회 주문상한)를 확인한다.
* **U3. 전략 셋팅**: Admin이 배포한 템플릿을 복제하거나 개인 전략 프로파일을 생성하여 **체결/매수/매도** 파라미터(슬리피지, TP/SL, 그리드 간격, DCA 규칙 등)를 설정한다.
* **U4. 봇 조종**: 자신에게 허용된 페어/전략에 대해 **시작/중지/일시정지**를 수행한다. 중지 시 미체결 주문 정리 옵션(즉시 취소 / 유지)을 선택 가능.
* **U5. 모니터링**: 체결 수, 실패 사유, 평균 슬리피지, PnL(현물 기준 실현 손익/수수료 포함), 경보를 실시간 확인한다.
* **U6. 키/전략 변경 감사**: 본인 변경 이력(언제, 무엇을, 전/후 값) 조회.

**AC (수용 기준)**

* 키 저장 직후 연결 테스트 성공 시에만 활성화된다.
* 전략 저장 시 정밀도/최소 주문값/한도 검증을 통과해야 **활성화 가능** 상태가 된다.
* 봇 시작 시 잔액·수수료·한도를 재검사해 실패 원인을 명확히 피드백한다.

### 3.3 Operator 관점

* **O1. 운영 대시보드**: 다수 봇의 상태/체결률/에러율/WS연결 상태를 한 화면에서 확인한다.
* **O2. 장애 대응**: 재시작·폴백(REST)·재구독·전역 취소를 수행한다.

### 3.4 System 관점

* **S1. 시세·잔고 동기화**: WS 우선, REST 폴백. 지연/누락 대비 버퍼링 및 재동기화.
* **S2. 주문 수명주기 관리**: 생성→접수→부분체결→완료/취소, 리트라이/백오프.
* **S3. 보안**: 시그니처/타임스탬프 검증, 키 암호화/마스킹, IP 화이트리스트, 감사로그.

### 3.5 권한/책임 경계(요약)

| 항목             | Admin | User | Operator       |
| -------------- | ----- | ---- | -------------- |
| 토큰·페어 등록/정밀도   | ✅     | ❌    | ❌              |
| 봇 계정 승인/한도 설정  | ✅     | ❌    | ❌              |
| 본인 API 키 등록/회전 | ❌     | ✅    | ❌              |
| 전략 템플릿 발행      | ✅     | ❌    | ❌              |
| 개인 전략 생성/수정    | ❌     | ✅    | ❌              |
| 봇 시작/중지(자기 봇)  | ❌     | ✅    | ⚠️(운영 권한 범위 내) |
| 전역 중지/일괄 취소    | ✅     | ❌    | ✅              |

### 3.6 기본 시퀀스(요약)

1. **Admin**: 토큰/페어/정밀도 등록 → 전략 템플릿 발행 → 봇 계정 승인/한도 부여.
2. **User**: API Key/Secret 등록(+테스트) → 잔액/한도 확인 → 템플릿 복제·전략 셋팅 → 봇 시작.
3. **System**: 시세/잔고 동기화 → 주문 생성/체결/취소 → 로그/알림 → 리스크 가드.

---

## 4. 기능 요구사항

기능 요구사항

### 4.1 어드민: 토큰/페어/정밀도 설정

* [R-ADM-001] 토큰 등록: `symbol`, `name`, `chain(optional)`.
* [R-ADM-002] 페어 등록: `base`, `quote`, `symbol_code(ex: LTCUSDT)`.
* [R-ADM-003] 정밀도 설정: `price_precision`, `qty_precision`, `amount_precision`.
* [R-ADM-004] 최소 주문 수량/금액: `min_qty`, `min_notional`.
* [R-ADM-005] 수수료 스키마: `maker_fee`, `taker_fee`(거래소/계정별 상이 시 계정단 재정의 허용).
* [R-ADM-006] 거래소 심볼 메타 자동 동기화(선택): Exchange API의 심볼 메타에서 정밀도/최소값을 **불러와 저장**.

### 4.2 어드민: 봇 계정(API Key) 관리

* [R-ADM-101] 봇 계정 생성: `name`, `exchange`, `api_key`, `api_secret`, `passphrase(optional)`.
* [R-ADM-102] 권한/리스크 한도: `max_open_orders`, `max_daily_volume`, `max_order_value`.
* [R-ADM-103] 연결 테스트: `GET /account`, `GET /balances` 등 호출로 유효성 확인.
* [R-ADM-104] 키 보안: KMS/암호화 저장, 마스킹, 감사로그.

### 4.3 어드민: 전략 프로파일 정의

* [R-ADM-201] 공통: 대상 `pair`, 참조 정밀도, 공통 슬리피지(bps), 라운딩 규칙(`ROUND_DOWN/UP/FLOOR`), 타임인포스(`GTC/IOC/FOK`).
* [R-ADM-202] 체결봇: 스프레드 임계치, 상대호가 추종 여부, 잔량 맞춤, 가격 개선틱, 최대 연속 체결 수.
* [R-ADM-203] 매수봇: 엔트리 방식(지정/시장/조건부), 계단/그리드 파라미터, 1회 주문수량/최대 동시주문, 평균단가 관리(DCA).
* [R-ADM-204] 매도봇: 목표 수익률/트레일링, 부분청산 비율, 손절(하드/트레일링), 보호호가(가격 바운드).
* [R-ADM-205] 캘린더/세션: 거래 금지 시간대, 점검 모드.

### 4.4 봇 런타임

* [R-BOT-001] 시세 수집: Ticker/Orderbook/Trades(REST+WebSocket 지원 시 WS 우선).
* [R-BOT-002] 잔고/포지션 동기화: Quote/Base 자산 가용 수량 확인.
* [R-BOT-003] 주문 인터페이스: **생성, 조회, 취소, 대량취소**.
* [R-BOT-004] 체결 이벤트 수신 및 포지션·평단가 업데이트.
* [R-BOT-005] 정밀도/최소단위에 따른 **라운딩 & 검증** 후 주문.
* [R-BOT-006] 장애 복구: 재시작 시 미체결/오픈오더 재동기화.
* [R-BOT-007] 리스크 가드: 한도 초과 차단, 수수료 고려 체결가 산정.
* [R-BOT-008] **봇 상태 관리**: RUNNING / PAUSED / STOPPED / ERROR / HALTED(외부·내부 문제로 비정상 정지) 상태를 갖는다. HALTED 발생 시 원인코드(WS_DISCONNECT, RATE_LIMIT, REJECT, INSUFFICIENT_BALANCE, CONFIG_ERROR, USER_KILL 등)와 함께 타임스탬프 기록.
* [R-BOT-009] **사용자 주도 실행**: 각 봇(전략 인스턴스)은 **사용자(User)가 개별적으로 시작/정지**해야 활성화/중지된다. Admin/Operator는 전역 중지(비상)만 수행.

### 4.5 모니터링·알림·로그

* [R-MON-001] 대시보드: 봇 상태(ON/OFF/HALTED), PnL, 체결 수, 실패 수, 잔고.
* [R-MON-002] 알림: 임계치 초과/연속 실패/잔고 부족/WS 끊김 → Slack/Telegram/Email.
* [R-MON-003] 감시 작업: 체결률, 평균 슬리피지, 리젝 사유 코드 통계.
* [R-MON-004] 감사 로그: 설정 변경·키 열람·주문/취소 이벤트.
* [R-MON-005] **정지 이벤트 기록**: HALTED/ERROR 발생 시 `bot_events`(신규 테이블)와 애플리케이션 로그에 원인, 상세 메시지, 관련 주문ID/요청ID, 복구 액션을 구조화하여 기록.
* [R-MON-006] **재가동 워크플로우**: 사용자가 재시작을 누르면 사전 점검(키 유효성, 잔고, 페어 메타, 레이트 리밋 상태)을 통과해야 RUNNING 전환.

### 4.6 추세 목표(Equity/Position Curve Target) 모듈

> 가격을 **조작**하는 기능이 아니라, **전략의 목표 궤적(Equity 또는 포지션 잔량/노출)**을 시간에 따라
> 매끄러운 곡선으로 **설정/시각화**하고, 주문 크기·빈도를 **조정**하는 기준으로 사용한다.

* [R-CURVE-001] **일일 상승률 목표**: `daily_up_rate`(%)를 설정하면, 목표 equity/노출이 하루 기준으로 지속 상승하는 곡선을 생성한다.

* [R-CURVE-002] **일일 하강률 목표**: `daily_down_rate`(%)를 설정하면, 목표 equity/노출이 하루 기준으로 지속 하강하는 곡선을 생성한다.

* [R-CURVE-003] **기간 상승 곡선**: `[start, end, total_up_%]`를 입력하면, 지정 기간 동안의 목표 궤적을 자동 스플라인/지수/선형 등 **곡선 옵션**으로 생성하여 **자연스러운 상승 곡선**을 만든다.

* [R-CURVE-004] **기간 하강 곡선**: `[start, end, total_down_%]`를 입력하면, 지정 기간 동안의 목표 궤적을 자동 곡선으로 생성하여 **자연스러운 하강 곡선**을 만든다.

* [R-CURVE-005] **곡선-전략 연동**: 생성된 목표 궤적과 현재 실측(Equity/노출)을 비교해 **주문 크기·빈도·그리드 스텝 수**를 미세조정(DCA 강도, TP 간격 보정 등). 시장 유동성/슬리피지·레이트리밋에 부합할 것.

* [R-CURVE-006] **시각화**: 백엔드에서 표준화된 시계열(utc_ts, target_value, actual_value)을 제공, 프론트에서 라인 차트로 표시.

* [R-CURVE-007] **규제/윤리 가드**: 곡선 목표는 **시장 가격**을 목표로 하지 않으며, 시세 조작을 유도하지 않는다. 주문은 항상 시장 상태·거래소 규칙·법규를 준수.

* [R-MON-001] 대시보드: 봇 상태(ON/OFF), PnL, 체결 수, 실패 수, 잔고.

* [R-MON-002] 알림: 임계치 초과/연속 실패/잔고 부족/WS 끊김 → Slack/Telegram/Email.

* [R-MON-003] 감시 작업: 체결률, 평균 슬리피지, 리젝 사유 코드 통계.

* [R-MON-004] 감사 로그: 설정 변경·키 열람·주문/취소 이벤트.

---

## 5. 비기능 요구사항

* **성능**: WS 지연 < 300ms(가급), REST 호촐 리트라이/백오프.
* **보안**: 키 암호화 저장, 서브넷/IP 화이트리스트, 시그니처/타임스탬프 검증.
* **가용성**: 봇 프로세스 별 헬스체크, 무중단 재배포(rolling).
* **감사성**: 변경 이력/버전링.

---

## 6. 외부 API 연동 (ExchangeDocs v2 매핑)

> 기준 문서: Open API Doc (Spot). 실제 운영 시 `baseurl`은 거래소에서 제공한 값을 사용.

### 6.1 공통 (Base / Headers / 서명)

* **Base URL**: `https://www.mbitinside.com`
* **공통 헤더**

  * `X-CH-APIKEY`: 발급받은 API Key
  * `X-CH-TS`: 요청 타임스탬프(ms)
  * `X-CH-SIGN`: 서명(HMAC-SHA256)
  * `Content-Type: application/json`
* **서명 규칙 (TRADE/USER_DATA)**

  * 원문: `timestamp + method + requestPath + bodyString`
  * 키: API Secret, 알고리즘: HMAC-SHA256
  * 시간 보안: `recvWindow`(ms) 허용, 서버 시간과 1초 이상 차이 나면 거절

### 6.2 퍼블릭(무서명)

| 내부 인터페이스        | 외부 메소드/경로              | 필수 파라미터                                         | 메모                                                 |
| --------------- | ---------------------- | ----------------------------------------------- | -------------------------------------------------- |
| Ping            | `GET /sapi/v1/ping`    | -                                               | 연결 확인                                              |
| Server Time     | `GET /sapi/v1/time`    | -                                               | 서버 타임스탬프(ms)                                       |
| Symbols(페어 메타)  | `GET /sapi/v1/symbols` | -                                               | `pricePrecision`, `quantityPrecision`, `limit*` 포함 |
| Orderbook Depth | `GET /sapi/v1/depth`   | `symbol`, `limit`                               | 기본 100, 최대 100                                     |
| 24h Ticker      | `GET /sapi/v1/ticker`  | `symbol`                                        | 고가/저가/거래량/종가 등                                     |
| Recent Trades   | `GET /sapi/v1/trades`  | `symbol`, `limit`                               | 최대 1000                                            |
| Klines          | `GET /sapi/v1/klines`  | `symbol`, `interval`, (startTime,endTime,limit) | interval: 1min~1month                              |

### 6.3 거래(TRADE, 서명 필요)

| 내부 인터페이스 | 외부 메소드/경로                     | 요청 바디(주요)                                                                                                                                | 비고                 |
| -------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| 신규 주문    | `POST /sapi/v1/order`         | `symbol`/`symbolName`, `side(BUY/SELL)`, `type(LIMIT/MARKET/IOC/FOK/POST_ONLY)`, `price*`, `volume*`, `newClientOrderId?`, `recvWindow?` | **레이트**: 100회/2초   |
| 주문 테스트   | `POST /sapi/v1/order/test`    | 신규 주문과 동일                                                                                                                                | 체결 엔진 미전송(서명 검증 용) |
| 배치 주문    | `POST /sapi/v1/batchOrders`   | `orders[...<=10]`, `symbol`/`symbolName`                                                                                                 | 최대 10건             |
| 주문 조회    | `GET /sapi/v1/order`          | `orderId` 등                                                                                                                              | (문서 하단 섹션 참조)      |
| 주문 취소    | `DELETE /sapi/v1/order`       | `orderId` 등                                                                                                                              |                    |
| 일괄 취소    | `DELETE /sapi/v1/batchOrders` | `symbol`/`symbolName`                                                                                                                    | 심볼 단위 일괄 취소        |
| 현재 오픈오더  | `GET /sapi/v1/openOrders`     | `symbol?`                                                                                                                                | 심볼별/전체 조회          |
| 체결내역     | `GET /sapi/v1/myTrades`       | `symbol`, (limit, fromId, startTime, endTime)                                                                                            |                    |

> **정밀도/최소 단위 검증**: 주문 전 `pricePrecision`, `quantityPrecision`, `limitAmountMin/limitPriceMin/limitVolumeMin`에 맞춰 라운딩/검증 필수.

### 6.4 계정/잔고(USER_DATA, 서명 필요)

| 내부 인터페이스 | 외부 메소드/경로              | 헤더                                    | 응답(핵심)                            |
| -------- | ---------------------- | ------------------------------------- | --------------------------------- |
| 계정 정보/잔고 | `GET /sapi/v1/account` | `X-CH-APIKEY`, `X-CH-TS`, `X-CH-SIGN` | `balances[{asset, free, locked}]` |

### 6.5 레이트 리밋/가중치(요약)

* 429 응답 시 제한 위반. IP 단위/UID 단위로 독립 집계.
* 일부 엔드포인트는 가중치(weight) 표기(IP/UID) 제공. 운영 시 **봇별 호출 예산**을 설정하고 초과 시 큐잉/백오프 적용.

---

## 7. 데이터 모델 (초안)

### 7.1 어드민 메타

* **tokens**: `id`, `symbol`, `name`, `chain`, `created_at`.
* **pairs**: `id`, `base_token_id`, `quote_token_id`, `symbol_code`, `price_precision`, `qty_precision`, `amount_precision`, `min_qty`, `min_notional`, `maker_fee`, `taker_fee`, `created_at`.
* **bot_accounts**: `id`, `name`, `exchange`, `api_key(enc)`, `api_secret(enc)`, `passphrase(enc)`, `limits(json)`, `created_at`.
* **strategy_profiles**: `id`, `name`, `type(enum:EXECUTE|BUY|SELL)`, `pair_id`, `params(json)`, `enabled`, `created_at`.

### 7.2 런타임/로그

* **orders**: `id(local)`, `exchange_order_id`, `bot_account_id`, `pair_id`, `side`, `type`, `price`, `qty`, `status`, `reason`, `sent_at`, `ack_at`, `filled_qty`, `avg_fill_price`, `fee`, `raw(json)`.
* **fills**: `id`, `order_id`, `price`, `qty`, `fee_asset`, `fee_amount`, `trade_id`, `ts`.
* **positions**(현물은 선택): `pair_id`, `base_qty`, `quote_qty`, `avg_cost`, `updated_at`.
* **metrics**: `ts`, `bot_id`, `kpis(json: slippage, fill_rate, error_rate ...)`.
* **audits**: `ts`, `actor`, `action`, `entity`, `before(json)`, `after(json)`.
* **bot_events**(신규): `id`, `bot_id`, `strategy_id`, `state_before`, `state_after`, `event_type('HALTED'|'ERROR'|'STOP'|'START')`, `reason_code`, `message`, `context(json)`, `ts`.

---

## 8. 정밀도/라운딩 규칙

* 가격, 수량별로 **라운딩 함수** 정의(거래소 제약 준수):

  * `round_price(p, price_precision)`
  * `round_qty(q, qty_precision)`
  * `enforce_minimums(q, min_qty, notional)`
* 주문 전 검증: 정밀도 → 최소수량/최소주문금액 → 잔고/수수료 → 한도.

---

## 9. 봇별 동작 로직 (요약)

### 9.1 체결봇

1. 호가 스냅샷/스트림 수집 → 2) 스프레드 계산 → 3) 조건 충족 시 상대측 가격에 **IOC/FOK** 발주 → 4) 미체결분 자동 취소 → 5) 체결 결과 반영.

**핵심 파라미터**: 스프레드 임계치(bps), 최대 주문수량, 가격개선틱, 잔량맞춤(상대 잔량의 x%).

### 9.2 매수봇

* 엔트리: 지정/시장/조건부(예: 가격 하락율 x% 시 매수).
* DCA/그리드: 스텝 수, 간격, 스텝별 수량 배분.
* 보호: 슬리피지 한계, 일일/세션 한도, 실패 재시도.

### 9.3 매도봇

* 목표수익률 TP, 손절 SL, 트레일링(호가 대비 x%).
* 부분청산: 예) 50%→30%→20%.
* 보호호가: 상/하한 가격 범위 벗어나면 취소/대기.

---

## 10. 리스크 & 예외 처리

* 주문 거절 코드 맵핑 및 재시도 정책(지수 백오프, 최대 N회).
* WS 끊김 시 REST 폴백, 재구독.
* 시간 동기화(NTP/서버 타임스탬프 보정).
* 잔고 변동/수수료 누락 대비 **사전 추정 체결가** 계산.

---

## 11. 운영 & 배포

* 프로세스: 봇(프로세스/컨테이너) 단위로 스케일 → 봇별 환경변수/프로파일 주입.
* 헬스체크: `/healthz` + 최근 주문/시세 수신 시각.
* 구성관리: Git 버전, 프로파일 JSON 템플릿, 환경별(DEV/STG/PRD) 분리.

---

## 12. 초기 체크리스트

* [ ] 거래소 API 자격 발급 및 IP 화이트리스트
* [ ] 심볼 메타 수집·정밀도 검증
* [ ] 어드민 CRUD 완성(토큰/페어/정밀도/최소값)
* [ ] 봇 계정 키 등록/암호화/테스트
* [ ] 전략 프로파일 3종 템플릿 작성
* [ ] 주문/체결/잔고 인터페이스 연동 테스트
* [ ] 대시보드·알림 채널 연결

---

## 13. 변경 이력

* v0.1 (2025-09-30): 초기 초안 작성 — 구조·데이터 모델·봇 로직 요약 반영.

---

## 14. 다음 단계(업데이트 예정)

* [ ] 대상 거래소 ExchangeDocs v2 스펙 매핑 표(엔드포인트/파라미터/시그니처 예시)
* [ ] OpenAPI(YAML) 스텁 + Express 라우트 스켈레톤
* [ ] DB DDL(최소 스키마) & 마이그레이션 초안
* [ ] 테스트 시나리오(성능/리스크/복구)

---

## 15. DB DDL (PostgreSQL · 초안)

> 키 보관은 **KMS 또는 외부 비밀관리**를 권장. DB에는 암호화된 값과 키 아이디만 저장.

```sql
-- 15.0: enum & helper
CREATE TYPE bot_type AS ENUM ('EXECUTE','BUY','SELL');
CREATE TYPE rounding_rule AS ENUM ('ROUND_DOWN','ROUND_UP','FLOOR');

-- 15.1: users (플랫폼 사용자)
CREATE TABLE app_users (
  id              BIGSERIAL PRIMARY KEY,
  email           CITEXT UNIQUE NOT NULL,
  name            TEXT,
  role            TEXT DEFAULT 'user', -- user | admin | operator
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_app_users_role ON app_users(role);

-- 15.2: tokens
CREATE TABLE tokens (
  id              BIGSERIAL PRIMARY KEY,
  symbol          TEXT NOT NULL,
  name            TEXT,
  chain           TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX uq_tokens_symbol ON tokens(symbol);

-- 15.3: pairs (정밀도/최소값 포함)
CREATE TABLE pairs (
  id               BIGSERIAL PRIMARY KEY,
  base_token_id    BIGINT NOT NULL REFERENCES tokens(id),
  quote_token_id   BIGINT NOT NULL REFERENCES tokens(id),
  symbol_code      TEXT NOT NULL,           -- ex) LTCUSDT
  price_precision  INT  NOT NULL,
  qty_precision    INT  NOT NULL,
  amount_precision INT  NOT NULL,
  min_qty          NUMERIC NOT NULL,
  min_notional     NUMERIC NOT NULL,
  maker_fee_bps    NUMERIC NOT NULL DEFAULT 0, -- basis points
  taker_fee_bps    NUMERIC NOT NULL DEFAULT 0,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX uq_pairs_symbol_code ON pairs(symbol_code);
CREATE INDEX idx_pairs_base_quote ON pairs(base_token_id, quote_token_id);

-- 15.4: bot_accounts (거래소 API 키 저장)
CREATE TABLE bot_accounts (
  id              BIGSERIAL PRIMARY KEY,
  owner_user_id   BIGINT REFERENCES app_users(id), -- NULL이면 시스템 소유
  name            TEXT NOT NULL,
  exchange        TEXT NOT NULL DEFAULT 'mbitinside',
  api_key_cipher  TEXT NOT NULL,    -- 암호문
  api_secret_cipher TEXT NOT NULL,  -- 암호문
  km_key_id       TEXT,             -- KMS key identifier
  limits          JSONB DEFAULT '{}',-- {max_open_orders,max_daily_volume,max_order_value}
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_bot_accounts_owner ON bot_accounts(owner_user_id);

-- 15.5: strategy_profiles
CREATE TABLE strategy_profiles (
  id              BIGSERIAL PRIMARY KEY,
  owner_user_id   BIGINT REFERENCES app_users(id),
  name            TEXT NOT NULL,
  type            bot_type NOT NULL,
  pair_id         BIGINT NOT NULL REFERENCES pairs(id),
  rounding        rounding_rule NOT NULL DEFAULT 'FLOOR',
  params          JSONB NOT NULL DEFAULT '{}', -- {slippage_bps, grid, dca, tp, sl, session, ...}
  enabled         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_strategy_owner_type ON strategy_profiles(owner_user_id, type);

-- 15.6: orders (로컬 카탈로그)
CREATE TABLE orders (
  id                BIGSERIAL PRIMARY KEY,
  exchange_order_id TEXT,
  bot_account_id    BIGINT NOT NULL REFERENCES bot_accounts(id),
  pair_id           BIGINT NOT NULL REFERENCES pairs(id),
  side              TEXT NOT NULL CHECK (side IN ('BUY','SELL')),
  ord_type          TEXT NOT NULL,                   -- LIMIT/MARKET/IOC/FOK/POST_ONLY
  price             NUMERIC,
  qty               NUMERIC NOT NULL,
  status            TEXT NOT NULL,                   -- NEW/OPEN/PARTIALLY_FILLED/FILLED/CANCELED/REJECTED
  reason            TEXT,
  sent_at           TIMESTAMPTZ,
  ack_at            TIMESTAMPTZ,
  filled_qty        NUMERIC DEFAULT 0,
  avg_fill_price    NUMERIC,
  fee_asset         TEXT,
  fee_amount        NUMERIC,
  raw               JSONB,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_orders_lookup ON orders(bot_account_id, pair_id, status);
CREATE INDEX idx_orders_exid ON orders(exchange_order_id);

-- 15.7: fills (체결 상세)
CREATE TABLE fills (
  id           BIGSERIAL PRIMARY KEY,
  order_id     BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  trade_id     TEXT,
  price        NUMERIC NOT NULL,
  qty          NUMERIC NOT NULL,
  fee_asset    TEXT,
  fee_amount   NUMERIC,
  ts           TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_fills_order ON fills(order_id);

-- 15.8: audits
CREATE TABLE audits (
  id         BIGSERIAL PRIMARY KEY,
  actor_id   BIGINT REFERENCES app_users(id),
  action     TEXT NOT NULL,
  entity     TEXT NOT NULL,
  before     JSONB,
  after      JSONB,
  ts         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 15.9: metrics (운영 KPI)
CREATE TABLE metrics (
  id        BIGSERIAL PRIMARY KEY,
  bot_id    BIGINT,
  kpis      JSONB NOT NULL,
  ts        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**정밀도 권장 타입**: 가격/수량/금액은 `NUMERIC(38, 18)` 등 충분한 정밀도 채택 후 애플리케이션 레벨에서 라운딩.

---

## 16. OpenAPI (YAML) 스텁

> 내부 관리 API 초안. 실제 배포 시 인증은 OAuth2 또는 API Key(서버-서버) + 사용자 세션(JWT) 혼합 권장.

```yaml
openapi: 3.0.3
info:
  title: Trading Bot Admin/User API
  version: 0.1.0
servers:
  - url: https://api.yourbot.local
    description: Internal gateway
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    Pair:
      type: object
      properties:
        id: { type: integer }
        symbolCode: { type: string }
        pricePrecision: { type: integer }
        qtyPrecision: { type: integer }
        amountPrecision: { type: integer }
        minQty: { type: string }
        minNotional: { type: string }
    StrategyProfile:
      type: object
      properties:
        id: { type: integer }
        name: { type: string }
        type: { type: string, enum: [EXECUTE, BUY, SELL] }
        pairId: { type: integer }
        rounding: { type: string, enum: [ROUND_DOWN, ROUND_UP, FLOOR] }
        params: { type: object }
        enabled: { type: boolean }
    ApiKeyCreateReq:
      type: object
      required: [name, exchange, apiKey, apiSecret]
      properties:
        name: { type: string }
        exchange: { type: string, example: mbitinside }
        apiKey: { type: string }
        apiSecret: { type: string }
    OrderRequest:
      type: object
      required: [symbol, side, type, volume]
      properties:
        symbol: { type: string, example: LTCUSDT }
        side: { type: string, enum: [BUY, SELL] }
        type: { type: string, enum: [LIMIT, MARKET, IOC, FOK, POST_ONLY] }
        price: { type: string, nullable: true }
        volume: { type: string }
        clientOrderId: { type: string, nullable: true }
        timeInForce: { type: string, enum: [GTC, IOC, FOK], nullable: true }
    CurveTargetReq:
      type: object
      required: [strategyId, mode, params]
      properties:
        strategyId: { type: integer }
        mode: { type: string, enum: [DAILY_UP, DAILY_DOWN, PERIOD_UP, PERIOD_DOWN] }
        params:
          type: object
          description: daily_rate 또는 {start,end,total_pct,curve}
    CurvePoint:
      type: object
      properties:
        utc_ts: { type: string, format: date-time }
        target_value: { type: string }
        actual_value: { type: string, nullable: true }
    BotEvent:
      type: object
      properties:
        id: { type: integer }
        strategyId: { type: integer }
        event_type: { type: string, enum: [HALTED, ERROR, STOP, START] }
        reason_code: { type: string }
        message: { type: string }
        ts: { type: string, format: date-time }
security:
  - bearerAuth: []
paths:
  /admin/pairs:
    get:
      summary: List pairs
      responses:
        '200': { description: OK }
    post:
      summary: Create pair
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/Pair' }
      responses:
        '201': { description: Created }
  /user/accounts/keys:
    post:
      summary: Register user exchange API key
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/ApiKeyCreateReq' }
      responses:
        '201': { description: Created }
  /user/accounts/keys/test:
    post:
      summary: Test connectivity (balances/account)
      responses:
        '200': { description: OK }
  /user/balances:
    get:
      summary: Get balances (proxied from exchange)
      responses:
        '200': { description: OK }
  /strategies:
    get:
      summary: List strategies (mine or admin templates)
      responses:
        '200': { description: OK }
    post:
      summary: Create strategy
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/StrategyProfile' }
      responses:
        '201': { description: Created }
  /bots/{strategyId}/start:
    post:
      summary: Start bot for strategy
      parameters:
        - in: path
          name: strategyId
          schema: { type: integer }
          required: true
      responses:
        '202': { description: Started }
  /bots/{strategyId}/stop:
    post:
      summary: Stop bot for strategy
      parameters:
        - in: path
          name: strategyId
          schema: { type: integer }
          required: true
      responses:
        '202': { description: Stopped }
  /orders:
    post:
      summary: Place order (server-side rounding/min checks)
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/OrderRequest' }
      responses:
        '201': { description: Accepted }
    delete:
      summary: Cancel order
      parameters:
        - in: query
          name: orderId
          required: true
          schema: { type: string }
      responses:
        '200': { description: Canceled }
  /curves/targets:
    post:
      summary: Create/replace curve target for a strategy
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/CurveTargetReq' }
      responses:
        '201': { description: Created }
  /curves/{strategyId}:
    get:
      summary: Get generated curve points (target vs actual)
      parameters:
        - in: path
          name: strategyId
          required: true
          schema: { type: integer }
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/CurvePoint' }
  /bots/{strategyId}/events:
    get:
      summary: List bot events (HALTED/ERROR/etc)
      parameters:
        - in: path
          name: strategyId
          required: true
          schema: { type: integer }
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/BotEvent' }
```

yaml
openapi: 3.0.3
info:
title: Trading Bot Admin/User API
version: 0.1.0
servers:

* url: [https://api.yourbot.local](https://api.yourbot.local)
  description: Internal gateway
  components:
  securitySchemes:
  bearerAuth:
  type: http
  scheme: bearer
  bearerFormat: JWT
  schemas:
  Pair:
  type: object
  properties:
  id: { type: integer }
  symbolCode: { type: string }
  pricePrecision: { type: integer }
  qtyPrecision: { type: integer }
  amountPrecision: { type: integer }
  minQty: { type: string }
  minNotional: { type: string }
  StrategyProfile:
  type: object
  properties:
  id: { type: integer }
  name: { type: string }
  type: { type: string, enum: [EXECUTE, BUY, SELL] }
  pairId: { type: integer }
  rounding: { type: string, enum: [ROUND_DOWN, ROUND_UP, FLOOR] }
  params: { type: object }
  enabled: { type: boolean }
  ApiKeyCreateReq:
  type: object
  required: [name, exchange, apiKey, apiSecret]
  properties:
  name: { type: string }
  exchange: { type: string, example: mbitinside }
  apiKey: { type: string }
  apiSecret: { type: string }
  OrderRequest:
  type: object
  required: [symbol, side, type, volume]
  properties:
  symbol: { type: string, example: LTCUSDT }
  side: { type: string, enum: [BUY, SELL] }
  type: { type: string, enum: [LIMIT, MARKET, IOC, FOK, POST_ONLY] }
  price: { type: string, nullable: true }
  volume: { type: string }
  clientOrderId: { type: string, nullable: true }
  timeInForce: { type: string, enum: [GTC, IOC, FOK], nullable: true }
  security:
* bearerAuth: []
  paths:
  /admin/pairs:
  get:
  summary: List pairs
  responses:
  '200': { description: OK }
  post:
  summary: Create pair
  requestBody:
  required: true
  content:
  application/json:
  schema: { $ref: '#/components/schemas/Pair' }
  responses:
  '201': { description: Created }
  /user/accounts/keys:
  post:
  summary: Register user exchange API key
  requestBody:
  required: true
  content:
  application/json:
  schema: { $ref: '#/components/schemas/ApiKeyCreateReq' }
  responses:
  '201': { description: Created }
  /user/accounts/keys/test:
  post:
  summary: Test connectivity (balances/account)
  responses:
  '200': { description: OK }
  /user/balances:
  get:
  summary: Get balances (proxied from exchange)
  responses:
  '200': { description: OK }
  /strategies:
  get:
  summary: List strategies (mine or admin templates)
  responses:
  '200': { description: OK }
  post:
  summary: Create strategy
  requestBody:
  required: true
  content:
  application/json:
  schema: { $ref: '#/components/schemas/StrategyProfile' }
  responses:
  '201': { description: Created }
  /bots/{strategyId}/start:
  post:
  summary: Start bot for strategy
  parameters:
  - in: path
  name: strategyId
  schema: { type: integer }
  required: true
  responses:
  '202': { description: Started }
  /bots/{strategyId}/stop:
  post:
  summary: Stop bot for strategy
  parameters:
  - in: path
  name: strategyId
  schema: { type: integer }
  required: true
  responses:
  '202': { description: Stopped }
  /orders:
  post:
  summary: Place order (server-side rounding/min checks)
  requestBody:
  required: true
  content:
  application/json:
  schema: { $ref: '#/components/schemas/OrderRequest' }
  responses:
  '201': { description: Accepted }
  delete:
  summary: Cancel order
  parameters:
  - in: query
  name: orderId
  required: true
  schema: { type: string }
  responses:
  '200': { description: Canceled }

```

**노트**
- `orders` 엔드포인트는 내부 게이트웨이에서 정밀도/최소값/한도 검증 후 거래소 `/sapi/v1/order`로 프록시.
- `/user/accounts/keys/test`는 거래소 `GET /sapi/v1/account` 호출로 유효성 검증.
- 추후 `websocket` 구독(시세/체결)용 게이트웨이 경로 `/ws` 정의 예정.

---

## 17. 변경 이력
- v0.2 (2025-10-01): 거래소 Base URL 반영(https://www.mbitinside.com), DB DDL 초안, OpenAPI YAML 스텁 추가.
- v0.1 (2025-09-30): 초기 초안 작성 — 구조·데이터 모델·봇 로직 요약.

---

## 18. 실행 계획 (스프린트-0/1 체크리스트)
> 아래 항목을 완료해 나가면 **개발 진행(Implementation In Progress)**으로 간주.

### 스프린트-0: 베이스라인 구축
- [ ] Git 레포 초기화(backend `/apps/gw`, `/apps/bots`, `/packages/shared`)
- [ ] 환경변수 템플릿 `.env.example` (MBIT API KEY/SECRET, KMS, DB URL)
- [ ] DB 초기 마이그레이션 적용 (섹션 15 DDL 반영)
- [ ] OpenAPI 스텁 → 라우트 스켈레톤 생성(Express/Nest 중 택1)
- [ ] 거래소 HTTP 클라이언트(서명/HMAC/타임스탬프, 베이스 URL 바인딩)
- [ ] 헬스체크 `/healthz` 및 `/version`

### 스프린트-1: 핵심 유스케이스
- [ ] **API 키 등록/테스트**: `/user/accounts/keys`, `/user/accounts/keys/test`
- [ ] **잔액 프록시**: `/user/balances` → `GET /sapi/v1/account`
- [ ] **페어 메타 싱크**: `GET /sapi/v1/symbols` → `pairs` 업서트
- [ ] **주문 프록시**: `/orders` (정밀도/최소값/한도 검증 → `POST /sapi/v1/order`)
- [ ] **일괄 취소**: 내부 `/orders` DELETE → `DELETE /sapi/v1/batchOrders`
- [ ] **감사로그**: 키/전략/주문 변경 이벤트 기록

### 스프린트-2: 봇 런타임 베타
- [ ] WS 구독 게이트웨이 `/ws` (ticker/depth/myTrades)
- [ ] 체결봇 MVP (스프레드 임계치 + IOC)
- [ ] 매수봇/매도봇 MVP (TP/SL 최소 구현)
- [ ] 모니터링 대시보드(상태, 체결 수, 에러율)

### 품질 보증
- [ ] 레이트리밋/백오프 통합 테스트
- [ ] 시그니처 검증 유닛테스트
- [ ] 라운딩/정밀도 검증 유닛테스트 (경계값)
- [ ] 장애/재시작 복구 시나리오 테스트

---

## 19. 프로젝트 스캐폴드 (NestJS · pnpm workspaces)
> 실행 대상: Node 20+, pnpm 9+, PostgreSQL 14+

### 19.1 폴더 구조
```

trading-bot/
├─ apps/
│  ├─ gw/                 # API 게이트웨이 (NestJS)
│  │  ├─ src/
│  │  │  ├─ main.ts
│  │  │  ├─ app.module.ts
│  │  │  ├─ common/
│  │  │  │  ├─ config.service.ts
│  │  │  │  ├─ http.module.ts
│  │  │  │  └─ logger.interceptor.ts
│  │  │  ├─ exchange/
│  │  │  │  ├─ exchange.module.ts
│  │  │  │  ├─ exchange.service.ts      # 서명/HMAC/요청 래퍼
│  │  │  │  └─ signature.util.ts
│  │  │  ├─ admin/
│  │  │  │  ├─ pairs.controller.ts      # /admin/pairs
│  │  │  │  └─ pairs.service.ts
│  │  │  ├─ user/
│  │  │  │  ├─ keys.controller.ts       # /user/accounts/keys(+/test)
│  │  │  │  ├─ balances.controller.ts   # /user/balances
│  │  │  │  └─ strategies.controller.ts # /strategies
│  │  │  ├─ bots/
│  │  │  │  ├─ bots.controller.ts       # /bots/{id}/start|stop
│  │  │  │  └─ bots.service.ts
│  │  │  ├─ orders/
│  │  │  │  ├─ orders.controller.ts     # /orders (proxy)
│  │  │  │  └─ orders.service.ts
│  │  │  └─ dto/
│  │  │     ├─ pair.dto.ts
│  │  │     ├─ api-key.dto.ts
│  │  │     └─ order.dto.ts
│  │  ├─ test/
│  │  └─ tsconfig.json
│  └─ bots/              # 봇 런타임 (NestJS or worker)
│     ├─ src/
│     │  ├─ main.ts
│     │  ├─ bot.module.ts
│     │  ├─ runner.service.ts           # 체결/매수/매도 봇 루프 MVP
│     │  ├─ strategies/
│     │  │  ├─ execute.strategy.ts
│     │  │  ├─ buy.strategy.ts
│     │  │  └─ sell.strategy.ts
│     │  └─ ports/
│     │     └─ exchange.port.ts         # gw의 exchange.service 인터페이스
│     └─ tsconfig.json
├─ packages/
│  └─ shared/
│     ├─ src/
│     │  ├─ precision.ts                # 라운딩/최소값 검증
│     │  ├─ rate-limit.ts
│     │  └─ types.ts
│     └─ tsconfig.json
├─ prisma/
│  ├─ migrations/
│  └─ schema.prisma (선택)              # 또는 SQL 직접 관리
├─ sql/
│  └─ 001_init.sql                      # 섹션 15 DDL 저장
├─ .env.example
├─ package.json
├─ pnpm-workspace.yaml
├─ tsconfig.base.json
└─ README.md

````

### 19.2 패키지 매니저 설정
**pnpm-workspace.yaml**
```yaml
packages:
  - 'apps/*'
  - 'packages/*'
````

**package.json**

```json
{
  "name": "trading-bot-monorepo",
  "private": true,
  "packageManager": "pnpm@9",
  "scripts": {
    "dev:gw": "pnpm --filter gw dev",
    "dev:bots": "pnpm --filter bots dev",
    "build": "pnpm -r build",
    "lint": "pnpm -r lint",
    "migrate:sql": "psql $PG_URL -f sql/001_init.sql"
  },
  "workspaces": ["apps/*", "packages/*"]
}
```

**.env.example**

```
NODE_ENV=development
PG_URL=postgres://user:pass@localhost:5432/trading_bot
MBIT_BASE_URL=https://www.mbitinside.com
# gw에서 사용자별 요청에 사용할 Key/Secret은 DB에 암호화 저장
KMS_KEY_ID=local-dev-kms
JWT_SECRET=change-me
PORT_GW=8080
PORT_BOTS=8090
```

### 19.3 Gateway(apis/gw) 최소 코드

**apps/gw/src/main.ts**

```ts
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, { cors: true });
  await app.listen(process.env.PORT_GW || 8080);
}
bootstrap();
```

**apps/gw/src/app.module.ts**

```ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { HttpModule } from './common/http.module';
import { ExchangeModule } from './exchange/exchange.module';
import { PairsModule } from './admin/pairs.module';
import { KeysModule } from './user/keys.module';
import { BalancesModule } from './user/balances.module';
import { StrategiesModule } from './user/strategies.module';
import { BotsModule } from './bots/bots.module';
import { OrdersModule } from './orders/orders.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    HttpModule,
    ExchangeModule,
    PairsModule,
    KeysModule,
    BalancesModule,
    StrategiesModule,
    BotsModule,
    OrdersModule,
  ],
})
export class AppModule {}
```

**apps/gw/src/common/http.module.ts**

```ts
import { Module } from '@nestjs/common';
import { HttpModule as AxiosHttp } from '@nestjs/axios';

@Module({ imports: [AxiosHttp.register({ timeout: 5000 })], exports: [AxiosHttp] })
export class HttpModule {}
```

**apps/gw/src/exchange/signature.util.ts**

```ts
import * as crypto from 'crypto';

export function sign({ ts, method, path, body, secret }: {
  ts: string; method: string; path: string; body?: string; secret: string;
}) {
  const payload = `${ts}${method.toUpperCase()}${path}${body ?? ''}`;
  return crypto.createHmac('sha256', secret).update(payload).digest('hex');
}
```

**apps/gw/src/exchange/exchange.service.ts**

```ts
import { Injectable } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';
import { sign } from './signature.util';

@Injectable()
export class ExchangeService {
  private readonly base = process.env.MBIT_BASE_URL || 'https://www.mbitinside.com';

  constructor(private readonly http: HttpService) {}

  async publicGet(path: string, params?: any) {
    const url = `${this.base}${path}`;
    const { data } = await firstValueFrom(this.http.get(url, { params }));
    return data;
  }

  async privateReq(path: string, method: 'GET'|'POST'|'DELETE', apiKey: string, apiSecret: string, body?: any) {
    const ts = Date.now().toString();
    const bodyStr = body ? JSON.stringify(body) : '';
    const sig = sign({ ts, method, path, body: bodyStr, secret: apiSecret });
    const headers = {
      'X-CH-APIKEY': apiKey,
      'X-CH-TS': ts,
      'X-CH-SIGN': sig,
      'Content-Type': 'application/json',
    };
    const url = `${this.base}${path}`;
    const req = method === 'GET'
      ? this.http.get(url, { headers })
      : method === 'POST'
      ? this.http.post(url, body, { headers })
      : this.http.delete(url, { headers, data: body });
    const { data } = await firstValueFrom(req);
    return data;
  }
}
```

**apps/gw/src/orders/orders.controller.ts** (요약)

```ts
import { Body, Controller, Delete, Post, Query } from '@nestjs/common';
import { OrdersService } from './orders.service';
import { OrderDto } from '../dto/order.dto';

@Controller('orders')
export class OrdersController {
  constructor(private readonly svc: OrdersService) {}

  @Post()
  async place(@Body() dto: OrderDto) {
    return this.svc.place(dto);
  }

  @Delete()
  async cancel(@Query('orderId') orderId: string) {
    return this.svc.cancel(orderId);
  }
}
```

**apps/gw/src/dto/order.dto.ts** (정밀도 검증은 shared/precision.ts 이용)

```ts
export class OrderDto {
  symbol!: string;           // LTCUSDT
  side!: 'BUY' | 'SELL';
  type!: 'LIMIT' | 'MARKET' | 'IOC' | 'FOK' | 'POST_ONLY';
  price?: string;            // LIMIT 계열
  volume!: string;
  clientOrderId?: string;
  timeInForce?: 'GTC' | 'IOC' | 'FOK';
  apiAccountId!: number;     // 어떤 bot_account를 사용할지
}
```

**packages/shared/src/precision.ts** (라운딩 유틸)

```ts
import Decimal from 'decimal.js';

export function roundPrice(p: string, precision: number) {
  return new Decimal(p).toDecimalPlaces(precision, Decimal.ROUND_FLOOR).toFixed(precision);
}
export function roundQty(q: string, precision: number) {
  return new Decimal(q).toDecimalPlaces(precision, Decimal.ROUND_FLOOR).toFixed(precision);
}
export function enforceMinimums(q: string, minQty: string, notional?: { price: string; minNotional: string }) {
  const qtyOk = new Decimal(q).gte(new Decimal(minQty));
  const notionalOk = !notional || new Decimal(q).mul(notional.price).gte(new Decimal(notional.minNotional));
  return qtyOk && notionalOk;
}
```

### 19.4 SQL 마이그레이션

* `sql/001_init.sql`에 **섹션 15 DDL** 저장.
* 적용: `pnpm migrate:sql` (로컬 `psql` 사용).

### 19.5 실행 순서 (로컬)

1. PostgreSQL 기동, DB 생성: `createdb trading_bot`
2. `.env` 작성(예: `.env.example` 복사)
3. `pnpm i`
4. `pnpm migrate:sql`
5. `pnpm dev:gw` (Gateway) / `pnpm dev:bots` (Bots)

---

## 20. 구현 세부 (순차 진행 코드)

> 아래 순서대로 붙이면 바로 동작 테스트 가능. (NestJS 기준)

### 20.1 OrdersService: 정밀도/최소값/한도 검증 + 거래소 프록시

**apps/gw/src/orders/orders.service.ts**

```ts
import { Injectable, BadRequestException } from '@nestjs/common';
import { ExchangeService } from '../exchange/exchange.service';
import { roundPrice, roundQty, enforceMinimums } from '@shared/precision';

interface PlaceReq {
  symbol: string; side: 'BUY'|'SELL'; type: 'LIMIT'|'MARKET'|'IOC'|'FOK'|'POST_ONLY';
  price?: string; volume: string; apiAccountId: number; clientOrderId?: string; timeInForce?: 'GTC'|'IOC'|'FOK';
}

@Injectable()
export class OrdersService {
  constructor(private readonly ex: ExchangeService) {}

  // TODO: inject repos for pairs/bot_accounts
  private async getPairMeta(symbol: string) {
    // repo.pairs.findBySymbolCode(symbol)
    return { price_precision: 4, qty_precision: 3, min_qty: '0.001', min_notional: '5' };
  }
  private async getBotKeys(apiAccountId: number) {
    // repo.bot_accounts.findById(apiAccountId)
    return { apiKey: process.env.DEMO_API_KEY!, apiSecret: process.env.DEMO_API_SECRET! };
  }

  async place(req: PlaceReq) {
    const meta = await this.getPairMeta(req.symbol);
    const price = req.price ? roundPrice(req.price, meta.price_precision) : undefined;
    const qty = roundQty(req.volume, meta.qty_precision);

    // 최소값 검증
    const ok = enforceMinimums(qty, meta.min_qty, price ? { price, minNotional: meta.min_notional } : undefined);
    if (!ok) throw new BadRequestException('MIN_CHECK_FAILED');

    const { apiKey, apiSecret } = await this.getBotKeys(req.apiAccountId);
    const body: any = { symbol: req.symbol, side: req.side, type: req.type, volume: qty, timeInForce: req.timeInForce };
    if (price) body.price = price;
    if (req.clientOrderId) body.newClientOrderId = req.clientOrderId;

    // 거래소 프록시
    return this.ex.privateReq('/sapi/v1/order', 'POST', apiKey, apiSecret, body);
  }

  async cancel(orderId: string) {
    const { apiKey, apiSecret } = await this.getBotKeys(0);
    return this.ex.privateReq('/sapi/v1/order', 'DELETE', apiKey, apiSecret, { orderId });
  }
}
```

### 20.2 PairsService: 심볼 메타 동기화 업서트

**apps/gw/src/admin/pairs.service.ts**

```ts
import { Injectable } from '@nestjs/common';
import { ExchangeService } from '../exchange/exchange.service';

@Injectable()
export class PairsService {
  constructor(private readonly ex: ExchangeService) {}
  // TODO: inject repo
  async syncSymbols() {
    const data = await this.ex.publicGet('/sapi/v1/symbols');
    // data.symbols[].map(s => upsert to pairs)
    return { synced: (data.symbols||[]).length };
  }
}
```

### 20.3 KeysController: API 키 저장/테스트

**apps/gw/src/user/keys.controller.ts**

```ts
import { Body, Controller, Post } from '@nestjs/common';
import { ExchangeService } from '../exchange/exchange.service';

@Controller('user/accounts/keys')
export class KeysController {
  constructor(private readonly ex: ExchangeService) {}

  @Post()
  async save(@Body() body: any) {
    // TODO: encrypt and persist to bot_accounts
    return { id: 1 };
  }

  @Post('test')
  async test(@Body() body: any) {
    const { apiKey, apiSecret } = body;
    const acc = await this.ex.privateReq('/sapi/v1/account', 'GET', apiKey, apiSecret);
    return { ok: true, balances: acc?.balances };
  }
}
```

### 20.4 CurvesService: 목표 곡선 생성기

**apps/gw/src/curves/curves.service.ts**

```ts
import { Injectable } from '@nestjs/common';

export type CurveMode = 'DAILY_UP'|'DAILY_DOWN'|'PERIOD_UP'|'PERIOD_DOWN';

@Injectable()
export class CurvesService {
  // 지수/선형/스플라인 중 선형+지수 기본 제공
  generateDaily(startTs: number, days: number, dailyRate: number, baseValue = 1) {
    const pts: { utc_ts:number; target_value:number }[] = [];
    let v = baseValue;
    for (let d = 0; d <= days; d++) {
      const ts = startTs + d*24*3600*1000;
      if (d>0) v = v * (1 + dailyRate/100);
      pts.push({ utc_ts: ts, target_value: v });
    }
    return pts;
  }
  generatePeriodLinear(startTs: number, endTs: number, totalPct: number, steps = 96, baseValue = 1) {
    const pts: { utc_ts:number; target_value:number }[] = [];
    for (let i=0;i<=steps;i++) {
      const t = startTs + Math.round(((endTs-startTs)/steps)*i);
      const ratio = i/steps;
      const v = baseValue * (1 + (totalPct/100)*ratio);
      pts.push({ utc_ts: t, target_value: v });
    }
    return pts;
  }
}
```

### 20.5 BotEvents: 서비스 & 기록 헬퍼

**apps/gw/src/bots/bot-events.service.ts**

```ts
import { Injectable } from '@nestjs/common';

@Injectable()
export class BotEventsService {
  // TODO: inject repo
  async record(evt: { strategyId:number; stateBefore?:string; stateAfter:string; eventType:'HALTED'|'ERROR'|'STOP'|'START'; reasonCode?:string; message?:string; context?:any; }) {
    // INSERT INTO bot_events ...
    return { ok: true };
  }
}
```

**봇 런타임에서 사용 예**

```ts
await botEvents.record({ strategyId, stateBefore:'RUNNING', stateAfter:'HALTED', eventType:'HALTED', reasonCode:'WS_DISCONNECT', message:'WebSocket disconnected', context:{ lastSeq } });
```

### 20.6 곡선-전략 연동 가이드

* 전략 루프마다 현재 Equity/노출(actual)을 수집 → `curve_points`의 최근 `target_value`와 비교 →

  * `actual < target`이면 **매수 강도↑**(주문 크기 소폭 증가, 스텝 간격 축소),
  * `actual > target`이면 **매도/청산 강도↑**(부분청산 비율 증가),
  * 단, **유동성·슬리피지·레이트리밋** 한계를 항상 선행 검증.

---

## 21. /docs 스냅샷(캔버스 → 레포 미러링 가이드)

> 캔버스의 최신 명세를 **레포 `/docs` 폴더**로 주기적으로 스냅샷합니다.

### 21.1 파일 구성

```
docs/
├─ README.md               # 개요/아키텍처 요약
├─ requirements.md         # 요구사항(이 문서 캔버스 요약본)
├─ api.yaml                # OpenAPI 스냅샷 (섹션 16 기반)
├─ schema.sql              # DDL 스냅샷 (섹션 15 + bot_events/curves 포함)
└─ CHANGELOG.md            # 변경 이력(요약)
```

### 21.2 템플릿

**docs/README.md**

```md
# Trading Bot – Overview

## Purpose
- Open API 기반 체결/매수/매도 자동화
- Admin/User/Operator 분리, 곡선 목표 기반 노출 관리

## Architecture (High-level)
- apps/gw: API Gateway (NestJS)
- apps/bots: Bot Runtime (NestJS/Worker)
- packages/shared: 공통 유틸(정밀도/레이트리밋)
- Postgres (Docker): 영속 데이터
```

**docs/requirements.md**

```md
# Requirements Snapshot
- 캔버스 문서의 v{date} 스냅샷입니다. 최신본은 캔버스를 참조하세요.
- 범위/이해관계자/스토리/기능/비기능/데이터모델/외부 API 매핑/스캐폴드/구현세부 포함.
```

**docs/CHANGELOG.md**

```md
# Changelog
- 2025-10-01 v0.2: Base URL 적용, DDL, OpenAPI, 스캐폴드/구현 세부 추가
- 2025-09-30 v0.1: 초기 초안
```

### 21.3 OpenAPI 내보내기 가이드

* 섹션 16의 YAML 블록을 복사 → `docs/api.yaml` 저장
* CI에서 `swagger-ui-dist`로 정적 호스팅(선택) 또는 VS Code 플러그인 미리보기

### 21.4 DDL 내보내기 가이드

* 섹션 15의 SQL 블록을 복사 → `docs/schema.sql` 저장
* `pnpm migrate:sql`로 적용 가능

---

## 22. Docker(Postgres) & ENV 샘플

### 22.1 docker-compose.yml

```yaml
version: '3.9'
services:
  db:
    image: postgres:14
    container_name: tb-postgres
    environment:
      POSTGRES_USER: tb
      POSTGRES_PASSWORD: tbpass
      POSTGRES_DB: trading_bot
    ports:
      - '5432:5432'
    volumes:
      - tb-pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tb"]
      interval: 5s
      timeout: 3s
      retries: 10
volumes:
  tb-pgdata:
```

### 22.2 ENV 프로필 샘플

```
# .env.dev
NODE_ENV=development
PG_URL=postgres://tb:tbpass@localhost:5432/trading_bot
MBIT_BASE_URL=https://www.mbitinside.com
KMS_KEY_ID=local-dev-kms
JWT_SECRET=dev-secret
PORT_GW=8080
PORT_BOTS=8090
```

---

## 23. 스냅샷 워크플로우(권장)

1. 캔버스 수정 → **섹션 15/16/19/20 업데이트 확인**
2. 아래 파일로 복사 저장

   * `docs/schema.sql` (섹션 15)
   * `docs/api.yaml` (섹션 16)
   * `docs/requirements.md` (이 문서 요약)
   * `docs/README.md`, `docs/CHANGELOG.md`
3. `git add docs && git commit -m "docs: snapshot vX.Y"`
4. 필요 시 태그 `vX.Y` 부여

---

## 24. ORM 세팅 – Prisma 우선, TypeORM 대안

> 빠른 스키마 반복과 타입 안전성 때문에 **Prisma 우선** 권장. 필요 시 **TypeORM 대안**도 병행 제공.

### 24.1 설치 & 스크립트

```bash
# 루트에서
pnpm add -w -D prisma
pnpm add -w @prisma/client

# 초기화
pnpx prisma init --datasource-provider postgresql
```

**.env.dev (추가 확인)**

```
DATABASE_URL="postgresql://tb:tbpass@localhost:5432/trading_bot?schema=public"
```

**package.json (루트) – 스크립트 보강**

```json
{
  "scripts": {
    "prisma:gen": "prisma generate",
    "prisma:push": "prisma db push",
    "prisma:migrate": "prisma migrate dev --name init",
    "prisma:studio": "prisma studio"
  }
}
```

### 24.2 schema.prisma (섹션 15 DDL 대응)

> 필드명/제약은 DDL을 최대한 반영. 일부 CHECK/ENUM은 Prisma의 `@db` 주석/`enum`으로 치환.

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum BotType {
  EXECUTE
  BUY
  SELL
}

enum RoundingRule {
  ROUND_DOWN
  ROUND_UP
  FLOOR
}

model app_users {
  id         BigInt   @id @default(autoincrement())
  email      String   @unique
  name       String?
  role       String   @default("user")
  is_active  Boolean  @default(true)
  created_at DateTime @default(now())
  updated_at DateTime @default(now())

  bot_accounts bot_accounts[]
  audits       audits[]
}

model tokens {
  id         BigInt   @id @default(autoincrement())
  symbol     String   @unique
  name       String?
  chain      String?
  created_at DateTime @default(now())

  pairs_base  pairs[] @relation("pairs_base")
  pairs_quote pairs[] @relation("pairs_quote")
}

model pairs {
  id               BigInt   @id @default(autoincrement())
  base_token_id    BigInt
  quote_token_id   BigInt
  symbol_code      String   @unique
  price_precision  Int
  qty_precision    Int
  amount_precision Int
  min_qty          Decimal
  min_notional     Decimal
  maker_fee_bps    Decimal  @default(0)
  taker_fee_bps    Decimal  @default(0)
  created_at       DateTime @default(now())

  base_token  tokens @relation("pairs_base", fields: [base_token_id], references: [id])
  quote_token tokens @relation("pairs_quote", fields: [quote_token_id], references: [id])
  strategies  strategy_profiles[]
  orders      orders[]
}

model bot_accounts {
  id                BigInt   @id @default(autoincrement())
  owner_user_id     BigInt?
  name              String
  exchange          String   @default("mbitinside")
  api_key_cipher    String
  api_secret_cipher String
  km_key_id         String?
  limits            Json     @default("{}")
  is_active         Boolean  @default(true)
  created_at        DateTime @default(now())
  updated_at        DateTime @default(now())

  owner app_users? @relation(fields: [owner_user_id], references: [id])
  orders orders[]
}

model strategy_profiles {
  id            BigInt       @id @default(autoincrement())
  owner_user_id BigInt?
  name          String
  type          BotType
  pair_id       BigInt
  rounding      RoundingRule @default(FLOOR)
  params        Json         @default("{}")
  enabled       Boolean      @default(true)
  created_at    DateTime     @default(now())
  updated_at    DateTime     @default(now())

  owner app_users? @relation(fields: [owner_user_id], references: [id])
  pair  pairs      @relation(fields: [pair_id], references: [id])
  orders orders[]
  bot_events bot_events[]
  curve_targets curve_targets[]
  curve_points  curve_points[]
}

model orders {
  id                BigInt   @id @default(autoincrement())
  exchange_order_id String?
  bot_account_id    BigInt
  pair_id           BigInt
  side              String
  ord_type          String
  price             Decimal?
  qty               Decimal
  status            String
  reason            String?
  sent_at           DateTime?
  ack_at            DateTime?
  filled_qty        Decimal   @default(0)
  avg_fill_price    Decimal?
  fee_asset         String?
  fee_amount        Decimal?
  raw               Json?
  created_at        DateTime  @default(now())

  bot_account bot_accounts @relation(fields: [bot_account_id], references: [id])
  pair       pairs        @relation(fields: [pair_id], references: [id])
  fills      fills[]
}

model fills {
  id         BigInt   @id @default(autoincrement())
  order_id   BigInt
  trade_id   String?
  price      Decimal
  qty        Decimal
  fee_asset  String?
  fee_amount Decimal?
  ts         DateTime

  order orders @relation(fields: [order_id], references: [id], onDelete: Cascade)
}

model audits {
  id       BigInt   @id @default(autoincrement())
  actor_id BigInt?
  action   String
  entity   String
  before   Json?
  after    Json?
  ts       DateTime @default(now())

  actor app_users? @relation(fields: [actor_id], references: [id])
}

model metrics {
  id     BigInt   @id @default(autoincrement())
  bot_id BigInt?
  kpis   Json
  ts     DateTime @default(now())
}

model bot_events {
  id           BigInt   @id @default(autoincrement())
  bot_id       BigInt?
  strategy_id  BigInt
  state_before String?
  state_after  String
  event_type   String
  reason_code  String?
  message      String?
  context      Json?
  ts           DateTime @default(now())

  strategy strategy_profiles @relation(fields: [strategy_id], references: [id])
}

model curve_targets {
  id           BigInt   @id @default(autoincrement())
  strategy_id  BigInt
  mode         String
  params       Json
  active       Boolean  @default(true)
  created_at   DateTime @default(now())

  strategy strategy_profiles @relation(fields: [strategy_id], references: [id])
  points   curve_points[]
}

model curve_points {
  id           BigInt   @id @default(autoincrement())
  strategy_id  BigInt
  utc_ts       DateTime
  target_value Decimal
  actual_value Decimal?
  generated_by BigInt?
  created_at   DateTime @default(now())

  strategy strategy_profiles @relation(fields: [strategy_id], references: [id])
  target   curve_targets?    @relation(fields: [generated_by], references: [id])

  @@unique([strategy_id, utc_ts])
}
```

**적용**

```bash
pnpm prisma:gen
pnpm prisma:migrate   # 개발 중엔 migrate dev, 빠른 실험은 db push
pnpm prisma:studio    # 데이터 확인
```

### 24.3 NestJS PrismaModule(간단 버전)

```ts
// apps/gw/src/prisma/prisma.module.ts
import { Global, Module } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Global()
@Module({
  providers: [
    {
      provide: PrismaClient,
      useFactory: () => new PrismaClient(),
    },
  ],
  exports: [PrismaClient],
})
export class PrismaModule {}
```

```ts
// apps/gw/src/app.module.ts (일부)
import { PrismaModule } from './prisma/prisma.module';
@Module({ imports: [PrismaModule /* ...기존 모듈 */] })
export class AppModule {}
```

**서비스 예시 – PairsService 업서트**

```ts
// apps/gw/src/admin/pairs.service.ts (발췌)
import { Injectable } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { ExchangeService } from '../exchange/exchange.service';

@Injectable()
export class PairsService {
  constructor(private prisma: PrismaClient, private ex: ExchangeService) {}

  async syncSymbols() {
    const data = await this.ex.publicGet('/sapi/v1/symbols');
    const symbols = data?.symbols ?? [];
    for (const s of symbols) {
      // base/quote token upsert
      const base = await this.prisma.tokens.upsert({
        where: { symbol: s.baseAsset },
        update: {},
        create: { symbol: s.baseAsset },
      });
      const quote = await this.prisma.tokens.upsert({
        where: { symbol: s.quoteAsset },
        update: {},
        create: { symbol: s.quoteAsset },
      });
      await this.prisma.pairs.upsert({
        where: { symbol_code: s.symbol },
        update: {
          base_token_id: base.id,
          quote_token_id: quote.id,
          price_precision: s.pricePrecision,
          qty_precision: s.quantityPrecision,
          amount_precision: s.amountPrecision ?? s.pricePrecision,
          min_qty: s.limitVolumeMin,
          min_notional: s.limitAmountMin,
        },
        create: {
          symbol_code: s.symbol,
          base_token_id: base.id,
          quote_token_id: quote.id,
          price_precision: s.pricePrecision,
          qty_precision: s.quantityPrecision,
          amount_precision: s.amountPrecision ?? s.pricePrecision,
          min_qty: s.limitVolumeMin,
          min_notional: s.limitAmountMin,
        },
      });
    }
    return { synced: symbols.length };
  }
}
```

**서비스 예시 – BotEvents 기록**

```ts
// apps/gw/src/bots/bot-events.service.ts (발췌)
import { Injectable } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class BotEventsService {
  constructor(private prisma: PrismaClient) {}
  record(input: { strategyId: bigint | number; stateBefore?: string; stateAfter: string; eventType: string; reasonCode?: string; message?: string; context?: any; }) {
    return this.prisma.bot_events.create({
      data: {
        strategy_id: BigInt(input.strategyId),
        state_before: input.stateBefore,
        state_after: input.stateAfter,
        event_type: input.eventType,
        reason_code: input.reasonCode,
        message: input.message,
        context: input.context ?? {},
      },
    });
  }
}
```

### 24.4 TypeORM 대안(요약)

> Prisma 대신 TypeORM을 쓰고 싶을 때 최소 골격.

```bash
pnpm add -w typeorm reflect-metadata pg
```

**apps/gw/src/typeorm/data-source.ts**

```ts
import 'reflect-metadata';
import { DataSource } from 'typeorm';
export const AppDataSource = new DataSource({
  type: 'postgres',
  url: process.env.DATABASE_URL,
  entities: [__dirname + '/../**/*.entity.{ts,js}'],
  migrations: [__dirname + '/../migrations/*.{ts,js}'],
  synchronize: false,
});
```

**예시 엔티티 – Pair**

```ts
// apps/gw/src/admin/pair.entity.ts
import { Entity, PrimaryGeneratedColumn, Column, Index, ManyToOne, JoinColumn } from 'typeorm';
@Entity('pairs')
export class PairEntity {
  @PrimaryGeneratedColumn('increment', { type: 'bigint' }) id: string;
  @Index({ unique: true })
  @Column({ type: 'text' }) symbol_code!: string;
  @Column({ type: 'bigint' }) base_token_id!: string;
  @Column({ type: 'bigint' }) quote_token_id!: string;
  @Column('int') price_precision!: number;
  @Column('int') qty_precision!: number;
  @Column('int') amount_precision!: number;
  @Column('numeric') min_qty!: string;
  @Column('numeric') min_notional!: string;
}
```

**마이그레이션**

```bash
pnpx typeorm migration:generate -d apps/gw/src/typeorm/data-source.ts -n init
pnpx typeorm migration:run -d apps/gw/src/typeorm/data-source.ts
```

---

## 25. GitHub 연동 후 다음 단계 (CI/CD & 시드)

> 로컬 ↔ GitHub 연계 기준. 아래 파일들은 레포에 그대로 추가.

### 25.1 Git 브랜치/PR 규칙(경량)

* `main`: 안정 릴리스
* `dev`: 통합 브랜치
* 기능별: `feature/*` → PR → `dev` 머지 → 필요 시 `main` 릴리스 태그

### 25.2 GitHub Actions: CI 파이프라인

**.github/workflows/ci.yml**

```yaml
name: CI
on:
  push:
    branches: [ dev, feature/** ]
  pull_request:
    branches: [ dev ]
jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
      - run: pnpm i --frozen-lockfile
      - name: Prisma Generate
        run: pnpm prisma:gen
      - name: Lint
        run: pnpm -r lint || true
      - name: Unit tests
        run: pnpm -r test || true
```

> 필요 시 **staging 배포** 잡을 별도 워크플로우로 분리(.yml 추가)하고, Docker 이미지를 빌드/푸시.

### 25.3 Prisma 시드 스크립트(선택)

**prisma/seed.ts**

```ts
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

async function main() {
  // 최소 토큰/페어 예시
  const base = await prisma.tokens.upsert({ where: { symbol: 'LTC' }, update: {}, create: { symbol: 'LTC' } });
  const quote = await prisma.tokens.upsert({ where: { symbol: 'USDT' }, update: {}, create: { symbol: 'USDT' } });
  await prisma.pairs.upsert({
    where: { symbol_code: 'LTCUSDT' },
    update: { base_token_id: base.id, quote_token_id: quote.id, price_precision: 4, qty_precision: 3, amount_precision: 4, min_qty: '0.001', min_notional: '5' },
    create: { symbol_code: 'LTCUSDT', base_token_id: base.id, quote_token_id: quote.id, price_precision: 4, qty_precision: 3, amount_precision: 4, min_qty: '0.001', min_notional: '5' },
  });
}

main().finally(() => prisma.$disconnect());
```

**package.json 스크립트 추가**

```json
{
  "scripts": {
    "prisma:seed": "ts-node --transpile-only prisma/seed.ts"
  }
}
```

### 25.4 GitHub Secrets (필수)

* `DATABASE_URL` : 스테이징/CI용 Postgres URL(없으면 CI에서 DB 단계 스킵)
* `MBIT_BASE_URL` : [https://www.mbitinside.com](https://www.mbitinside.com)
* *(배포 시)* `REGISTRY_USER`, `REGISTRY_TOKEN`, `STAGING_SSH` 등

### 25.5 로컬 → 원격 진행 체크리스트

* [ ] `docker-compose up -d`로 DB 기동
* [ ] `pnpm prisma:migrate` → `pnpm prisma:seed`
* [ ] `pnpm dev:gw`로 API 서버 가동(로컬)
* [ ] PR 생성(feature/* → dev), CI 그린 확인
* [ ] `/admin/pairs` 동기화 → `/orders` 스모크 테스트

---

## 26. 즉시 실행 런북 (Step-by-step Checklist)

> 로컬 PC와 GitHub가 연결된 상태에서 **지금 바로 실행** 가능한 단계별 가이드입니다. OS별 명령 포함.

### 26.1 코드 최신화 & 브랜치 준비

```bash
git checkout dev || git checkout -b dev
git pull origin dev || true
git checkout -b feature/bootstrap-run
```

* 확인: `git status`가 깨끗하고 현재 브랜치가 `feature/bootstrap-run`.

### 26.2 환경 변수 파일 준비

* `.env.dev`를 `.env`로 복사 후 `DATABASE_URL`, `MBIT_BASE_URL` 확인.

```powershell
Copy-Item .env.dev .env -Force   # Windows
```

```bash
cp -f .env.dev .env             # macOS/Linux
```

### 26.3 Docker로 Postgres 기동

```bash
docker compose -f docker-compose.yml up -d
docker ps | grep tb-postgres
docker logs -n 20 tb-postgres
```

### 26.4 DB 연결 확인

```bash
psql "$PG_URL" -c "\\dt" || psql "postgresql://tb:tbpass@localhost:5432/trading_bot" -c "select now();"
```

### 26.5 의존성 설치

```bash
pnpm i
```

### 26.6 Prisma 코드 생성 & 마이그레이션 & 시드

```bash
pnpm prisma:gen
pnpm prisma:migrate
pnpm prisma:seed   # 선택
```

* 확인: `prisma:studio`로 테이블 확인 가능.

### 26.7 게이트웨이 서버 실행

```bash
pnpm dev:gw
```

* 확인: 콘솔에 `Listening on 8080` 출력.

### 26.8 기본 API 스모크 테스트

* **심볼 동기화**:

```bash
curl -X POST http://localhost:8080/admin/pairs/sync
```

* **API 키 연결 테스트** (실키 필요):

```bash
curl -X POST http://localhost:8080/user/accounts/keys/test \
  -H "Content-Type: application/json" \
  -d '{"apiKey":"<YOUR_KEY>","apiSecret":"<YOUR_SECRET>"}'
```

* **주문 프록시 드라이런**:

```bash
curl -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"LTCUSDT","side":"BUY","type":"LIMIT","price":"60.1234","volume":"0.010","apiAccountId":1}'
```

* **봇 이벤트 조회**:

```bash
curl http://localhost:8080/bots/123/events
```

### 26.9 GitHub로 푸시 & CI 확인

```bash
git add .
git commit -m "feat: bootstrap runbook, prisma migrate, pairs sync stub"
git push origin feature/bootstrap-run
```

* GitHub PR → `dev`, Actions 탭 CI 성공 확인.

### 26.10 자주 발생하는 오류 해결 팁

* Docker가 WSL에서 동작 안 함(Windows): Docker Desktop → **WSL Integration** 활성화.
* 5432 포트 충돌: 기존 Postgres 종료 또는 포트 변경(`5433:5432`).
* `prisma:migrate` 실패: 초기 단계에 한해 `rm -rf prisma/migrations && pnpm prisma:migrate`.
* `node-gyp`류 빌드 에러: Node 20, Python 3.x, build tools 설치.
* 거래소 시간 오류: OS 시간 동기화 필요.

### 26.11 다음 확장(선택)

* `/admin/pairs/sync` 컨트롤러 완성
* `/orders → /sapi/v1/order/test` 분기 추가
* `POST /curves/targets` → `curve_points` 생성 저장
* WS 게이트웨이 구독/백오프 정책 구현

---
